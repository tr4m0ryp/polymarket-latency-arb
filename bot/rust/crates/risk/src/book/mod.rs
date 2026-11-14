//! Risk state of one UTC day: positions, orders in flight, sends per hour, realised and
//! marked PnL, the day lock. Every change is appended to `<state>/ledger-<day>.jsonl` and
//! replayed on open, so a restart the same day sees the same exposure, PnL and order count.
mod bank;
mod check;
mod day;
mod intent;
mod ledger;
mod mutate;
mod open;
mod read;

use std::collections::{HashMap, VecDeque};
use std::fs::{File, OpenOptions};
use std::io::Write;
use std::path::{Path, PathBuf};

pub use day::{lock_path, utc_day};
pub use intent::{Intent, Pos};
pub use open::RiskError;

use crate::bankroll::Bankroll;
use crate::limits::Limits;
use ledger::{Leg, Row};

pub struct RiskBook {
    limits: Limits,
    state: PathBuf,
    day: String,
    pos: HashMap<(String, String), Pos>,
    inflight: HashMap<String, f64>,
    sends: VecDeque<f64>,
    last_send: HashMap<String, f64>,
    realised: f64,
    balance: Option<f64>,
    marks: HashMap<String, f64>,
    stop_reason: Option<String>,
    ledger: Option<File>,
    // bankroll caps (bank.rs) ------------------------------------------------------------
    bank: Bankroll,
    /// cid -> (slug, up, shares) of orders in flight
    inflight_meta: HashMap<String, (String, bool, f64)>,
    /// (slug, up) -> fills of this process (a restart forgets them: open positions stay)
    fills: HashMap<(String, bool), u32>,
    /// slug -> side of the first fill
    first_side: HashMap<String, bool>,
    /// resolved winnings not yet seen in a balance read (redeem pending)
    claim: f64,
    day_peak: f64,
    /// all-time peak equity (persisted in `<state>/peak`)
    peak: f64,
}

impl RiskBook {
    // persistence -----------------------------------------------------------------------
    pub fn ledger_path(&self) -> PathBuf {
        day::ledger_path(&self.state, &self.day)
    }

    /// Append one row. A write failure cannot be undone, so it stops the book (fail closed).
    fn log(&mut self, row: Row) {
        let mut line = match serde_json::to_string(&row) {
            Ok(s) => s,
            Err(e) => return self.stop(format!("ledger_io: {e}")),
        };
        line.push('\n');
        if self.ledger.is_none() {
            match OpenOptions::new()
                .create(true)
                .append(true)
                .open(self.ledger_path())
            {
                Ok(f) => self.ledger = Some(f),
                Err(e) => return self.stop(format!("ledger_io: {e}")),
            }
        }
        if let Some(Err(e)) = self.ledger.as_mut().map(|f| f.write_all(line.as_bytes())) {
            self.stop(format!("ledger_io: {e}"));
        }
    }

    /// New UTC day: fresh ledger, open positions carried, realised PnL reset. Sends keep
    /// counting (rolling hour). Returns true if the day changed.
    pub fn roll(&mut self, now: f64) -> bool {
        let day = utc_day(now);
        if day == self.day {
            return false;
        }
        self.day = day;
        self.realised = 0.0;
        self.day_peak = self.equity().unwrap_or(0.0);
        self.ledger = None;
        let mut legs: Vec<Leg> = self
            .pos
            .iter()
            .map(|((_, token), p)| leg_of(token, p))
            .collect();
        legs.sort_by(|a, b| (&a.slug, &a.token).cmp(&(&b.slug, &b.token)));
        for l in legs {
            self.log(Row::Carry(l));
        }
        true
    }

    // accessors -------------------------------------------------------------------------
    pub fn limits(&self) -> &Limits {
        &self.limits
    }
    pub fn day(&self) -> &str {
        &self.day
    }
    pub fn state_dir(&self) -> &Path {
        &self.state
    }
    pub fn positions(&self) -> impl Iterator<Item = (&(String, String), &Pos)> {
        self.pos.iter()
    }
    pub fn balance(&self) -> Option<f64> {
        self.balance
    }
    /// Venue balance read (None until the first read: the balance cap is then skipped).
    /// A rise over our fill-adjusted balance is taken as redeemed winnings (claim drops).
    pub fn set_balance(&mut self, b: Option<f64>) {
        if let (Some(old), Some(new)) = (self.balance, b) {
            if new > old {
                self.claim = (self.claim - (new - old)).max(0.0);
            }
        }
        self.balance = b;
    }
    pub fn stop_reason(&self) -> Option<&str> {
        self.stop_reason.as_deref()
    }
    /// Stop the book: every later `check` returns "stopped". The first reason is kept.
    pub fn stop(&mut self, reason: String) {
        self.stop_reason.get_or_insert(reason);
    }
}

fn leg_of(token: &str, p: &Pos) -> Leg {
    Leg {
        slug: p.slug.clone(),
        token: token.to_string(),
        up: p.up,
        end: p.end,
        sh: p.sh,
        cost: p.cost,
        fee: p.fee,
    }
}
