//! The pre-send gate: first cap an order would break.
use super::{Intent, RiskBook};
use crate::limits::{VENUE_MIN_NOTIONAL, VENUE_MIN_SHARES};

const EPS: f64 = 1e-9;

impl RiskBook {
    /// First cap this order breaks, or `None` if it may be sent. Order (book.py order, with
    /// the two Rust-taker pacing gates right after the day lock, because they are cheap,
    /// transient and the common reason in a hot loop; a malformed order that also hits
    /// them reports the pacing reason):
    ///
    /// `stopped`, `day_locked`, `floor_halt`, `max_inflight`, `refractory`, `max_shares`, `max_notional`,
    /// `below_venue_min_shares`, `below_venue_min_notional`, `max_exposure`,
    /// `loss_headroom`, `max_orders_hour`, `balance`.
    pub fn check(&self, it: &Intent, now: f64) -> Option<&'static str> {
        let l = &self.limits;
        if self.stop_reason.is_some() {
            return Some("stopped");
        }
        if self.locked() {
            return Some("day_locked");
        }
        if self.halted() {
            return Some("floor_halt");
        }
        if self.inflight.len() >= l.max_inflight as usize {
            return Some("max_inflight");
        }
        if let Some(&last) = self.last_send.get(&it.slug) {
            if now - last < l.min_refractory_s {
                return Some("refractory");
            }
        }
        if it.size > l.max_shares + EPS {
            return Some("max_shares");
        }
        if it.notional() > l.max_notional + EPS {
            return Some("max_notional");
        }
        if it.size < VENUE_MIN_SHARES - EPS {
            return Some("below_venue_min_shares");
        }
        if it.notional() < VENUE_MIN_NOTIONAL - EPS {
            return Some("below_venue_min_notional");
        }
        let worst = it.worst();
        if self.exposure() + worst > l.max_exposure + EPS {
            return Some("max_exposure");
        }
        if self.pnl() - worst <= -l.loss_cap {
            return Some("loss_headroom");
        }
        if self.orders_last_hour(now) >= l.max_orders_hour as usize {
            return Some("max_orders_hour");
        }
        if let Some(cash) = self.spendable() {
            if cash < worst {
                return Some("balance"); // balance - reserve - in flight (bankroll.reserve)
            }
        }
        None
    }
}
