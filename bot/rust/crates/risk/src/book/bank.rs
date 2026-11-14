//! Bankroll caps on the book: equity, the order size for a signal, the day drawdown pause.
use std::fs::OpenOptions;
use std::io::Write;

use super::{day, lock_path, Intent, RiskBook};
use crate::bankroll::{Bankroll, SidePolicy};
use crate::limits::{fee, VENUE_MIN_NOTIONAL, VENUE_MIN_SHARES};

const EPS: f64 = 1e-9;

impl RiskBook {
    pub fn set_bankroll(&mut self, b: Bankroll) {
        self.bank = b;
        self.day_peak = self.day_peak.max(self.equity().unwrap_or(0.0));
        self.peak = std::fs::read_to_string(self.peak_path()).ok()
            .and_then(|s| s.trim().parse::<f64>().ok()).unwrap_or(0.0);
    }

    pub fn peak_path(&self) -> std::path::PathBuf {
        self.state.join("peak")
    }

    /// Floor halt marker: while it exists the book refuses every order (a human removes it).
    pub fn halt_path(&self) -> std::path::PathBuf {
        self.state.join("halt")
    }

    pub fn halted(&self) -> bool {
        self.halt_path().exists()
    }

    pub fn peak(&self) -> f64 {
        self.peak
    }

