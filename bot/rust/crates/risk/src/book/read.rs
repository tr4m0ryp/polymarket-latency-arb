//! Readings (exposure, PnL, send counts) and the loss-cap breach.
use std::fs::OpenOptions;
use std::io::Write;

use super::{day, lock_path, RiskBook};

impl RiskBook {
    // readings --------------------------------------------------------------------------
    /// Open cost + fee of unresolved positions plus the worst case of orders in flight.
    pub fn exposure(&self) -> f64 {
        self.pos.values().map(|p| p.cost + p.fee).sum::<f64>() + self.inflight_total()
    }

    pub fn inflight_total(&self) -> f64 {
        self.inflight.values().sum()
    }

    pub fn inflight_count(&self) -> usize {
        self.inflight.len()
    }

    /// Open positions at our book's mid (at cost while no mid is known).
    pub fn marked(&self) -> f64 {
        self.pos
            .iter()
            .map(|((_, token), p)| {
                let v = match self.marks.get(token) {
                    Some(m) if !m.is_nan() => p.sh * m,
                    _ => p.cost,
                };
                v - p.cost - p.fee
            })
            .sum()
    }

    pub fn realised(&self) -> f64 {
        self.realised
    }

    pub fn pnl(&self) -> f64 {
        self.realised + self.marked()
    }

    pub fn orders_last_hour(&self, now: f64) -> usize {
        self.sends.iter().filter(|&&s| s > now - 3600.0).count()
    }

    pub fn locked(&self) -> bool {
        lock_path(&self.state, &self.day).exists()
    }

    /// Loss cap reached: lock the day (once) and report true.
    pub fn breach(&mut self) -> bool {
        let pnl = self.pnl();
        if pnl > -self.limits.loss_cap {
            return false;
        }
        let lp = lock_path(&self.state, &self.day);
        let body = format!(
            "{{\"pnl\": {:?}, \"realised\": {:?}, \"t\": {:?}}}",
            pnl,
            self.realised,
            day::unix_now()
        );
        // create_new: the first breach writes the lock, later ones leave it untouched.
        match OpenOptions::new().write(true).create_new(true).open(&lp) {
            Ok(mut f) => {
                if let Err(e) = f.write_all(body.as_bytes()) {
                    self.stop(format!("lock_io: {e}"));
                }
            }
            Err(e) if e.kind() == std::io::ErrorKind::AlreadyExists => {}
            Err(e) => self.stop(format!("lock_io: {e}")),
        }
        self.stop_reason = Some(format!(
            "loss cap: pnl {pnl:.2} <= -{:?}",
            self.limits.loss_cap
        ));
        true
    }
}
