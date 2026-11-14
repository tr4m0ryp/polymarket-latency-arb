//! Every hard cap trips with its reason, in the documented order.
mod common;
use btl_risk::Limits;
use common::*;

#[test]
fn base_order_passes() {
    let t = Tmp::new();
    assert_eq!(book(&t.state()).check(&base(), NOW), None);
}

#[test]
fn stopped() {
    let t = Tmp::new();
    let mut rb = book(&t.state());
    rb.stop("x".into());
    assert_eq!(rb.check(&base(), NOW), Some("stopped"));
}

#[test]
fn day_locked() {
    let t = Tmp::new();
    let rb = book(&t.state());
    std::fs::write(t.state().join(format!("lock-{DAY}")), "{}").unwrap();
    assert_eq!(rb.check(&base(), NOW), Some("day_locked"));
}

#[test]
fn max_shares_and_notional() {
    let t = Tmp::new();
    let rb = book(&t.state());
    assert_eq!(rb.check(&it(0.5, 6.0, "m1", "UP"), NOW), Some("max_shares"));
    assert_eq!(
        rb.check(&it(0.61, 5.0, "m1", "UP"), NOW),
        Some("max_notional")
    );
    assert_eq!(rb.check(&it(0.60, 5.0, "m1", "UP"), NOW), None);
}

#[test]
fn venue_minimums() {
    let t = Tmp::new();
    let rb = book(&t.state());
    assert_eq!(
        rb.check(&it(0.5, 4.0, "m1", "UP"), NOW),
        Some("below_venue_min_shares")
    );
    assert_eq!(
        rb.check(&it(0.19, 5.0, "m1", "UP"), NOW),
        Some("below_venue_min_notional")
    );
}

#[test]
fn max_exposure_counts_open_positions() {
    let t = Tmp::new();
    let mut rb = book(&t.state());
    for i in 0..5 {
        rb.fill(&it(0.5, 5.0, &format!("m{i}"), "UP"), 5.0, 2.5, 0.0875);
    }
    assert!((rb.exposure() - 12.9375).abs() < 1e-9);
    assert_eq!(
        rb.check(&it(0.40, 5.0, "x", "UP"), NOW),
        Some("max_exposure")
    );
}

#[test]
fn inflight_counts_as_exposure() {
    // A reservation counts at its worst case (notional + fee) until released.
    let t = Tmp::new();
    let mut rb = book(&t.state());
    for i in 0..5 {
        rb.fill(&it(0.5, 5.0, &format!("m{i}"), "UP"), 5.0, 2.5, 0.0875);
    }
    rb.reserve("s0", &it(0.40, 5.0, "z", "UP"), NOW); // worst 2.0 + fee
    assert!(rb.exposure() > 14.9);
    rb.release("s0");
    assert!((rb.exposure() - 12.9375).abs() < 1e-9);
}

#[test]
fn loss_headroom() {
    let t = Tmp::new();
    let mut rb = book(&t.state());
    for i in 0..3 {
        let x = it(0.5, 5.0, &format!("l{i}"), "UP");
        rb.fill(&x, 5.0, 2.5, 0.0875);
        rb.resolve(&format!("l{i}"), 0.0);
    }
    assert_eq!(rb.exposure(), 0.0);
    assert!((rb.pnl() + 7.7625).abs() < 1e-9);
    assert_eq!(rb.check(&base(), NOW), Some("loss_headroom"));
    assert_eq!(rb.check(&it(0.20, 5.0, "m1", "UP"), NOW), None); // worst 1.11 keeps pnl > -10
}

#[test]
fn max_orders_hour_and_window() {
    let t = Tmp::new();
    let mut rb = book(&t.state());
    send_n(&mut rb, 40, NOW - 3000.0, 1.0);
    let x = it(0.5, 5.0, "fresh", "UP");
    assert_eq!(rb.check(&x, NOW), Some("max_orders_hour"));
    assert_eq!(rb.orders_last_hour(NOW), 40);
    assert_eq!(rb.check(&x, NOW + 601.0), None); // the oldest left the 3600 s window
}

