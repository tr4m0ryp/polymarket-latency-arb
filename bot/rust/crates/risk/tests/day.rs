//! UTC day roll, carry, restart after midnight, loss-cap lock.
mod common;
use btl_risk::{lock_path, utc_day};
use common::*;
use std::fs;

const MIDNIGHT: f64 = 1_791_849_600.0; // 2026-10-13 00:00:00 UTC

#[test]
fn utc_day_matches_gmtime() {
    assert_eq!(utc_day(NOW), "2026-10-12");
    assert_eq!(utc_day(0.0), "1970-01-01");
    assert_eq!(utc_day(MIDNIGHT - 0.001), "2026-10-12");
    assert_eq!(utc_day(MIDNIGHT), "2026-10-13");
    assert_eq!(utc_day(951_782_400.0), "2000-02-29");
    assert_eq!(utc_day(-1.0), "1969-12-31");
}

#[test]
fn roll_carries_positions_and_resets_realised() {
    let t = Tmp::new();
    let mut rb = book(&t.state());
    rb.fill(&it(0.5, 5.0, "open", "UP"), 5.0, 2.5, 0.0875);
    let lost = it(0.5, 5.0, "lost", "UP");
    rb.fill(&lost, 5.0, 2.5, 0.0875);
    rb.resolve("lost", 0.0);
    send_n(&mut rb, 2, MIDNIGHT - 100.0, 1.0);
    let (exp, realised) = (rb.exposure(), rb.realised());
    assert!(realised < 0.0);
    assert!(!rb.roll(NOW + 10.0)); // same day
    assert!(rb.roll(MIDNIGHT + 1.0));
    assert_eq!(rb.day(), "2026-10-13");
    assert_eq!(rb.realised(), 0.0);
    assert!((rb.exposure() - exp).abs() < 1e-9);
    assert_eq!(rb.orders_last_hour(MIDNIGHT + 1.0), 2); // rolling hour keeps counting
    let new = fs::read_to_string(rb.ledger_path()).unwrap();
    assert_eq!(new.lines().count(), 1);
    assert!(new.contains("\"k\":\"carry\"") && new.contains("\"slug\":\"open\""));
    // a restart on the new day replays the carry row
    let b =
        btl_risk::RiskBook::open(btl_risk::Limits::default(), t.state(), MIDNIGHT + 5.0).unwrap();
    assert!((b.exposure() - exp).abs() < 1e-9);
    assert_eq!(b.realised(), 0.0);
}

#[test]
fn restart_after_midnight_without_roll_carries_from_previous_ledger() {
    let t = Tmp::new();
    let mut rb = book(&t.state());
    rb.fill(&it(0.5, 5.0, "open", "UP"), 5.0, 2.5, 0.0875);
    send_n(&mut rb, 2, MIDNIGHT - 100.0, 1.0);
    rb.fill(&it(0.5, 5.0, "lost", "UP"), 5.0, 2.5, 0.0875);
    rb.resolve("lost", 0.0);
    let b =
        btl_risk::RiskBook::open(btl_risk::Limits::default(), t.state(), MIDNIGHT + 60.0).unwrap();
    assert_eq!(b.day(), "2026-10-13");
    assert!((b.exposure() - 2.5875).abs() < 1e-9);
    assert_eq!(b.realised(), 0.0);
    assert_eq!(b.orders_last_hour(MIDNIGHT + 60.0), 2);
    // and it was persisted: reopening reads today's own ledger
    let c =
        btl_risk::RiskBook::open(btl_risk::Limits::default(), t.state(), MIDNIGHT + 70.0).unwrap();
    assert!((c.exposure() - 2.5875).abs() < 1e-9);
}

fn lose(rb: &mut btl_risk::RiskBook, n: usize) {
    for i in 0..n {
        let x = it(0.55, 5.0, &format!("x{i}"), "UP");
        rb.fill(&x, 5.0, 2.75, 0.0866);
        rb.resolve(&format!("x{i}"), 0.0);
    }
}

#[test]
fn breach_writes_lock_once_and_stops() {
    let t = Tmp::new();
    let mut rb = book(&t.state());
    lose(&mut rb, 3);
    assert!(!rb.breach() && !rb.locked()); // -8.51
    assert!(rb.stop_reason().is_none());
    lose(&mut rb, 1); // -11.35
    assert!(rb.breach() && rb.locked());
    let lp = lock_path(&t.state(), DAY);
    let first = fs::read_to_string(&lp).unwrap();
    assert!(first.contains("\"pnl\"") && first.contains("\"realised\""));
    let mtime = fs::metadata(&lp).unwrap().modified().unwrap();
    lose(&mut rb, 1);
    assert!(rb.breach());
    assert_eq!(fs::read_to_string(&lp).unwrap(), first); // not rewritten
    assert_eq!(fs::metadata(&lp).unwrap().modified().unwrap(), mtime);
    assert!(rb
        .stop_reason()
        .unwrap()
        .starts_with("loss cap: pnl -14.18 <= -10.0"));
    assert_eq!(rb.check(&base(), NOW), Some("stopped"));
    // restart the same day: ledger replayed, lock still there
    let again =
        btl_risk::RiskBook::open(btl_risk::Limits::default(), t.state(), NOW + 60.0).unwrap();
    assert!(again.locked());
    assert_eq!(again.check(&base(), NOW + 60.0), Some("day_locked"));
}

#[test]
fn breach_counts_marked_losses() {
    let t = Tmp::new();
    let mut rb = book(&t.state());
    for i in 0..5 {
        rb.fill(
            &it(0.6, 5.0, &format!("o{i}"), &format!("T{i}")),
            5.0,
            3.0,
            0.1,
        );
        rb.mark(&format!("T{i}"), 0.05);
    }
    // marked: 5 * (0.25 - 3.1) = -14.25
    assert!(rb.breach());
}

#[test]
fn next_day_is_not_locked_by_yesterday() {
    let t = Tmp::new();
    let mut rb = book(&t.state());
    lose(&mut rb, 4);
    assert!(rb.breach());
    rb.roll(MIDNIGHT + 1.0);
    assert!(!rb.locked());
    assert!(rb.stop_reason().is_some()); // the process-level stop persists, like Python
}
