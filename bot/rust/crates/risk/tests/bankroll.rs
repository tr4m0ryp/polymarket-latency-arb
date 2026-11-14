//! Bankroll caps: equity-scaled sizing, the reserve, fractional per-market / open caps, side
//! policies, fills per market, the day drawdown pause and the all-time-peak floor halt.
mod common;
use btl_risk::{Bankroll, Intent, Limits, RiskBook, SidePolicy, Sizing};
use common::*;

fn caps() -> Bankroll {
    Bankroll { sizing: Sizing::Frac(0.02), max_sh: 500.0, market_frac: Some(0.10), open_frac: None,
        side: SidePolicy::Any, max_fills: u32::MAX, dd_stop: None, reserve: 0.0, floor: None }
}

fn bk(dir: &std::path::Path, b: Bankroll, bal: f64) -> RiskBook {
    let mut rb = RiskBook::open(Limits::default(), dir, NOW).unwrap();
    rb.set_balance(Some(bal));
    rb.set_bankroll(b.checked().unwrap());
    rb
}

fn up(price: f64, slug: &str) -> Intent {
    it(price, 0.0, slug, "UP")
}

fn down(price: f64, slug: &str) -> Intent {
    Intent { up: false, token: "DN".into(), ..it(price, 0.0, slug, "DN") }
}

#[test]
fn fraction_sizing_scales_with_equity() {
    let t = Tmp::new();
    let mut rb = bk(&t.state(), caps(), 100.0);
    assert_eq!(rb.size_for(&up(0.40, "m1"), 0.03), Ok(5.0)); // 2% of $100 = $2 -> 5 sh, venue floor 5
    rb.set_balance(Some(1000.0));
    assert_eq!(rb.size_for(&up(0.40, "m1"), 0.03), Ok(50.0)); // $20 / 0.40
}

#[test]
fn reserve_is_untouchable() {
    let t = Tmp::new();
    let mut rb = bk(&t.state(), Bankroll { reserve: 43.04, market_frac: None, ..caps() }, 143.04);
    assert!((rb.equity().unwrap() - 100.0).abs() < 1e-9);
    assert_eq!(rb.size_for(&up(0.50, "m1"), 0.03), Ok(5.0));
    // working cash $1.50: 5 sh at 0.5 no longer fits, the reserve is not used
    rb.set_balance(Some(44.54));
    assert_eq!(rb.size_for(&up(0.50, "m1"), 0.03), Err("balance"));
    rb.set_balance(Some(43.04));
    assert_eq!(rb.size_for(&up(0.50, "m1"), 0.03), Err("reserve"));
    rb.set_balance(Some(20.0));
    assert_eq!(rb.size_for(&up(0.50, "m1"), 0.03), Err("reserve"));
    // the hard check also keeps the reserve out of the affordability test
    let mut rb2 = bk(&t.state(), Bankroll { reserve: 43.04, ..caps() }, 45.0);
    assert_eq!(rb2.check(&it(0.50, 5.0, "m1", "UP"), NOW), Some("balance"));
    rb2.set_balance(Some(46.0));
    assert_eq!(rb2.check(&it(0.50, 5.0, "m1", "UP"), NOW), None);
}

#[test]
fn market_cap_shrinks_then_skips() {
    let t = Tmp::new();
    let mut rb = bk(&t.state(), Bankroll { sizing: Sizing::Fixed(60.0), ..caps() }, 100.0);
    // 10% of $100 = $10 per market: 60 sh at 0.5 shrinks to 19 sh
    let q = rb.size_for(&up(0.50, "m1"), 0.03).unwrap();
    assert_eq!(q, 19.0);
    rb.fill(&it(0.50, q, "m1", "UP"), q, 9.5, 0.33);
    assert_eq!(rb.size_for(&up(0.50, "m1"), 0.03), Err("market_cap"));
    assert!(rb.size_for(&up(0.50, "m2"), 0.03).is_ok());
}

#[test]
fn open_cap_counts_every_market() {
    let t = Tmp::new();
    let mut rb = bk(&t.state(), Bankroll { open_frac: Some(0.25), market_frac: None, ..caps() }, 100.0);
    for i in 0..4 {
        rb.fill(&it(0.50, 10.0, &format!("m{i}"), "UP"), 10.0, 5.0, 0.0);
    }
    // equity still $100 (cost basis), open $20: room $5 -> 9 sh at 0.5 + fee
    let q = rb.size_for(&up(0.50, "m9"), 0.03).unwrap();
    assert!(q <= 9.0 && q >= 5.0, "{q}");
    rb.fill(&it(0.50, 9.0, "m9", "UP"), 9.0, 4.5, 0.0);
    assert_eq!(rb.size_for(&up(0.50, "m10"), 0.03), Err("open_cap"));
}

