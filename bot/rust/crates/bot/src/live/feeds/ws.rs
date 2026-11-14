//! A websocket pump: connect, optional hello, read forever (or until `until`, wall s),
//! reconnect with backoff, ping text "PING" every `ping_s`. Each frame goes to `on_msg` with
//! its receipt times (monotonic, wall ns) taken right after the read.
use futures_util::{SinkExt, StreamExt};
use std::time::Duration;
use tokio_tungstenite::tungstenite::Message;

use crate::live::msg::Msg;
use btl_venue::{mono_ns, wall_ns};

pub struct Pump {
    pub url: String,
    pub name: String,
    pub conn: usize,
    pub hello: Option<String>,
    pub ping_s: Option<u64>,
    pub until: Option<f64>,
}

fn now_s() -> f64 {
    wall_ns() as f64 / 1e9
}

pub async fn run(p: Pump, tx: crossbeam_channel::Sender<Msg>, mut on_msg: impl FnMut(&str, u64, u64)) {
    let mut backoff = 1.0f64;
    let note = |state: &'static str, err: Option<String>| {
        let _ = tx.send(Msg::Conn { feed: p.name.clone(), conn: p.conn, state, err });
    };
    while p.until.is_none_or(|u| now_s() < u) {
        let r = tokio_tungstenite::connect_async(p.url.as_str()).await;
        let (mut ws, _) = match r {
            Ok(x) => x,
            Err(e) => {
                note("error", Some(format!("{e}").chars().take(300).collect()));
                tokio::time::sleep(Duration::from_secs_f64(backoff)).await;
                backoff = (backoff * 2.0).min(30.0);
                continue;
            }
        };
        note("connect", None);
        backoff = 1.0;
        if let Some(h) = &p.hello {
            let _ = ws.send(Message::Text(h.clone())).await;
        }
        let mut ping = tokio::time::interval(Duration::from_secs(p.ping_s.unwrap_or(3600)));
        ping.tick().await;
        let err = loop {
            let left = p.until.map(|u| (u - now_s()).max(0.1)).unwrap_or(3600.0);
            tokio::select! {
                m = tokio::time::timeout(Duration::from_secs_f64(left.min(60.0)), ws.next()) => match m {
                    Err(_) => {
                        if p.until.is_some_and(|u| now_s() >= u) { break None; }
                    }
                    Ok(None) => break Some("closed".to_string()),
                    Ok(Some(Err(e))) => break Some(format!("{e}")),
                    Ok(Some(Ok(Message::Text(s)))) => {
                        let (mono, wall) = (mono_ns(), wall_ns());
                        if s != "PONG" && !s.is_empty() { on_msg(&s, mono, wall); }
                    }
                    Ok(Some(Ok(Message::Binary(b)))) => {
                        let (mono, wall) = (mono_ns(), wall_ns());
                        if let Ok(s) = std::str::from_utf8(&b) { on_msg(s, mono, wall); }
                    }
                    Ok(Some(Ok(_))) => {}
                },
                _ = ping.tick(), if p.ping_s.is_some() => {
                    if let Err(e) = ws.send(Message::Text("PING".into())).await { break Some(format!("{e}")); }
                }
            }
        };
        let _ = ws.close(None).await;
        match err {
            None => break,
            Some(e) => {
                note("error", Some(e.chars().take(300).collect()));
                tokio::time::sleep(Duration::from_secs_f64(backoff)).await;
                backoff = (backoff * 2.0).min(30.0);
            }
        }
    }
    note("close", None);
}
