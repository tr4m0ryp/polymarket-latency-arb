//! The 60 s `stats` line: feed counts and receipt lags, engine counters, latency percentiles
//! (feature build, model, decision -> wire, receipt -> wire, sign), risk state, memory.
use serde_json::{json, Value};
use std::collections::HashMap;
use std::sync::{Arc, Mutex};

use btl_signal::engine::Engine;
use btl_signal::feed::Ev;
use btl_signal::Signal;

use super::exec::Exec;
use super::feeds::binance::FanIn;
use super::msg::Recv;
use crate::replay::pct;

pub struct Stats {
    every_ns: u64,
    next: u64,
    feeds: HashMap<&'static str, u64>,
    feat: Vec<u64>,
    model: Vec<u64>,
    /// receipt wall - exchange stamp (perp book / trades, CLOB), us (signed: host clock error shows)
    lag: HashMap<&'static str, Vec<i64>>,
    pub fans: Vec<(&'static str, Arc<Mutex<FanIn>>)>,
}

fn rss_mb() -> f64 {
    std::fs::read_to_string("/proc/self/status").ok().and_then(|s| s.lines().find(|l| l.starts_with("VmRSS:"))
        .and_then(|l| l.split_whitespace().nth(1)).and_then(|x| x.parse::<f64>().ok())).map(|k| k / 1024.0).unwrap_or(f64::NAN)
}

impl Stats {
    pub fn new(every_s: u64, fans: Vec<(&'static str, Arc<Mutex<FanIn>>)>) -> Stats {
        Stats { every_ns: every_s * 1_000_000_000, next: btl_venue::mono_ns() + every_s * 1_000_000_000,
            feeds: HashMap::new(), feat: vec![], model: vec![], lag: HashMap::new(), fans }
    }

    pub fn feed(&mut self, ev: &Ev, r: Recv) {
        let k = ev.kind().as_str();
        *self.feeds.entry(k).or_default() += 1;
        let vt = ev.venue_t();
        if vt.is_finite() {
            let l = (r.wall as f64 / 1e3 - vt * 1e6) as i64;
            self.lag.entry(k).or_default().push(l);
        }
    }

    pub fn signal(&mut self, s: &Signal) {
        self.feat.push(s.feat_ns);
        self.model.push(s.model_ns);
    }

    pub fn due(&self, now: u64) -> bool {
        now >= self.next
    }

    pub fn line(&mut self, eng: &Engine, ex: &mut Exec, queue: usize) -> Value {
        self.next = btl_venue::mono_ns() + self.every_ns;
        let fans: Value = self.fans.iter().map(|(n, f)| {
            let f = f.lock().unwrap();
            (n.to_string(), json!({"wins": f.wins, "dups": f.dups}))
        }).collect::<serde_json::Map<_, _>>().into();
        let lag: Value = self.lag.iter_mut().map(|(k, v)| (k.to_string(), pct_i(v))).collect::<serde_json::Map<_, _>>().into();
        let now = btl_venue::wall_ns() as f64 / 1e9;
        let out = json!({"feeds": self.feeds, "fanin": fans, "recv_lag_us": lag, "engine": eng.stats,
            "markets": eng.world.mkts.len(), "queue": queue, "feat_us": pct(&mut self.feat), "model_us": pct(&mut self.model),
            "dec_to_send_us": pct(&mut ex.lat_dec_send), "recv_to_send_us": pct(&mut ex.lat_recv_send),
            "sign_us": pct(&mut ex.lat_sign), "exec": ex.n, "pnl": ex.risk.pnl(), "exposure": ex.risk.exposure(),
            "orders_last_hour": ex.risk.orders_last_hour(now), "balance": ex.risk.balance(), "rss_mb": rss_mb(),
            "log_dropped": ex.log.dropped(),
            "keepwarm_ms": ex.venue.as_ref().map(|v| v.clob.ping_ns().iter().map(|x| *x as f64 / 1e6).collect::<Vec<_>>())});
        self.feeds.clear();
        self.lag.clear();
        self.feat.clear();
        self.model.clear();
        ex.lat_dec_send.clear();
        ex.lat_recv_send.clear();
        ex.lat_sign.clear();
        out
    }
}

fn pct_i(v: &mut [i64]) -> Value {
    if v.is_empty() {
        return Value::Null;
    }
    v.sort_unstable();
    let at = |p: f64| v[((v.len() - 1) as f64 * p).round() as usize];
    json!({"n": v.len(), "p10": at(0.1), "p50": at(0.5), "p90": at(0.9), "p99": at(0.99)})
}