#[test]
fn side_policies() {
    let t = Tmp::new();
    let mut one = bk(&t.state(), Bankroll { side: SidePolicy::OneDirection, ..caps() }, 100.0);
    one.fill(&it(0.50, 5.0, "m1", "UP"), 5.0, 2.5, 0.0);
    assert_eq!(one.size_for(&down(0.45, "m1"), 0.03), Err("one_side"));
    assert!(one.size_for(&up(0.50, "m1"), 0.03).is_ok());

    let t2 = Tmp::new();
    let mut per = bk(&t2.state(), Bankroll { side: SidePolicy::PerSide, max_fills: 1, ..caps() }, 100.0);
    per.fill(&it(0.50, 5.0, "m1", "UP"), 5.0, 2.5, 0.0);
    assert_eq!(per.size_for(&up(0.50, "m1"), 0.03), Err("max_fills"));
    assert!(per.size_for(&down(0.45, "m1"), 0.03).is_ok());

    let t3 = Tmp::new();
    let mut hedge = bk(&t3.state(), Bankroll { side: SidePolicy::HedgeOnly, sizing: Sizing::Fixed(20.0),
        market_frac: None, ..caps() }, 100.0);
    hedge.fill(&it(0.50, 8.0, "m1", "UP"), 8.0, 4.0, 0.0);
    // opposite side capped at the 8-share imbalance: never more Down than Up
    assert_eq!(hedge.size_for(&down(0.45, "m1"), 0.03), Ok(8.0));
    hedge.fill(&Intent { up: false, ..it(0.45, 8.0, "m1", "DN") }, 8.0, 3.6, 0.0);
    assert_eq!(hedge.size_for(&down(0.45, "m1"), 0.03), Err("hedge_only"));
    assert_eq!(hedge.size_for(&up(0.50, "m1"), 0.03), Ok(20.0));
}

#[test]
fn max_fills_per_market() {
    let t = Tmp::new();
    let mut rb = bk(&t.state(), Bankroll { max_fills: 2, ..caps() }, 100.0);
    rb.fill(&it(0.50, 5.0, "m1", "UP"), 5.0, 2.5, 0.0);
    assert!(rb.size_for(&down(0.45, "m1"), 0.03).is_ok());
    rb.fill(&Intent { up: false, ..it(0.45, 5.0, "m1", "DN") }, 5.0, 2.25, 0.0);
    assert_eq!(rb.size_for(&up(0.50, "m1"), 0.03), Err("max_fills"));
    rb.resolve("m1", 1.0);
    assert!(rb.size_for(&up(0.50, "m1"), 0.03).is_ok(), "counts drop with the market");
}

#[test]
fn drawdown_pauses_the_day() {
    let t = Tmp::new();
    let mut rb = bk(&t.state(), Bankroll { dd_stop: Some(0.25), ..caps() }, 100.0);
    assert!(rb.size_for(&up(0.50, "m1"), 0.03).is_ok());
    rb.set_balance(Some(120.0)); // day peak 120 (winnings redeemed)
    assert!(rb.size_for(&up(0.50, "m1"), 0.03).is_ok());
    rb.set_balance(Some(89.0)); // -25.8% from the day's peak
    assert_eq!(rb.size_for(&up(0.50, "m1"), 0.03), Err("dd_stop"));
    assert!(t.state().join(format!("lock-{DAY}")).exists());
    assert_eq!(rb.check(&it(0.50, 5.0, "m1", "UP"), NOW), Some("day_locked"));
}

#[test]
fn floor_halts_for_good() {
    let t = Tmp::new();
    let mut rb = bk(&t.state(), Bankroll { floor: Some(0.5), ..caps() }, 100.0);
    assert!(rb.size_for(&up(0.50, "m1"), 0.03).is_ok());
    rb.set_balance(Some(300.0));
    assert!(rb.size_for(&up(0.50, "m1"), 0.03).is_ok());
    assert_eq!(std::fs::read_to_string(t.state().join("peak")).unwrap().trim(), "300");
    rb.set_balance(Some(149.0));
    assert_eq!(rb.size_for(&up(0.50, "m1"), 0.03), Err("floor_halt"));
    // a restart keeps the peak and the halt
    let rb2 = bk(&t.state(), Bankroll { floor: Some(0.5), ..caps() }, 149.0);
    assert_eq!(rb2.peak(), 300.0);
    assert_eq!(rb2.check(&it(0.50, 5.0, "m1", "UP"), NOW), Some("floor_halt"));
}

#[test]
fn resolved_winnings_count_until_redeemed() {
    let t = Tmp::new();
    let mut rb = bk(&t.state(), caps(), 100.0);
    rb.fill(&it(0.50, 10.0, "m1", "UP"), 10.0, 5.0, 0.0);
    assert!((rb.equity().unwrap() - 100.0).abs() < 1e-9);
    rb.resolve("m1", 1.0); // won: $10 owed, not yet in the balance
    assert!((rb.equity().unwrap() - 105.0).abs() < 1e-9);
    rb.set_balance(Some(105.0)); // redeemed
    assert!((rb.claim()).abs() < 1e-9);
    assert!((rb.equity().unwrap() - 105.0).abs() < 1e-9);
}

#[test]
fn bad_caps_are_refused() {
    for b in [Bankroll { market_frac: Some(1.5), ..caps() }, Bankroll { floor: Some(0.0), ..caps() },
              Bankroll { sizing: Sizing::Fixed(4.0), ..caps() }, Bankroll { reserve: -1.0, ..caps() },
              Bankroll { sizing: Sizing::Frac(0.0), ..caps() }] {
        assert!(b.checked().is_err(), "{b:?}");
    }
}
