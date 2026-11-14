//! Balance-scaled sizing and fractional caps (reports/bankroll-caps.md).
//!
//! Every order is sized from the live equity E = venue balance - reserve (adjusted by our fills
//! until the next read) + cost of open positions + resolved winnings not yet seen in the
//! balance. The reserve is untouchable: no cap, size or affordability check may use it, and
//! with balance - reserve <= 0 nothing is sent. Profits compound into E.
//! Per-market and total-open caps are fractions of E, so one 5-minute market can never take
//! more than `market_frac` of the wallet; an order is shrunk to the room left, skipped below
//! the venue's 5-share / $1 minimum. A drawdown of `dd_stop` from the UTC day's peak equity
//! pauses the rest of the day (day lock file, lifted by the next UTC day). Below `floor` x the
//! all-time peak equity (kept in `<state>/peak`) the bot halts for good (`<state>/halt`).
mod defaults;

pub use defaults::*;

use crate::limits::{LimitError, VENUE_MIN_NOTIONAL, VENUE_MIN_SHARES};

#[derive(Debug, Clone, Copy, PartialEq)]
pub enum Sizing {
    /// shares per order
    Fixed(f64),
    /// stake = f x E per order
    Frac(f64),
    /// stake = c x edge / (1 - p) x E (fractional Kelly on the model's predicted value)
    Kelly(f64),
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum SidePolicy {
    /// no side rule
    Any,
    /// no order on the side opposite a known fill in that market
    OneDirection,
    /// `max_fills` counts per side; the opposite side is free
    PerSide,
    /// an order opposite the market's net position is capped at the net share imbalance
    /// (it can only lower the market's worst-case loss)
    HedgeOnly,
}

#[derive(Debug, Clone, Copy, PartialEq)]
pub struct Bankroll {
    pub sizing: Sizing,
    pub max_sh: f64,
    /// committed cost + fee in one market (fills + orders in flight) <= x E; None = off
    pub market_frac: Option<f64>,
    /// all open positions + orders in flight <= x E; None = off
    pub open_frac: Option<f64>,
    pub side: SidePolicy,
    /// known fills per market (per side under PerSide)
    pub max_fills: u32,
    /// pause the UTC day below (1 - y) x the day's peak equity; None = off
    pub dd_stop: Option<f64>,
    /// $ of the venue balance the bot never uses (user rule 2026-10-14: $43.04)
    pub reserve: f64,
    /// halt for good below x the all-time peak equity (`<state>/halt`, a human removes it)
    pub floor: Option<f64>,
}

impl Bankroll {
    /// The pre-2026-10-15 behaviour: fixed shares, no fractional caps, no side rule.
    pub fn uncapped(shares: f64) -> Bankroll {
        Bankroll { sizing: Sizing::Fixed(shares), max_sh: 1e9, market_frac: None, open_frac: None,
            side: SidePolicy::Any, max_fills: u32::MAX, dd_stop: None, reserve: 0.0, floor: None }
    }

    pub fn checked(self) -> Result<Bankroll, LimitError> {
        let frac = |n: &str, v: Option<f64>| match v {
            Some(x) if !(x > 0.0 && x <= 1.0) => Err(LimitError(format!("{n}={x} outside (0, 1]"))),
            _ => Ok(()),
        };
        frac("market_frac", self.market_frac)?;
        frac("open_frac", self.open_frac)?;
        frac("dd_stop", self.dd_stop)?;
        frac("floor", self.floor)?;
        let s = match self.sizing {
            Sizing::Fixed(q) => q >= VENUE_MIN_SHARES,
            Sizing::Frac(f) => f > 0.0 && f <= 1.0,
            Sizing::Kelly(c) => c > 0.0 && c <= 2.0,
        };
        if !s || !(self.max_sh >= VENUE_MIN_SHARES) || self.max_fills == 0
            || !(self.reserve >= 0.0 && self.reserve.is_finite()) {
            return Err(LimitError(format!("bankroll caps invalid: {self:?}")));
        }
        Ok(self)
    }

    /// Shares before the room fit: sized from E, floored at the venue's 5 shares, capped at
    /// max_sh, raised to the venue's $1 minimum on cheap asks.
    pub fn shares(&self, equity: f64, price: f64, edge: f64) -> f64 {
        let q = match self.sizing {
            Sizing::Fixed(q) => q,
            Sizing::Frac(f) => (f * equity / price).floor(),
            Sizing::Kelly(c) => (c * edge.max(0.0) / (1.0 - price) * equity / price).floor(),
        };
        min_notional_size(q.max(VENUE_MIN_SHARES).min(self.max_sh), price)
    }
}

/// Shares for one order: `base`, raised just enough that price x shares reaches the venue's
/// $1 marketable minimum (+5% headroom) on cheap asks.
pub fn min_notional_size(base: f64, limit: f64) -> f64 {
    if limit <= 0.0 || base * limit >= VENUE_MIN_NOTIONAL {
        return base;
    }
    base.max((1.05 / limit - 1e-9).ceil()) // 1e-9: 1.05 / 0.15 is 7.0000000001 in f64
}
