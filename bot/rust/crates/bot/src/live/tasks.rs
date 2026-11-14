//! Background tasks on the tokio runtime: market discovery (+ CLOB feeds), settlement
//! outcomes, balance reads, the trade poll, the user websocket, SIGTERM / SIGINT.
use std::collections::HashSet;
use std::sync::atomic::{AtomicU64, Ordering};
use std::sync::{Arc, Mutex};
use std::time::Duration;

use crossbeam_channel::Sender;

use super::exec::Venue;
use super::feeds::{clob, gamma};
use super::msg::Msg;
use btl_venue::{wall_ns, ApiCreds, Clob};

fn now_s() -> f64 {
    wall_ns() as f64 / 1e9
}

pub fn http() -> reqwest::Client {
    reqwest::Client::builder().user_agent("btclat-bot/0.1").timeout(Duration::from_secs(15)).build().expect("http client")
}

pub type Ends = Arc<Mutex<Vec<(String, i64)>>>;

pub async fn discovery(tx: Sender<Msg>, ends: Ends) {
    let http = http();
    let mut started: HashSet<i64> = HashSet::new();
    loop {
        for start in gamma::wanted(now_s(), 90.0) {
            if started.contains(&start) {
                continue;
            }
            match gamma::fetch(&http, start).await {
                Ok(Some(m)) => {
                    started.insert(start);
                    ends.lock().unwrap().push((m.slug.clone(), m.end));
                    clob::spawn(&m, tx.clone());
                    let _ = tx.send(Msg::Market(Box::new(m)));
                }
                Ok(None) => {}
                Err(e) => {
                    let _ = tx.send(Msg::Conn { feed: "gamma".into(), conn: 0, state: "error", err: Some(format!("{e:#}")) });
                }
            }
        }
        tokio::time::sleep(Duration::from_secs(5)).await;
    }
}

pub async fn settle(tx: Sender<Msg>, ends: Ends) {
    let http = http();
    let mut done: HashSet<String> = HashSet::new();
    loop {
        tokio::time::sleep(Duration::from_secs(30)).await;
        let due: Vec<(String, i64)> = ends.lock().unwrap().iter()
            .filter(|(s, e)| !done.contains(s) && now_s() >= *e as f64 + 60.0).cloned().collect();
        for (slug, end) in due {
            match gamma::outcome(&http, &slug).await {
                Ok(Some(o)) => {
                    done.insert(slug.clone());
                    let _ = tx.send(Msg::Settle { slug, outcome: o });
                }
                Ok(None) if now_s() > end as f64 + 7200.0 => {
                    done.insert(slug);
                }
                Ok(None) => {}
                Err(e) => {
                    let _ = tx.send(Msg::Conn { feed: "gamma_settle".into(), conn: 0, state: "error", err: Some(format!("{e:#}")) });
                }
            }
        }
    }
}

pub async fn balance(tx: Sender<Msg>, clob: Clob, api: ApiCreds, addr: String, sig_type: u8) {
    loop {
        tokio::time::sleep(Duration::from_secs(60)).await;
        let r = clob.balance(&api, &addr, sig_type).await;
        let _ = tx.send(Msg::Balance(Box::new(r)));
    }
}

/// GET /data/trades every 3 s while an order went out in the last 120 s (last_send = wall s).
pub async fn trade_poll(tx: Sender<Msg>, v: (Clob, ApiCreds, String), last_send: Arc<AtomicU64>) {
    let (clob, api, addr) = v;
    loop {
        tokio::time::sleep(Duration::from_secs(3)).await;
        let last = last_send.load(Ordering::Relaxed) as f64;
        if now_s() - last > 120.0 {
            continue;
        }
        let r = clob.trades(&api, &addr, (now_s() - 900.0) as u64, 3).await.map_err(|e| format!("{e:#}"));
        let _ = tx.send(Msg::Trades(r));
    }
}

pub fn spawn_live(tx: &Sender<Msg>, v: &Venue, last_send: Arc<AtomicU64>) {
    tokio::spawn(balance(tx.clone(), v.clob.clone(), v.api.clone(), v.addr.clone(), v.sig_type));
    tokio::spawn(trade_poll(tx.clone(), (v.clob.clone(), v.api.clone(), v.addr.clone()), last_send));
    let (utx, mut urx) = tokio::sync::mpsc::channel(1024);
    tokio::spawn(btl_venue::userws::run(v.api.clone(), vec![], utx));
    let tx = tx.clone();
    tokio::spawn(async move {
        while let Some(m) = urx.recv().await {
            let _ = tx.send(Msg::User(m));
        }
    });
}

pub fn spawn_signals(tx: Sender<Msg>) {
    use tokio::signal::unix::{signal, SignalKind};
    tokio::spawn(async move {
        let mut term = signal(SignalKind::terminate()).expect("SIGTERM handler");
        let mut int = signal(SignalKind::interrupt()).expect("SIGINT handler");
        let why = tokio::select! { _ = term.recv() => "SIGTERM", _ = int.recv() => "SIGINT" };
        let _ = tx.send(Msg::Stop(why.into()));
    });
}
