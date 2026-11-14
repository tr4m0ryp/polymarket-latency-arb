//! Numerics against scipy / numpy / CPython values (tests/gen_num.py): must be bit-identical.
use btl_signal::num::{cephes, pyround3, pysum};

fn fixture() -> serde_json::Value {
    serde_json::from_str(include_str!("fixtures/num.json")).unwrap()
}

fn pairs(v: &serde_json::Value) -> Vec<(f64, f64)> {
    v.as_array().unwrap().iter().map(|p| (p[0].as_f64().unwrap(), p[1].as_f64().unwrap())).collect()
}

#[test]
fn ndtri_matches_scipy() {
    for (y, want) in pairs(&fixture()["ndtri"]) {
        assert_eq!(cephes::ndtri(y).to_bits(), want.to_bits(), "ndtri({y})");
    }
}

#[test]
fn ndtr_matches_scipy() {
    for (x, want) in pairs(&fixture()["ndtr"]) {
        assert_eq!(cephes::ndtr(x).to_bits(), want.to_bits(), "ndtr({x})");
    }
}

#[test]
fn pairwise_sum_matches_numpy() {
    for s in fixture()["sums"].as_array().unwrap() {
        let a: Vec<f64> = s["a"].as_array().unwrap().iter().map(|x| x.as_f64().unwrap()).collect();
        assert_eq!(pysum::pairwise(&a), s["sum"].as_f64().unwrap(), "n={}", a.len());
        assert_eq!(pysum::mean(&a), s["mean"].as_f64().unwrap(), "n={}", a.len());
    }
}

#[test]
fn round3_matches_python() {
    for (t, want) in pairs(&fixture()["round3"]) {
        assert_eq!(pyround3(t), want, "round({t}, 3)");
    }
}

#[test]
fn python_max_min_nan() {
    use btl_signal::num::{pymax, pymin};
    assert!(pymax(f64::NAN, 1.0).is_nan());
    assert_eq!(pymax(1.0, f64::NAN), 1.0);
    assert!(pymin(f64::NAN, 1.0).is_nan());
    assert_eq!(pymin(1.0, f64::NAN), 1.0);
}