#[test]
fn balance_minus_inflight() {
    let t = Tmp::new();
    let mut rb = book(&t.state());
    assert_eq!(rb.balance(), None);
    rb.set_balance(Some(1.0));
    assert_eq!(rb.check(&base(), NOW), Some("balance"));
    rb.set_balance(Some(50.0));
    assert_eq!(rb.check(&base(), NOW), None);
    rb.set_balance(Some(3.0));
    rb.fill(&it(0.5, 5.0, "a", "UP"), 5.0, 2.5, 0.0875); // balance drops to 0.4125
    assert_eq!(rb.check(&base(), NOW), Some("balance"));
}

#[test]
fn max_inflight_one() {
    let t = Tmp::new();
    let mut rb = book(&t.state());
    rb.reserve("a", &it(0.5, 5.0, "m1", "UP"), NOW);
    assert_eq!(rb.inflight_count(), 1);
    assert_eq!(
        rb.check(&it(0.5, 5.0, "m2", "UP"), NOW + 5.0),
        Some("max_inflight")
    );
    rb.release("a");
    assert_eq!(rb.check(&it(0.5, 5.0, "m2", "UP"), NOW + 5.0), None);
}

#[test]
fn refractory_is_per_slug() {
    let t = Tmp::new();
    let mut rb = book(&t.state());
    rb.reserve("a", &it(0.5, 5.0, "m1", "UP"), NOW);
    rb.release("a");
    assert_eq!(
        rb.check(&it(0.5, 5.0, "m1", "DN"), NOW + 0.1),
        Some("refractory")
    );
    assert_eq!(rb.check(&it(0.5, 5.0, "m2", "UP"), NOW + 0.1), None); // other market
    assert_eq!(rb.check(&it(0.5, 5.0, "m1", "UP"), NOW + 0.2), None);
}

#[test]
fn refractory_can_be_tightened() {
    let t = Tmp::new();
    let l = Limits::default()
        .lowered(btl_risk::LimitOverrides {
            min_refractory_s: Some(1.0),
            ..Default::default()
        })
        .unwrap();
    let mut rb = btl_risk::RiskBook::open(l, t.state(), NOW).unwrap();
    rb.reserve("a", &base(), NOW);
    rb.release("a");
    assert_eq!(rb.check(&base(), NOW + 0.5), Some("refractory"));
    assert_eq!(rb.check(&base(), NOW + 1.0), None);
}

#[test]
fn order_of_checks() {
    let t = Tmp::new();
    let mut rb = book(&t.state());
    rb.reserve("a", &base(), NOW);
    // in flight + too big: the pacing gate reports first
    assert_eq!(
        rb.check(&it(0.5, 6.0, "m1", "UP"), NOW + 0.01),
        Some("max_inflight")
    );
    rb.release("a");
    assert_eq!(
        rb.check(&it(0.5, 6.0, "m1", "UP"), NOW + 0.01),
        Some("refractory")
    );
    assert_eq!(
        rb.check(&it(0.5, 6.0, "m1", "UP"), NOW + 1.0),
        Some("max_shares")
    );
    rb.stop("x".into());
    assert_eq!(
        rb.check(&it(0.5, 6.0, "m1", "UP"), NOW + 1.0),
        Some("stopped")
    );
}

#[test]
fn marks_move_pnl() {
    let t = Tmp::new();
    let mut rb = book(&t.state());
    rb.fill(&base(), 5.0, 2.5, 0.0875);
    assert!((rb.pnl() + 0.0875).abs() < 1e-9); // at cost
    rb.mark("UP", 0.30);
    assert!((rb.pnl() - (1.5 - 2.5 - 0.0875)).abs() < 1e-9);
    rb.mark("UP", f64::NAN);
    assert!((rb.pnl() + 0.0875).abs() < 1e-9);
}
