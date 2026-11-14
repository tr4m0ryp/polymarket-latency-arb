//! Error kind of a CLOB answer.

use serde_json::Value;

use super::{s, truthy};

const ERRORS: &[(&str, &str)] = &[
    ("fak_no_match", "no orders found to match"), ("fok_killed", "fok orders are"),
    ("min_size", "lower than the minimum"), ("min_notional", "marketable buy"),
    ("min_notional", "invalid amount"), ("balance", "not enough balance"),
    ("closed_only", "closed only"), ("banned", "banned"), ("post_only_crosses", "invalid post-only"),
    ("crosses_book", "crosses the book"), ("tick", "tick size"), ("duplicate", "duplicated"),
    ("not_ready", "not yet ready"), ("paused", "trading is currently disabled"),
    ("cancel_only", "cancel-only"), ("post_only_mode", "post-only mode"), ("timeout", "timed out"),
    ("geoblock", "restricted"), ("geoblock", "region"), ("geoblock", "geoblock"),
    ("payload", "invalid order payload"), ("auth", "unauthorized"), ("auth", "invalid api key"),
];

fn by_code(code: u16) -> Option<&'static str> {
    Some(match code {
        0 => "transport",
        401 => "auth",
        403 => "forbidden",
        425 => "engine_restart",
        429 => "rate_limited",
        _ => return None,
    })
}

/// The error message of a body: errorMsg, error or message of an object (first truthy), the
/// text of anything else.
pub fn msg(body: &Value) -> String {
    match body {
        Value::Object(m) => ["errorMsg", "error", "message"]
            .iter()
            .filter_map(|k| m.get(*k))
            .find(|v| truthy(v))
            .map(s)
            .unwrap_or_default(),
        Value::Null => String::new(),
        v => s(v),
    }
}

/// None for a clean 200; else the kind from the message, then the status code.
pub fn classify(code: u16, body: &Value) -> Option<String> {
    let m = msg(body).to_lowercase();
    if code == 200 && m.is_empty() {
        return None;
    }
    if let Some((kind, _)) = ERRORS.iter().find(|(_, needle)| m.contains(needle)) {
        return Some(kind.to_string());
    }
    Some(match by_code(code) {
        Some(k) => k.to_string(),
        None if code != 200 => format!("http_{code}"),
        None => "error".to_string(),
    })
}
