#![allow(dead_code)]
use btl_risk::{Intent, LimitOverrides, Limits, RiskBook};
use std::path::{Path, PathBuf};
use std::sync::atomic::{AtomicU32, Ordering};

pub const NOW: f64 = 1_791_800_000.0; // 2026-10-12 UTC
pub const DAY: &str = "2026-10-12";

/// Self-removing unique temp dir (no external crate).
pub struct Tmp(pub PathBuf);

impl Tmp {
    pub fn new() -> Tmp {
        static N: AtomicU32 = AtomicU32::new(0);
        let p = std::env::temp_dir().join(format!(
            "btl_risk_{}_{}",
            std::process::id(),
            N.fetch_add(1, Ordering::SeqCst)
        ));
        let _ = std::fs::remove_dir_all(&p);
        std::fs::create_dir_all(&p).unwrap();
        Tmp(p)
    }
    pub fn state(&self) -> PathBuf {
        self.0.join("state")
    }
}

impl Drop for Tmp {
    fn drop(&mut self) {
        let _ = std::fs::remove_dir_all(&self.0);
    }
}

pub fn it(price: f64, size: f64, slug: &str, token: &str) -> Intent {
    Intent {
        arm: "vt_v1_m0.03_any".into(),
        slug: slug.into(),
        token: token.into(),
        up: true,
        price,
        size,
        end: NOW + 200.0,
    }
}

pub fn base() -> Intent {
    it(0.50, 5.0, "m1", "UP")
}

/// The caps exercised by these tests, passed as CLI-style overrides (the hard constants are
/// uncapped since 2026-10-14; the mechanism still applies to any limit a run sets).
pub fn test_limits() -> Limits {
    Limits::default()
        .lowered(LimitOverrides {
            max_shares: Some(5.0),
            max_notional: Some(3.0),
            max_exposure: Some(15.0),
            loss_cap: Some(10.0),
            max_orders_hour: Some(40),
            max_inflight: Some(1),
            min_refractory_s: None,
        })
        .unwrap()
}

pub fn book(dir: &Path) -> RiskBook {
    RiskBook::open(test_limits(), dir, NOW).unwrap()
}

/// Reserve then release `n` orders, `step` seconds apart starting at `t0`, on distinct slugs.
pub fn send_n(rb: &mut RiskBook, n: usize, t0: f64, step: f64) {
    for i in 0..n {
        let x = it(0.5, 5.0, &format!("s{i}"), "UP");
        rb.reserve(&format!("c{i}"), &x, t0 + step * i as f64);
        rb.release(&format!("c{i}"));
    }
}
