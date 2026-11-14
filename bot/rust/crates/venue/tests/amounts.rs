//! get_order_amounts parity on the full Python-generated grid (tick 0.01, BUY and SELL).

use btl_venue::sign::amounts::order_amounts;
use btl_venue::Side;
use serde_json::Value;

#[test]
fn amount_grid_matches_python() {
    let rows: Vec<Value> = serde_json::from_str(include_str!("fixtures/amount_vectors.json")).unwrap();
    let mut bad = Vec::new();
    for r in &rows {
        let (price, size) = (r[0].as_f64().unwrap(), r[1].as_f64().unwrap());
        let side = if r[2] == "BUY" { Side::Buy } else { Side::Sell };
        let want = (r[3].as_u64().unwrap(), r[4].as_u64().unwrap());
        let got = order_amounts(side, size, price);
        if got != want {
            bad.push(format!("{price} {size} {:?}: got {got:?} want {want:?}", side));
        }
    }
    assert!(rows.len() > 15_000, "{}", rows.len());
    assert!(bad.is_empty(), "{} of {} differ, first: {:?}", bad.len(), rows.len(), &bad[..bad.len().min(5)]);
}
