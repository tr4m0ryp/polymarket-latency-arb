//! POST /order, GET /data/order/<id> and DELETE /order answers.

use serde_json::Value;

use super::{classify, f, msg, obj, s, truthy};
use crate::http::Resp;

/// Status, order id and immediate fill of a POST /order answer. A BUY's `makingAmount` is pUSD
/// paid and `takingAmount` shares received.
#[derive(Clone, Debug, PartialEq)]
pub struct OrderResult {
    pub ok: bool,
    pub status: Option<String>,
    pub order_id: Option<String>,
    pub fill_sh: f64,
    pub fill_cost: f64,
    pub px: Option<f64>,
    pub trade_ids: Vec<String>,
    pub err: Option<String>,
    pub err_kind: Option<String>,
}

pub fn order(r: &Resp) -> OrderResult {
    let b = obj(&r.body);
    let kind = classify(r.code, &r.body);
    let success = b.get("success").or_else(|| b.get("ok")).map(truthy).unwrap_or(true);
    let ok = r.code == 200 && success && kind.is_none();
    let (sh, cost) = (f(b.get("takingAmount")), f(b.get("makingAmount")));
    let err = if ok {
        None
    } else {
        let m: String = msg(&r.body).chars().take(300).collect();
        if m.is_empty() { r.err.clone() } else { Some(m) }
    };
    OrderResult {
        ok,
        status: if ok { b.get("status").filter(|v| !v.is_null()).map(s) } else { Some("rejected".into()) },
        order_id: b.get("orderID").filter(|v| truthy(v)).map(s),
        fill_sh: if ok { sh } else { 0.0 },
        fill_cost: if ok { cost } else { 0.0 },
        px: (ok && sh > 0.0).then(|| cost / sh),
        trade_ids: match b.get("tradeIDs") {
            Some(Value::Array(a)) => a.iter().map(s).collect(),
            _ => Vec::new(),
        },
        err,
        err_kind: if ok { None } else { kind },
    }
}

/// GET /data/order/<id>: matched size at the order price. `found` false means the venue
/// answered without the order; its read side lags the engine, so never read that as 0 matched.
#[derive(Clone, Debug, PartialEq)]
pub struct Lookup {
    pub status: Option<String>,
    pub fill_sh: f64,
    pub fill_cost: f64,
    pub px: Option<f64>,
    pub found: bool,
}

pub fn lookup(r: &Resp) -> Lookup {
    let b = obj(&r.body);
    let (sh, px) = (f(b.get("size_matched")), f(b.get("price")));
    let t = |k: &str| b.get(k).is_some_and(truthy);
    Lookup {
        status: b.get("status").filter(|v| !v.is_null()).map(s),
        fill_sh: sh,
        fill_cost: sh * px,
        px: (sh > 0.0).then_some(px),
        found: t("status") || t("id"),
    }
}

/// The cancel answer lists `oid` under `canceled`.
pub fn cancelled(r: &Resp, oid: &str) -> bool {
    r.code == 200
        && matches!(obj(&r.body).get("canceled"), Some(Value::Array(a)) if a.iter().any(|x| x.as_str() == Some(oid)))
}

const GONE: &[&str] = &["can't be found", "cannot be found", "not found", "already canceled", "matched"];

/// The venue's reason when a cancel finds the order no longer on its book (maybe filled).
pub fn gone(r: &Resp, oid: &str) -> Option<String> {
    if r.code != 200 {
        return None;
    }
    let why = obj(&r.body).get("not_canceled")?.get(oid).filter(|v| truthy(v)).map(s)?;
    let low = why.to_lowercase();
    GONE.iter().any(|g| low.contains(g)).then_some(why)
}
