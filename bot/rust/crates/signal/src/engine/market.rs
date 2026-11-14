//! Shared Binance state (`Ctx`) and one `MarketCtx` per subscribed 5m market (raw.py).
use serde::{Deserialize, Serialize};

use crate::features::fair::Pzm;
use crate::state::{BookState, LockedTwap, PmBook, PmHist, Settle, TradeFlow};

/// A market as discovered on Gamma (btclat/live/markets.py `fetch`) or read from `markets-*`.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MarketMeta {
    pub fam: String,
    pub slug: String,
    pub start: i64,
    pub end: i64,
    #[serde(default)]
    pub condition_id: String,
    pub up: String,
    pub down: String,
    #[serde(default = "tick")]
    pub tick: f64,
}

fn tick() -> f64 {
    0.01
}

pub struct Ctx {
    pub perp: BookState,
    pub spot: BookState,
    pub flow: TradeFlow,
    pub settle: Settle,
    pub fair: Pzm,
}

impl Ctx {
    pub fn new(fair: Pzm) -> Ctx {
        Ctx { perp: BookState::new(0.1), spot: BookState::new(0.01), flow: TradeFlow::default(),
            settle: Settle::default(), fair }
    }
}

pub struct MarketCtx {
    pub meta: MarketMeta,
    pub start: f64,
    pub end: f64,
    pub book: PmBook,
    /// grid books, touch times and feed lag for the gate's extras (state/hist.rs)
    pub hist: PmHist,
    pub k: f64,
    pub lock: LockedTwap,
    /// tradable verdict, decided once after start + 1 (Engine.tradable)
    pub ok: Option<bool>,
}

impl MarketCtx {
    pub fn new(meta: MarketMeta) -> MarketCtx {
        let (start, end) = (meta.start as f64, meta.end as f64);
        MarketCtx { meta, start, end, book: PmBook::default(), hist: PmHist::new(start, end), k: f64::NAN,
            lock: LockedTwap::new(end), ok: None }
    }

    /// K = 60 s TWAP before the start (trade clock); fixed once computed.
    pub fn strike(&mut self, st: &Settle) -> f64 {
        if self.k.is_nan() {
            self.k = st.twap(self.start - 60.0, self.start);
        }
        self.k
    }
}
