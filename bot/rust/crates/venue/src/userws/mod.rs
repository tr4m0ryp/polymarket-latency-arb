//! The CLOB user channel: our own trades and order updates, pushed within ms of the match.
//! Port of btclat/trade/maker/fills/userws.py: hello with the L2 creds, text PING every 10 s,
//! reconnect with backoff (1 s doubling to 30 s), every event and every connect/close/error on
//! one mpsc channel with receipt timestamps. It is the fast path; the GET /data/trades poll is
//! the backstop, so a dropped socket costs seconds of fill latency, never a missed fill.

mod frames;

pub use frames::{events, hello};

use std::time::Duration;

use anyhow::{bail, Result};
use futures_util::{SinkExt, StreamExt};
use serde_json::Value;
use tokio::sync::mpsc;
use tokio::time::{interval_at, sleep, Instant};
use tokio_tungstenite::tungstenite::protocol::WebSocketConfig;
use tokio_tungstenite::tungstenite::Message;

use crate::clock::{mono_ns, wall_ns};
use crate::creds::ApiCreds;

pub const USER: &str = "wss://ws-subscriptions-clob.polymarket.com/ws/user";
pub const PING_S: u64 = 10;
/// No frame (not even a PONG) for this long: the socket is dead, reconnect.
pub const SILENT_S: u64 = 35;

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum WsState {
    Connected,
    Closed,
    Error,
}

#[derive(Clone, Debug)]
pub enum UserMsg {
    Event { ev: Value, t_mono_ns: u64, t_wall_ns: u64 },
    State { state: WsState, err: Option<String>, t_mono_ns: u64, t_wall_ns: u64 },
}

fn state(state: WsState, err: Option<String>) -> UserMsg {
    UserMsg::State { state, err, t_mono_ns: mono_ns(), t_wall_ns: wall_ns() }
}

/// Forever, until the receiver is dropped: subscribe, forward events, reconnect on error.
pub async fn run(api: ApiCreds, markets: Vec<String>, tx: mpsc::Sender<UserMsg>) {
    run_url(USER, api, markets, tx).await
}

/// `run` against any ws:// or wss:// URL (tests use a local server).
pub async fn run_url(url: &str, api: ApiCreds, markets: Vec<String>, tx: mpsc::Sender<UserMsg>) {
    let mut backoff = 1.0f64;
    while !tx.is_closed() {
        let msg = match session(url, &api, &markets, &tx, &mut backoff).await {
            Ok(()) => state(WsState::Closed, None),
            Err(e) => {
                let mut s = format!("{e:#}");
                s.truncate(200);
                state(WsState::Error, Some(s))
            }
        };
        if tx.send(msg).await.is_err() {
            return;
        }
        sleep(Duration::from_secs_f64(backoff)).await;
        backoff = (backoff * 2.0).min(30.0);
    }
}

/// One connection's life. Ok on a clean close or when the receiver is gone.
async fn session(url: &str, api: &ApiCreds, markets: &[String], tx: &mpsc::Sender<UserMsg>, backoff: &mut f64)
    -> Result<()> {
    let cfg = WebSocketConfig { max_message_size: Some(1 << 22), ..Default::default() };
    let (ws, _) = tokio_tungstenite::connect_async_with_config(url, Some(cfg), true).await?;
    let (mut sink, mut stream) = ws.split();
    sink.send(Message::Text(hello(api, markets))).await?;
    if tx.send(state(WsState::Connected, None)).await.is_err() {
        return Ok(());
    }
    *backoff = 1.0;
    let mut ping = interval_at(Instant::now() + Duration::from_secs(PING_S), Duration::from_secs(PING_S));
    let mut last_rx = Instant::now();
    loop {
        tokio::select! {
            _ = ping.tick() => {
                if last_rx.elapsed() > Duration::from_secs(SILENT_S) {
                    bail!("no frame for {SILENT_S} s");
                }
                sink.send(Message::Text("PING".into())).await?;
            }
            m = stream.next() => {
                let (t_mono_ns, t_wall_ns) = (mono_ns(), wall_ns());
                last_rx = Instant::now();
                let text = match m {
                    None | Some(Ok(Message::Close(_))) => return Ok(()),
                    Some(Err(e)) => return Err(e.into()),
                    Some(Ok(Message::Text(t))) => t,
                    Some(Ok(Message::Binary(b))) => String::from_utf8_lossy(&b).into_owned(),
                    Some(Ok(_)) => continue,
                };
                for ev in events(&text) {
                    if tx.send(UserMsg::Event { ev, t_mono_ns, t_wall_ns }).await.is_err() {
                        return Ok(());
                    }
                }
            }
        }
    }
}

#[cfg(test)]
mod tests;
