//! Offline gate: approval, kill file, day lock.
mod common;
use btl_risk::{killed, lock_path, offline_checks, utc_day, Refused};
use common::*;
use std::fs;

#[test]
fn clean_config_passes() {
    let t = Tmp::new();
    assert_eq!(offline_checks(true, &t.0, NOW), Ok(()));
    assert!(!killed(&t.0));
}

#[test]
fn needs_approval() {
    let t = Tmp::new();
    assert_eq!(offline_checks(false, &t.0, NOW), Err(Refused::NotApproved));
}

#[test]
fn kill_file_refuses_and_is_seen_by_killed() {
    let t = Tmp::new();
    fs::write(t.0.join("KILL"), "").unwrap();
    assert!(killed(&t.0));
    let e = offline_checks(true, &t.0, NOW).unwrap_err();
    assert_eq!(e, Refused::Killed(t.0.join("KILL")));
    assert!(e.to_string().contains("kill file"));
    fs::remove_file(t.0.join("KILL")).unwrap();
    assert!(!killed(&t.0));
    assert!(offline_checks(true, &t.0, NOW).is_ok());
}

#[test]
fn todays_lock_refuses_but_other_days_do_not() {
    let t = Tmp::new();
    let state = t.0.join("state");
    fs::create_dir_all(&state).unwrap();
    fs::write(lock_path(&state, "2026-10-11"), "{}").unwrap();
    assert!(offline_checks(true, &t.0, NOW).is_ok());
    fs::write(lock_path(&state, &utc_day(NOW)), "{}").unwrap();
    match offline_checks(true, &t.0, NOW) {
        Err(Refused::DayLocked { day, .. }) => assert_eq!(day, "2026-10-12"),
        other => panic!("{other:?}"),
    }
    assert!(offline_checks(true, &t.0, NOW + 86400.0).is_ok());
}

#[test]
fn the_book_lock_is_what_the_gate_reads() {
    let t = Tmp::new();
    let mut rb = book(&t.0.join("state"));
    for i in 0..4 {
        rb.fill(&it(0.55, 5.0, &format!("x{i}"), "UP"), 5.0, 2.75, 0.0866);
        rb.resolve(&format!("x{i}"), 0.0);
    }
    assert!(rb.breach());
    assert!(matches!(
        offline_checks(true, &t.0, NOW),
        Err(Refused::DayLocked { .. })
    ));
}
