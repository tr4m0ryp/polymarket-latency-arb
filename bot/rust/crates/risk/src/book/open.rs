//! Opening a book: validate limits, replay today's ledger (or carry from the last earlier one).
use std::collections::{HashMap, VecDeque};
use std::fs;
use std::path::{Path, PathBuf};

use thiserror::Error;

use super::ledger::{Leg, Row};
use super::{day, utc_day, RiskBook};
use crate::limits::{LimitError, Limits};

#[derive(Debug, Error)]
pub enum RiskError {
    #[error(transparent)]
    Limit(#[from] LimitError),
    #[error("{path}: {source}")]
    Io {
        path: PathBuf,
        source: std::io::Error,
    },
    #[error("{path} line {line}: {msg}")]
    Ledger {
        path: PathBuf,
        line: usize,
        msg: String,
    },
}

impl RiskBook {
    /// Build the book for the UTC day of `now`. `limits` are re-validated against the hard
    /// constants. Corrupt ledger lines are an error (fail closed), not skipped.
    pub fn open(limits: Limits, state: impl AsRef<Path>, now: f64) -> Result<RiskBook, RiskError> {
        let limits = limits.checked()?;
        let state = state.as_ref().to_path_buf();
        fs::create_dir_all(&state).map_err(|source| RiskError::Io {
            path: state.clone(),
            source,
        })?;
        let mut b = RiskBook::empty(limits, state, utc_day(now));
        let path = b.ledger_path();
        if path.exists() {
            b.replay(&path)?;
        } else if let Some(prev) = previous_ledger(&b.state, &b.day) {
            b.carry_from(&prev, now)?;
        }
        Ok(b)
    }

    fn empty(limits: Limits, state: PathBuf, day: String) -> RiskBook {
        RiskBook {
            limits,
            state,
            day,
            pos: HashMap::new(),
            inflight: HashMap::new(),
            sends: VecDeque::new(),
            last_send: HashMap::new(),
            realised: 0.0,
            balance: None,
            marks: HashMap::new(),
            stop_reason: None,
            ledger: None,
            bank: crate::bankroll::Bankroll::uncapped(crate::limits::VENUE_MIN_SHARES),
            inflight_meta: HashMap::new(),
            fills: HashMap::new(),
            first_side: HashMap::new(),
            claim: 0.0,
            day_peak: 0.0,
            peak: 0.0,
        }
    }

    fn replay(&mut self, path: &Path) -> Result<(), RiskError> {
        let text = fs::read_to_string(path).map_err(|source| RiskError::Io {
            path: path.to_path_buf(),
            source,
        })?;
        for (i, line) in text.lines().enumerate() {
            if line.trim().is_empty() {
                continue;
            }
            let row: Row = serde_json::from_str(line).map_err(|e| RiskError::Ledger {
                path: path.to_path_buf(),
                line: i + 1,
                msg: e.to_string(),
            })?;
            match row {
                Row::Send { t, .. } => self.sends.push_back(t),
                Row::Fill(l) => {
                    *self.fills.entry((l.slug.clone(), l.up)).or_default() += 1;
                    self.first_side.entry(l.slug.clone()).or_insert(l.up);
                    self.add(&l)
                }
                Row::Carry(l) => self.add(&l),
                Row::Resolve { slug, outcome } => {
                    self.resolve_in_memory(&slug, outcome);
                }
            }
        }
        Ok(())
    }

    /// First open of a day with no ledger yet (restart after midnight): the unresolved
    /// positions of the latest earlier ledger still count, so they are carried into today's
    /// ledger. Realised PnL does not carry; sends of the last hour do (in memory).
    fn carry_from(&mut self, prev: &Path, now: f64) -> Result<(), RiskError> {
        let mut old = RiskBook::empty(self.limits, self.state.clone(), String::new());
        old.replay(prev)?;
        self.sends = old
            .sends
            .into_iter()
            .filter(|&t| t > now - 3600.0)
            .collect();
        let mut legs: Vec<Leg> = old
            .pos
            .iter()
            .map(|((_, t), p)| super::leg_of(t, p))
            .collect();
        legs.sort_by(|a, b| (&a.slug, &a.token).cmp(&(&b.slug, &b.token)));
        for l in legs {
            self.add(&l);
            self.log(Row::Carry(l));
        }
        Ok(())
    }
}

/// Latest `ledger-<day>.jsonl` strictly before `today` (dates sort lexicographically).
fn previous_ledger(state: &Path, today: &str) -> Option<PathBuf> {
    let mut best: Option<String> = None;
    for e in fs::read_dir(state).ok()?.flatten() {
        let name = e.file_name().to_string_lossy().into_owned();
        let Some(d) = name
            .strip_prefix("ledger-")
            .and_then(|s| s.strip_suffix(".jsonl"))
        else {
            continue;
        };
        if d < today && best.as_deref().is_none_or(|b| d > b) {
            best = Some(d.to_string());
        }
    }
    best.map(|d| day::ledger_path(state, &d))
}
