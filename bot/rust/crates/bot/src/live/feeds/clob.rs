//! One CLOB market-channel connection per 5m market (btclat/live/feeds.py `clob`), from
//! discovery until end + 30 s; only the market's Up-token book is kept.
use std::collections::HashMap;

use btl_signal::feed::clob;
use btl_signal::MarketMeta;
use crossbeam_channel::Sender;

use super::ws::{self, Pump};
use crate::live::msg::{Msg, Recv};

pub const URL: &str = "wss://ws-subscriptions-clob.polymarket.com/ws/market";

pub fn spawn(m: &MarketMeta, tx: Sender<Msg>) {
    let hello = serde_json::json!({"assets_ids": [m.up, m.down], "type": "market", "custom_feature_enabled": true});
    let ups: HashMap<String, i64> = [(m.up.clone(), m.start)].into();
    let p = Pump { url: URL.into(), name: format!("clob:{}", m.slug), conn: 0, hello: Some(hello.to_string()),
        ping_s: Some(10), until: Some(m.end as f64 + 30.0) };
    let tx2 = tx.clone();
    tokio::spawn(ws::run(p, tx, move |raw, mono, wall| {
        for ev in clob::parse(wall as f64 / 1e9, raw, &ups) {
            let _ = tx2.send(Msg::Ev(ev, Recv { conn: 0, mono, wall }));
        }
    }));
}
