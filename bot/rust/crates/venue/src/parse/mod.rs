//! CLOB responses -> flat records; a port of btclat/trade/venue/parse.py. Error kinds follow
//! docs.polymarket.com/resources/error-codes (messages matched case-insensitively).

mod classify;
mod order;
mod reads;

pub use classify::{classify, msg};
pub use order::{cancelled, gone, lookup, order, Lookup, OrderResult};
pub use reads::{balance, best, Balance};

use serde_json::{Map, Value};

static EMPTY: std::sync::OnceLock<Map<String, Value>> = std::sync::OnceLock::new();

/// The body as an object, or an empty one (Python `b = resp.body if isinstance(dict) else {}`).
pub(crate) fn obj(v: &Value) -> &Map<String, Value> {
    v.as_object().unwrap_or_else(|| EMPTY.get_or_init(Map::new))
}

/// Python `float(x)` falling back to 0.0 on TypeError/ValueError.
pub(crate) fn f(x: Option<&Value>) -> f64 {
    match x {
        Some(Value::Number(n)) => n.as_f64().unwrap_or(0.0),
        Some(Value::String(s)) => s.trim().parse().unwrap_or(0.0),
        Some(Value::Bool(b)) => *b as u8 as f64,
        _ => 0.0,
    }
}

/// Python truthiness of a JSON value.
pub(crate) fn truthy(v: &Value) -> bool {
    match v {
        Value::Null => false,
        Value::Bool(b) => *b,
        Value::Number(n) => n.as_f64().is_some_and(|x| x != 0.0),
        Value::String(s) => !s.is_empty(),
        Value::Array(a) => !a.is_empty(),
        Value::Object(o) => !o.is_empty(),
    }
}

/// `str(x)` of a JSON value: strings bare, anything else as JSON.
pub(crate) fn s(v: &Value) -> String {
    match v {
        Value::String(s) => s.clone(),
        v => v.to_string(),
    }
}

#[cfg(test)]
mod tests;
