//! Live-bot signal pipeline, a bit-exact twin of the Python paper bot's veto path
//! (btclat/paper: feeds/parse, state, features, model/vector, arms/decide `vt_v1_m0.02_trigger`).
// Constants are written as in scipy's cephes / the Python sources (exact decimal literals), and
// NaN-aware comparisons are spelled `!(x >= y)` on purpose (NaN must fail the gate).
#![allow(clippy::excessive_precision, clippy::approx_constant, clippy::neg_cmp_op_on_partial_ord)]

pub mod engine;
pub mod features;
pub mod feed;
pub mod num;
pub mod state;

pub use engine::{Decision, Engine, MarketMeta, Signal, VetoParams};
