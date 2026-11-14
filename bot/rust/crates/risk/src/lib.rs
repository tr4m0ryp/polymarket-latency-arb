//! btl_risk: hard risk limits of the live taker, ported from `btclat/trade/risk` and the
//! offline half of `btclat/trade/gate/preflight.py`.
//!
//! - [`limits`]: the HARD constants and [`Limits`] (can only be lowered, re-validated by `checked`).
//! - [`book`]: [`RiskBook`], positions / in-flight / sends / PnL with a JSONL ledger that is
//!   byte-compatible with the Python book (`<state>/ledger-<day>.jsonl`, `<state>/lock-<day>`).
//! - [`bankroll`]: balance-fraction sizing and fractional per-market / open caps, side policy,
//!   fills per market, day drawdown pause.
//! - [`gate`]: kill file, day lock and approval checks (no network).

pub mod bankroll;
pub mod book;
pub mod gate;
pub mod limits;

pub use bankroll::{Bankroll, SidePolicy, Sizing};
pub use book::{lock_path, utc_day, Intent, Pos, RiskBook, RiskError};
pub use gate::{config_dir, killed, offline_checks, Refused};
pub use limits::{fee, LimitError, LimitOverrides, Limits};
