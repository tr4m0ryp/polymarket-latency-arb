//! Ledger replay and Python/Rust file compatibility.
mod common;
use btl_risk::RiskBook;
use common::*;
use std::fs;

const PY: &str = include_str!("fixtures/python-ledger-2026-10-12.jsonl");

fn close(a: f64, b: f64) -> bool {
    (a - b).abs() < 1e-9
}

#[test]
fn replay_reproduces_exposure_pnl_and_sends() {
    let t = Tmp::new();
    let mut a = book(&t.state());
    send_n(&mut a, 3, NOW - 50.0, 5.0);
    a.fill(&it(0.5, 5.0, "m1", "UP"), 5.0, 2.5, 0.0875);
    a.fill(&it(0.45, 5.0, "m2", "DN"), 5.0, 2.25, 0.086625);
    a.fill(&it(0.55, 5.0, "m3", "UP"), 5.0, 2.75, 0.086625);
    a.resolve("m3", 0.0);
    a.resolve("nope", 1.0); // unknown slug writes nothing
    let b = book(&t.state());
    assert!(close(a.exposure(), b.exposure()));
    assert!(close(a.pnl(), b.pnl()));
    assert!(close(a.realised(), b.realised()));
    assert_eq!(a.orders_last_hour(NOW), b.orders_last_hour(NOW));
    assert_eq!(b.orders_last_hour(NOW), 3);
    assert_eq!(
        fs::read_to_string(a.ledger_path()).unwrap().lines().count(),
        3 + 3 + 1
    );
}

#[test]
fn orders_hour_survives_restart() {
    let t = Tmp::new();
    let mut a = book(&t.state());
    send_n(&mut a, 40, NOW - 10.0, 0.0);
    assert_eq!(
        book(&t.state()).check(&base(), NOW),
        Some("max_orders_hour")
    );
}

#[test]
fn inflight_is_not_persisted() {
    let t = Tmp::new();
    let mut a = book(&t.state());
    a.reserve("c", &base(), NOW);
    let b = book(&t.state());
    assert_eq!(b.inflight_count(), 0);
    assert_eq!(b.orders_last_hour(NOW), 1);
}

#[test]
fn reads_a_ledger_written_by_the_python_book() {
    let t = Tmp::new();
    fs::create_dir_all(t.state()).unwrap();
    fs::write(t.state().join(format!("ledger-{DAY}.jsonl")), PY).unwrap();
    let rb = book(&t.state());
    // values printed by the Python RiskBook on the same operations
    assert!(close(rb.exposure(), 7.611485));
    assert!(close(rb.realised(), -2.836625));
    assert!(close(rb.pnl(), -3.09811));
    assert_eq!(rb.orders_last_hour(NOW), 4);
    assert_eq!(rb.positions().count(), 2); // m3 resolved
    let m1 = rb.positions().find(|(k, _)| k.0 == "m1").unwrap().1;
    assert!(close(m1.sh, 10.0) && close(m1.cost, 5.1));
}

#[test]
fn rust_rows_have_the_python_keys() {
    let t = Tmp::new();
    let mut a = book(&t.state());
    a.reserve("sig", &base(), NOW);
    a.release("sig");
    a.fill(&base(), 5.0, 2.5, 0.0875);
    a.resolve("m1", 1.0);
    let text = fs::read_to_string(a.ledger_path()).unwrap();
    let rows: Vec<serde_json::Value> = text
        .lines()
        .map(|l| serde_json::from_str(l).unwrap())
        .collect();
    let keys =
        |v: &serde_json::Value| -> Vec<String> { v.as_object().unwrap().keys().cloned().collect() };
    let sorted = |mut k: Vec<String>| {
        k.sort();
        k
    };
    assert_eq!(sorted(keys(&rows[0])), ["k", "oid", "t"]);
    assert_eq!(
        sorted(keys(&rows[1])),
        ["cost", "end", "fee", "k", "sh", "slug", "token", "up"]
    );
    assert_eq!(sorted(keys(&rows[2])), ["k", "outcome", "slug"]);
    assert_eq!(rows[0]["k"], "send");
    assert!(text.starts_with("{\"k\":\"send\",\"t\":"));
}

#[test]
fn corrupt_line_fails_closed() {
    let t = Tmp::new();
    fs::create_dir_all(t.state()).unwrap();
    fs::write(
        t.state().join(format!("ledger-{DAY}.jsonl")),
        format!("{PY}{{\"k\":\"fi"),
    )
    .unwrap();
    let e = RiskBook::open(btl_risk::Limits::default(), t.state(), NOW)
        .err()
        .unwrap();
    assert!(e.to_string().contains("line 10"), "{e}");
}
