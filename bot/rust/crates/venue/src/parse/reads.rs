//! Book and balance reads.

use serde_json::Value;

use super::{f, obj};
use crate::http::Resp;

/// (best bid, best ask) of a GET /book answer; NaN for an empty side.
pub fn best(r: &Resp) -> (f64, f64) {
    let b = obj(&r.body);
    let side = |k: &str| -> Vec<f64> {
        match b.get(k) {
            Some(Value::Array(a)) => {
                a.iter().filter(|x| f(x.get("size")) > 0.0).map(|x| f(x.get("price"))).collect()
            }
            _ => Vec::new(),
        }
    };
    let bid = side("bids").into_iter().fold(f64::NAN, f64::max);
    let ask = side("asks").into_iter().fold(f64::NAN, f64::min);
    (bid, ask)
}

#[derive(Clone, Debug, PartialEq)]
pub struct Balance {
    /// pUSD, dollars
    pub balance: f64,
    /// any exchange allowance set
    pub allowance_ok: bool,
    pub code: u16,
}

/// GET /balance-allowance: 6-decimal base units to dollars.
pub fn balance(r: &Resp) -> Balance {
    let b = obj(&r.body);
    let allowance_ok = match b.get("allowances") {
        Some(Value::Object(m)) if !m.is_empty() => m.values().any(|v| f(Some(v)) > 0.0),
        _ => b.get("allowance").is_some_and(|v| f(Some(v)) > 0.0),
    };
    Balance { balance: f(b.get("balance")) / 1e6, allowance_ok, code: r.code }
}
