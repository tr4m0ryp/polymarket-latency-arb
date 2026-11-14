//! Binance spot and USD-M perp (raw @trade + @bookTicker) on N connections per stream; the
//! first arrival per bookTicker update id (monotonic) or trade id wins (FanIn in live.py).
//! Wins per connection and duplicates are counted for the stats line.
use std::collections::{HashSet, VecDeque};
use std::sync::{Arc, Mutex};

use btl_signal::feed::binance::{self, Key};
use crossbeam_channel::Sender;

use super::ws::{self, Pump};
use crate::live::msg::{Msg, Recv};

pub const SPOT: &str = "wss://stream.binance.com:9443/stream?streams=btcusdt@trade/btcusdt@bookTicker";
pub const PERP: &str = "wss://fstream.binance.com/public/stream?streams=btcusdt@trade/btcusdt@bookTicker";

#[derive(Default)]
pub struct FanIn {
    last_u: u64,
    seen: HashSet<u64>,
    order: VecDeque<u64>,
    pub wins: Vec<u64>,
    pub dups: u64,
}

impl FanIn {
    /// True if this message is the first arrival.
    pub fn take(&mut self, conn: usize, key: Key) -> bool {
        match key {
            Key::U(u) => {
                if u <= self.last_u {
                    self.dups += 1;
                    return false;
                }
                self.last_u = u;
            }
            Key::T(id) => {
                if !self.seen.insert(id) {
                    self.dups += 1;
                    return false;
                }
                self.order.push_back(id);
                if self.order.len() > 50_000 {
                    if let Some(old) = self.order.pop_front() {
                        self.seen.remove(&old);
                    }
                }
            }
        }
        if self.wins.len() <= conn {
            self.wins.resize(conn + 1, 0);
        }
        self.wins[conn] += 1;
        true
    }
}

pub fn spawn(perp: bool, n: usize, tx: Sender<Msg>, fan: Arc<Mutex<FanIn>>) {
    let name = if perp { "binance_fut" } else { "binance" };
    for i in 0..n {
        let (tx, fan) = (tx.clone(), fan.clone());
        let p = Pump { url: (if perp { PERP } else { SPOT }).into(), name: format!("{name}#{i}"), conn: i,
            hello: None, ping_s: None, until: None };
        let tx2 = tx.clone();
        tokio::spawn(ws::run(p, tx, move |raw, mono, wall| {
            let Some((ev, key)) = binance::parse(wall as f64 / 1e9, raw, perp) else { return };
            let first = fan.lock().map(|mut f| f.take(i, key)).unwrap_or(false);
            if first {
                let _ = tx2.send(Msg::Ev(ev, Recv { conn: i as u8, mono, wall }));
            }
        }));
    }
}
