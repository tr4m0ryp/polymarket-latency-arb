//! `Clob`: k order connections (k <= 3, as fanout.py) plus one data connection for public
//! reads, and the server clock offset (auth timestamps use server time, as client.py does).

use std::sync::atomic::{AtomicI64, AtomicU64, Ordering};
use std::sync::Arc;

use anyhow::{bail, Result};
use futures_util::future::join_all;
use serde_json::Value;

use super::conn::{Conn, Req};
use super::resp::Resp;
use crate::clock::wall_ns;

pub const HOST: &str = "https://clob.polymarket.com";
pub const GEOBLOCK: &str = "https://polymarket.com/api/geoblock";
/// Hard cap on identical copies of one order (btclat/trade/venue/fanout.py MAX_CONNS).
pub const MAX_CONNS: usize = 3;

pub(crate) struct Inner {
    pub conns: Vec<Conn>,
    pub data: Conn,
    /// server clock - local wall clock, ns (from GET /time)
    pub offset_ns: AtomicI64,
    /// last keep-warm round trip per order connection, ns (0: none yet)
    pub ping_ns: Vec<AtomicU64>,
}

/// Cheap to clone (one Arc); share it across tasks.
#[derive(Clone)]
pub struct Clob {
    pub(crate) inner: Arc<Inner>,
}

impl Clob {
    /// `k` order connections (1..=3) to `host`, plus a data connection. Nothing is dialled
    /// until `connect()` / `warm()`.
    pub fn new(host: &str, k: usize) -> Result<Clob> {
        if !(1..=MAX_CONNS).contains(&k) {
            bail!("k={k} outside 1..{MAX_CONNS}");
        }
        let conns = (0..k).map(|i| Conn::new(i, host)).collect::<Result<Vec<_>>>()?;
        let inner = Inner {
            data: Conn::new(k, host)?,
            conns,
            offset_ns: AtomicI64::new(0),
            ping_ns: (0..k).map(|_| AtomicU64::new(0)).collect(),
        };
        Ok(Clob { inner: Arc::new(inner) })
    }

    pub fn k(&self) -> usize {
        self.inner.conns.len()
    }

    /// Idle time (ns) of each order connection.
    pub fn idle_ns(&self) -> Vec<u64> {
        self.inner.conns.iter().map(|c| c.idle_ns()).collect()
    }

    /// Last keep-warm round trip (ns) of each order connection, 0 if none yet.
    pub fn ping_ns(&self) -> Vec<u64> {
        self.inner.ping_ns.iter().map(|p| p.load(Ordering::Relaxed)).collect()
    }

    pub(crate) async fn on(&self, i: usize, r: Req<'_>) -> Resp {
        self.inner.conns[i.min(self.k() - 1)].req(r).await
    }

    pub(crate) async fn on_data(&self, r: Req<'_>) -> Resp {
        self.inner.data.req(r).await
    }

    /// GET /time on order connection 0.
    pub async fn time(&self) -> Resp {
        self.on(0, Req::get("/time")).await
    }

    /// GET /time on every order connection at once (TCP + TLS + HTTP/2 set up, warm).
    pub async fn warm(&self) -> Vec<Resp> {
        join_all(self.inner.conns.iter().map(|c| c.req(Req::get("/time")))).await
    }

    /// Warm every connection (data too) and set the server clock offset from the first good
    /// GET /time: offset = server - midpoint(send, ack). Returns the order-connection pings.
    pub async fn connect(&self) -> Vec<Resp> {
        let (rs, _) = tokio::join!(self.warm(), self.on_data(Req::get("/time")));
        if let Some(r) = rs.iter().find(|r| r.ok()) {
            self.set_offset(r);
        }
        rs
    }

    fn set_offset(&self, r: &Resp) {
        let server_s = match &r.body {
            Value::Object(m) => m.get("time").and_then(as_f64),
            v => as_f64(v),
        };
        if let Some(s) = server_s {
            let mid = (r.t_send_wall_ns / 2 + r.t_ack_wall_ns / 2) as i128;
            let off = (s * 1e9) as i128 - mid;
            self.inner.offset_ns.store(off as i64, Ordering::Relaxed);
        }
    }

    /// Server clock minus local clock, seconds.
    pub fn offset_s(&self) -> f64 {
        self.inner.offset_ns.load(Ordering::Relaxed) as f64 / 1e9
    }

    /// Now on the server clock, unix seconds.
    pub fn server_now_s(&self) -> f64 {
        (wall_ns() as i128 + self.inner.offset_ns.load(Ordering::Relaxed) as i128) as f64 / 1e9
    }

    /// Auth header timestamp: whole server seconds (Python `int(time.time() + offset)`).
    pub fn auth_ts(&self) -> u64 {
        self.server_now_s().max(0.0) as u64
    }
}

fn as_f64(v: &Value) -> Option<f64> {
    match v {
        Value::Number(n) => n.as_f64(),
        Value::String(s) => s.trim().parse().ok(),
        _ => None,
    }
}
