//! No limit can be raised past its hard value; an edited Limits is refused. Since 2026-10-14
//! the money and order caps are uncapped (1e9 / u32::MAX) by the user's call: run as designed.
mod common;
use btl_risk::{LimitOverrides as O, Limits, RiskBook};
use common::*;

fn refused(o: O) -> bool {
    Limits::default().lowered(o).is_err()
}

#[test]
fn every_limit_refuses_loosening() {
    assert!(refused(O {
        max_shares: Some(2e9),
        ..Default::default()
    }));
    assert!(refused(O {
        max_inflight: Some(65),
        ..Default::default()
    }));
    assert!(refused(O {
        min_refractory_s: Some(0.1),
        ..Default::default()
    })); // smaller = looser
}

#[test]
fn rejects_nonpositive_and_nan() {
    assert!(refused(O {
        loss_cap: Some(0.0),
        ..Default::default()
    }));
    assert!(refused(O {
        loss_cap: Some(-1.0),
        ..Default::default()
    }));
    assert!(refused(O {
        max_shares: Some(f64::NAN),
        ..Default::default()
    }));
    assert!(refused(O {
        max_inflight: Some(0),
        ..Default::default()
    }));
    assert!(refused(O {
        min_refractory_s: Some(0.0),
        ..Default::default()
    }));
}

#[test]
fn lowering_works() {
    let l = Limits::default()
        .lowered(O {
            max_orders_hour: Some(10),
            loss_cap: Some(5.0),
            min_refractory_s: Some(0.5),
            ..Default::default()
        })
        .unwrap();
    assert_eq!(
        (l.max_orders_hour, l.loss_cap, l.min_refractory_s),
        (10, 5.0, 0.5)
    );
    assert_eq!(l.max_exposure, 1e9);
    assert_eq!(
        Limits::default().lowered(O::default()).unwrap(),
        Limits::default()
    );
}

#[test]
fn hard_values() {
    let l = Limits::default();
    assert_eq!(
        (l.max_shares, l.max_notional, l.max_exposure, l.loss_cap),
        (1e9, 1e9, 1e9, 1e9)
    );
    assert_eq!(
        (l.max_orders_hour, l.max_inflight, l.min_refractory_s),
        (u32::MAX, 64, 0.2)
    );
    assert!((btl_risk::fee(0.5, 5.0) - 0.0875).abs() < 1e-12);
}

#[test]
fn tampered_limits_refused_by_checked_and_open() {
    let l = Limits {
        max_exposure: 2e9,
        ..Default::default()
    };
    assert!(l.checked().is_err());
    let t = Tmp::new();
    assert!(RiskBook::open(l, t.state(), NOW).is_err());
    let l = Limits {
        min_refractory_s: 0.05,
        ..Default::default()
    };
    assert!(RiskBook::open(l, t.state(), NOW).is_err());
    assert!(Limits::default().checked().is_ok());
}
