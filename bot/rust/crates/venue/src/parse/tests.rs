use serde_json::{json, Value};

use super::*;
use crate::http::Resp;

fn resp(code: u16, body: Value) -> Resp {
    let mut r = Resp::transport_error("POST", "/order", 0, (1, 1), 0, "x".into());
    (r.code, r.body, r.err) = (code, body, None);
    r
}

#[test]
fn order_fill_and_rejections() {
    let r = order(&resp(200, json!({"success": true, "status": "matched", "orderID": "0xab",
        "makingAmount": "2.85", "takingAmount": "5", "tradeIDs": ["t1"]})));
    assert!(r.ok);
    assert_eq!((r.status.as_deref(), r.order_id.as_deref(), r.fill_sh, r.fill_cost), (Some("matched"), Some("0xab"), 5.0, 2.85));
    assert!((r.px.unwrap() - 0.57).abs() < 1e-12);
    assert_eq!(r.trade_ids, ["t1"]);
    let r = order(&resp(400, json!({"errorMsg": "order couldn't be fully filled. FOK orders are fully filled or killed."})));
    assert_eq!((r.ok, r.err_kind.as_deref(), r.status.as_deref()), (false, Some("fok_killed"), Some("rejected")));
    let r = order(&resp(200, json!({"success": false, "errorMsg": "no orders found to match with FAK order"})));
    assert_eq!(r.err_kind.as_deref(), Some("fak_no_match"));
    let r = order(&resp(200, json!({"success": false, "errorMsg": ""})));
    assert_eq!((r.ok, r.err_kind.as_deref()), (false, None));
    let mut t = resp(0, Value::Null);
    t.err = Some("timeout".into());
    let r = order(&t);
    assert_eq!((r.err.as_deref(), r.err_kind.as_deref()), (Some("timeout"), Some("transport")));
    assert_eq!(classify(429, &json!("Too Many Requests")).as_deref(), Some("rate_limited"));
    assert_eq!(classify(503, &json!({})).as_deref(), Some("http_503"));
    assert_eq!(classify(200, &json!({"error": "weird"})).as_deref(), Some("error"));
    assert_eq!(classify(400, &json!({"error": "Trading restricted in your region"})).as_deref(), Some("geoblock"));
    assert_eq!(classify(200, &json!({"success": true})), None);
}

#[test]
fn lookup_cancel_gone() {
    let l = lookup(&resp(200, json!({"id": "0x1", "status": "LIVE", "size_matched": "2", "price": "0.4"})));
    assert_eq!((l.found, l.fill_sh, l.px), (true, 2.0, Some(0.4)));
    assert!((l.fill_cost - 0.8).abs() < 1e-12);
    let l = lookup(&resp(200, Value::Null));
    assert_eq!((l.found, l.fill_sh, l.px), (false, 0.0, None));
    let c = resp(200, json!({"canceled": ["a"], "not_canceled": {"b": "order can't be found - already canceled or matched", "c": "other"}}));
    assert!(cancelled(&c, "a") && !cancelled(&c, "b"));
    assert!(gone(&c, "b").unwrap().contains("can't be found"));
    assert_eq!((gone(&c, "c"), gone(&c, "a")), (None, None));
}

#[test]
fn book_and_balance() {
    let b = resp(200, json!({"bids": [{"price": "0.40", "size": "10"}, {"price": "0.45", "size": "0"}, {"price": "0.42", "size": "3"}],
                             "asks": [{"price": "0.60", "size": "1"}, {"price": "0.55", "size": "2"}]}));
    assert_eq!(best(&b), (0.42, 0.55));
    let (bb, ba) = best(&resp(200, json!({"bids": [], "asks": []})));
    assert!(bb.is_nan() && ba.is_nan());
    let x = balance(&resp(200, json!({"balance": "12500000", "allowances": {"0xE1": "0", "0xE2": "100"}})));
    assert_eq!((x.balance, x.allowance_ok, x.code), (12.5, true, 200));
    let x = balance(&resp(200, json!({"balance": 1000000, "allowance": "0"})));
    assert_eq!((x.balance, x.allowance_ok), (1.0, false));
}
