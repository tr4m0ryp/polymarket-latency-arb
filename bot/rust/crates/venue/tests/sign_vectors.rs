//! Signing parity with py_clob_client_v2: fixtures from tests/gen_vectors.py.

use btl_venue::auth::l2::l2_headers;
use btl_venue::{ApiCreds, Creds, OrderSpec, OrderType, Side, Signer};
use serde_json::Value;

fn vectors() -> Value {
    serde_json::from_str(include_str!("fixtures/sign_vectors.json")).unwrap()
}

fn api(v: &Value) -> ApiCreds {
    let a = &v["api"];
    ApiCreds {
        key: a["key"].as_str().unwrap().into(),
        secret: a["secret"].as_str().unwrap().into(),
        passphrase: a["passphrase"].as_str().unwrap().into(),
    }
}

fn spec(o: &Value) -> OrderSpec {
    OrderSpec {
        token_id: o["token_id"].as_str().unwrap().into(),
        price: o["price"].as_f64().unwrap(),
        size: o["size"].as_f64().unwrap(),
        side: if o["side"] == "BUY" { Side::Buy } else { Side::Sell },
        order_type: match o["order_type"].as_str().unwrap() {
            "FAK" => OrderType::Fak,
            "FOK" => OrderType::Fok,
            "GTC" => OrderType::Gtc,
            _ => OrderType::Gtd,
        },
        post_only: o["post_only"].as_bool().unwrap(),
        expiration: o["expiration"].as_u64().unwrap(),
    }
}

#[test]
fn order_bodies_match_python() {
    let v = vectors();
    let key = v["key"].as_str().unwrap();
    let orders = v["orders"].as_array().unwrap();
    let mut seen = std::collections::HashSet::new();
    for o in orders {
        let st = o["sig_type"].as_u64().unwrap() as u8;
        let creds = Creds::new(key, o["funder"].as_str().unwrap(), st, None).unwrap();
        let signer = Signer::new(&creds).unwrap();
        assert_eq!(signer.address(), v["address"].as_str().unwrap());
        let s = signer
            .sign(&spec(o), o["owner"].as_str().unwrap(), o["salt"].as_u64().unwrap(), o["timestamp_ms"].as_u64().unwrap())
            .unwrap();
        assert_eq!(s.maker_amount, o["maker_amount"].as_u64().unwrap());
        assert_eq!(s.taker_amount, o["taker_amount"].as_u64().unwrap());
        assert_eq!(s.body, o["body"].as_str().unwrap(), "sig_type {st} {}", o["side"]);
        assert!(s.sign_ns > 0 && s.build_ns >= s.sign_ns);
        seen.insert((st, o["side"].as_str().unwrap().to_string(), o["order_type"].as_str().unwrap().to_string()));
    }
    assert_eq!(orders.len(), 35);
    for st in 0..4u8 {
        for side in ["BUY", "SELL"] {
            assert!(seen.iter().any(|(a, b, _)| *a == st && b == side), "missing {st} {side}");
        }
    }
}

#[test]
fn l1_headers_match_python() {
    let v = vectors();
    let creds = Creds::new(v["key"].as_str().unwrap(), v["funder"].as_str().unwrap(), 0, None).unwrap();
    let signer = Signer::new(&creds).unwrap();
    for c in v["l1"].as_array().unwrap() {
        let h = signer.l1_headers(c["ts"].as_u64().unwrap(), c["nonce"].as_u64().unwrap()).unwrap();
        assert_eq!(h.len(), 4);
        for (name, val) in h {
            assert_eq!(val, c["headers"][name].as_str().unwrap(), "{name}");
        }
    }
}

#[test]
fn l2_headers_match_python() {
    let v = vectors();
    let api = api(&v);
    for c in v["l2"].as_array().unwrap() {
        let h = l2_headers(&api, v["address"].as_str().unwrap(), c["method"].as_str().unwrap(),
                           c["path"].as_str().unwrap(), c["body"].as_str(), c["ts"].as_u64().unwrap());
        let names: Vec<_> = h.iter().map(|(n, _)| *n).collect();
        assert_eq!(names, ["POLY_ADDRESS", "POLY_SIGNATURE", "POLY_TIMESTAMP", "POLY_API_KEY", "POLY_PASSPHRASE"]);
        for (name, val) in h {
            assert_eq!(val, c["headers"][name].as_str().unwrap(), "{} {}", c["method"], name);
        }
    }
}

#[test]
fn bad_specs_are_refused() {
    let v = vectors();
    let creds = Creds::new(v["key"].as_str().unwrap(), v["funder"].as_str().unwrap(), 0, None).unwrap();
    let signer = Signer::new(&creds).unwrap();
    let mut s = spec(&v["orders"][0]);
    for (price, size, ot, exp) in [(0.0, 5.0, OrderType::Fak, 0), (1.0, 5.0, OrderType::Fak, 0),
                                   (0.5, 0.001, OrderType::Fak, 0), (0.5, 5.0, OrderType::Gtd, 0),
                                   (0.5, 5.0, OrderType::Fak, 1_760_000_000), (f64::NAN, 5.0, OrderType::Fak, 0)] {
        (s.price, s.size, s.order_type, s.expiration) = (price, size, ot, exp);
        assert!(signer.sign(&s, "o", 1, 1).is_err(), "{price} {size} {ot} {exp}");
    }
    s.token_id = "12x".into();
    (s.price, s.size, s.order_type, s.expiration) = (0.5, 5.0, OrderType::Fak, 0);
    assert!(signer.sign(&s, "o", 1, 1).is_err());
    let dbg = format!("{signer:?}");
    assert!(!dbg.contains("4c0883a6"), "{dbg}");
}
