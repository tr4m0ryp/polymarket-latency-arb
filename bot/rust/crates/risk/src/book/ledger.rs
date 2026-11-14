//! Ledger rows. Same JSONL format as `btclat/trade/risk/book.py`: one object per line, tag `k`.
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Leg {
    pub slug: String,
    pub token: String,
    pub up: bool,
    pub end: f64,
    pub sh: f64,
    pub cost: f64,
    pub fee: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(tag = "k", rename_all = "lowercase")]
pub enum Row {
    Send { t: f64, oid: String },
    Fill(Leg),
    Carry(Leg),
    Resolve { slug: String, outcome: f64 },
}