    /// New all-time peak (persisted when it rises by >= 1%), or the floor halt.
    fn track_peak(&mut self, e: f64) -> Result<(), &'static str> {
        if e >= self.peak * 1.01 || self.peak <= 0.0 {
            self.peak = e;
            if let Err(err) = std::fs::write(self.peak_path(), format!("{e}")) {
                self.stop(format!("peak_io: {err}"));
            }
        }
        if self.bank.floor.is_some_and(|f| e < f * self.peak) {
            let body = format!("{{\"reason\": \"floor\", \"equity\": {e:?}, \"peak\": {:?}, \"t\": {:?}}}",
                               self.peak, day::unix_now());
            if let Err(err) = std::fs::write(self.halt_path(), body) {
                self.stop(format!("halt_io: {err}"));
            }
            return Err("floor_halt");
        }
        Ok(())
    }

    pub fn bankroll(&self) -> &Bankroll {
        &self.bank
    }

    /// Working bankroll: balance (fill-adjusted) - reserve + open positions at cost + resolved
    /// winnings not yet redeemed. None until the first balance read.
    pub fn equity(&self) -> Option<f64> {
        let open: f64 = self.pos.values().map(|p| p.cost + p.fee).sum();
        self.balance.map(|b| b - self.bank.reserve + open + self.claim)
    }

    /// Cash the bot may still commit: balance - reserve - orders in flight (None: no read yet).
    pub fn spendable(&self) -> Option<f64> {
        self.balance.map(|b| b - self.bank.reserve - self.inflight_total())
    }

    pub fn claim(&self) -> f64 {
        self.claim
    }

    pub fn day_peak(&self) -> f64 {
        self.day_peak
    }

    /// (shares held, shares in flight) on one side of a market.
    fn side_shares(&self, slug: &str, up: bool) -> f64 {
        let held: f64 = self.pos.values().filter(|p| p.slug == slug && p.up == up).map(|p| p.sh).sum();
        let fly: f64 = self.inflight_meta.values().filter(|m| m.0 == slug && m.1 == up).map(|m| m.2).sum();
        held + fly
    }

    /// Cost + fee committed in one market: positions plus the worst case of orders in flight.
    pub fn market_committed(&self, slug: &str) -> f64 {
        let held: f64 = self.pos.values().filter(|p| p.slug == slug).map(|p| p.cost + p.fee).sum();
        let fly: f64 = self.inflight_meta.iter().filter(|(_, m)| m.0 == slug)
            .map(|(c, _)| self.inflight.get(c).copied().unwrap_or(0.0)).sum();
        held + fly
    }

    /// Shares for an order at `it.price` on `it.slug` / `it.up` (it.size is ignored), or the
    /// skip reason: `reserve` (balance - reserve <= 0), `floor_halt` (writes `<state>/halt`),
    /// `dd_stop` (also locks the day),
    /// `max_fills`, `one_side`, `hedge_only`,
    /// `no_balance`, `market_cap`, `open_cap`, `balance`. Sized from equity, then shrunk to
    /// the room the caps and the cash leave; below 5 sh or $1 it is skipped.
    pub fn size_for(&mut self, it: &Intent, edge: f64) -> Result<f64, &'static str> {
        let b = self.bank;
        let fixed = matches!(b.sizing, crate::bankroll::Sizing::Fixed(_));
        if self.balance.is_some_and(|bal| bal - b.reserve <= 0.0) {
            return Err("reserve");
        }
        let eq = self.equity();
        if let Some(e) = eq {
            self.track_peak(e)?;
            self.day_peak = self.day_peak.max(e);
            if b.dd_stop.is_some_and(|y| e < (1.0 - y) * self.day_peak) {
                self.pause_day(e);
                return Err("dd_stop");
            }
        }
        let own = self.fills.get(&(it.slug.clone(), it.up)).copied().unwrap_or(0);
        let other = self.fills.get(&(it.slug.clone(), !it.up)).copied().unwrap_or(0);
        let n = if b.side == SidePolicy::PerSide { own } else { own + other };
        if n >= b.max_fills {
            return Err("max_fills");
        }
        let first = self.first_side.get(&it.slug).copied();
        if b.side == SidePolicy::OneDirection && first.is_some_and(|s| s != it.up) {
            return Err("one_side");
        }
        let e = match (eq, fixed) {
            (Some(e), _) => e,
            (None, true) => f64::INFINITY,
            (None, false) => return Err("no_balance"),
        };
        let p = it.price;
        let mut q = b.shares(e, p, edge);
        if b.side == SidePolicy::HedgeOnly {
            let (mine, theirs) = (self.side_shares(&it.slug, it.up), self.side_shares(&it.slug, !it.up));
            if mine >= theirs && first.is_some_and(|s| s != it.up) {
                return Err("hedge_only");
            }
            if mine < theirs {
                q = q.min((theirs - mine).floor());
            }
        }
        let w = p + fee(p, 1.0);
        let mut rooms: Vec<(f64, &'static str)> = vec![];
        if let Some(cash) = self.spendable() {
            rooms.push((cash, "balance"));
        }
        if let (Some(f), true) = (b.market_frac, e.is_finite()) {
            rooms.push((f * e - self.market_committed(&it.slug), "market_cap"));
        }
        if let (Some(f), true) = (b.open_frac, e.is_finite()) {
            rooms.push((f * e - self.exposure(), "open_cap"));
        }
        let mut why = "";
        for (room, r) in rooms {
            if q * w > room + EPS {
                q = (room.max(0.0) / w + EPS).floor();
                why = r;
            }
        }
        if q < VENUE_MIN_SHARES - EPS || q * p < VENUE_MIN_NOTIONAL - EPS {
            return Err(if why.is_empty() { "hedge_only" } else { why });
        }
        Ok(q)
    }

    /// Drawdown stop: lock the UTC day (the book refuses orders until the next day).
    fn pause_day(&mut self, e: f64) {
        let lp = lock_path(&self.state, &self.day);
        let body = format!("{{\"reason\": \"dd_stop\", \"equity\": {e:?}, \"day_peak\": {:?}, \"t\": {:?}}}",
                           self.day_peak, day::unix_now());
        match OpenOptions::new().write(true).create_new(true).open(&lp) {
            Ok(mut f) => {
                if let Err(err) = f.write_all(body.as_bytes()) {
                    self.stop(format!("lock_io: {err}"));
                }
            }
            Err(err) if err.kind() == std::io::ErrorKind::AlreadyExists => {}
            Err(err) => self.stop(format!("lock_io: {err}")),
        }
    }
}
