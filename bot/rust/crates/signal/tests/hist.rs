//! Book-survival extras (research/vetohold/label/extras.py) on hand-built message sequences, and
//! numpy's float32 pairwise sum (fixtures/f32sum.json, numpy `.sum()` of masked float32 ladders).
use btl_signal::features::extras;
use btl_signal::num::pysum::pairwise_f32;
use btl_signal::state::PmHist;

#[test]
fn f32_pairwise_sum_matches_numpy() {
    let v: serde_json::Value = serde_json::from_str(include_str!("fixtures/f32sum.json")).unwrap();
    for s in v["sums"].as_array().unwrap() {
        let a: Vec<f32> = s["a"].as_array().unwrap().iter().map(|x| x.as_f64().unwrap() as f32).collect();
        assert_eq!(pairwise_f32(&a) as f64, s["sum"].as_f64().unwrap());
    }
}

const START: f64 = 1_791_900_600.0;

#[test]
fn grid_book_hides_messages_inside_the_current_5ms_row() {
    let mut h = PmHist::new(START, START + 300.0);
    let t0 = START - 2.0;
    // snapshot: Up ask 40 c x 100, Up bid 38 c x 50, venue stamp 20 ms before receipt
    h.on_msg(t0 + 10.0, t0 + 9.98, true, &[(1, 38, 50.0), (-1, 40, 100.0)]);
    // ask 40 c grows to 300 at t0 + 20.0123 (row 4003): invisible at 20.0149 (row 4002)
    h.on_msg(t0 + 20.0123, t0 + 20.0, false, &[(-1, 40, 300.0)]);
    let x = extras(&mut h, t0 + 20.0149, 1.0, 0.40);
    assert_eq!(x[0], 100.0, "dep0 still reads the earlier row");
    assert_eq!(x[3], 0.0, "ddep0.25");
    let x = extras(&mut h, t0 + 20.0150, 1.0, 0.40);
    assert_eq!((x[0], x[1], x[2]), (300.0, 300.0, 300.0));
    assert_eq!(x[3], 200.0, "ddep0.25 = 300 - 100");
    assert_eq!(x[5], ((t0 + 20.0150) - (t0 + 20.0123)) as f32, "age since the ask column was touched");
    // Down side: buy Down at 1 - bid = 62 c; dep0 = Up bid at 38 c; age from the snapshot (capped)
    let x = extras(&mut h, t0 + 75.0, -1.0, 0.62);
    assert_eq!(x[0], 50.0);
    assert_eq!(x[5], 60.0);
    // rlag: 3 rows at 20 ms (snapshot marker + 2 levels) and 1 at 12.3 ms
    let want = (3.0 * ((t0 + 10.0) - (t0 + 9.98)) + ((t0 + 20.0123) - (t0 + 20.0))) / 4.0;
    assert!((x[6] as f64 - want).abs() < 1e-6, "{} vs {want}", x[6]);
}

#[test]
fn rlag_averages_the_last_50_rows() {
    let mut h = PmHist::new(START, START + 300.0);
    for k in 0..80 {
        let t = START + k as f64 * 0.1;
        let lag = if k < 30 { 1.0 } else { 0.5 };
        h.on_msg(t, t - lag, false, &[(1, 30, 10.0)]);
    }
    assert_eq!(h.rlag(), 0.5);
}
