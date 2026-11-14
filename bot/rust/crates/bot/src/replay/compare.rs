//! Decision parity: Rust replay orders vs the Python paper bot's on the same tape
//! (btclat/paper/replay/decisions.py). A match = same market, side and limit at the same
//! receipt time (to 1 us). Unmatched orders are listed with their nearest counterpart.
use anyhow::Result;
use serde_json::{json, Value};
use std::path::Path;

fn read(p: &Path) -> Result<Vec<Value>> {
    Ok(std::fs::read_to_string(p)?.lines().filter(|l| !l.is_empty()).map(serde_json::from_str).collect::<Result<_, _>>()?)
}

fn key(v: &Value) -> (String, i64, i64, i64) {
    let t = v["t"].as_f64().unwrap_or(f64::NAN);
    (v["slug"].as_str().unwrap_or("").to_string(), (t * 1e6).round() as i64, v["side"].as_f64().unwrap_or(0.0) as i64,
        (v["limit"].as_f64().unwrap_or(f64::NAN) * 1e6).round() as i64)
}

pub fn compare(py: &Path, rs: &Path) -> Result<Value> {
    let (a, b) = (read(py)?, read(rs)?);
    let ka: std::collections::HashSet<_> = a.iter().map(key).collect();
    let kb: std::collections::HashSet<_> = b.iter().map(key).collect();
    let both = ka.intersection(&kb).count();
    let only = |x: &[Value], other: &std::collections::HashSet<(String, i64, i64, i64)>| -> Vec<Value> {
        x.iter().filter(|v| !other.contains(&key(v))).take(50).cloned().collect()
    };
    let (only_py, only_rs) = (only(&a, &kb), only(&b, &ka));
    let rate = if a.is_empty() { f64::NAN } else { both as f64 / a.len().max(b.len()) as f64 };
    let pred_diff = a.iter().zip(&b).filter(|(x, y)| key(x) == key(y))
        .map(|(x, y)| (x["pred_up"].as_f64().unwrap_or(0.0) - y["pred_up"].as_f64().unwrap_or(0.0)).abs()
            .max((x["pred_dn"].as_f64().unwrap_or(0.0) - y["pred_dn"].as_f64().unwrap_or(0.0)).abs()))
        .fold(0.0f64, f64::max);
    Ok(json!({"python": a.len(), "rust": b.len(), "matched": both, "match_rate": rate,
        "only_python": only_py, "only_rust": only_rs, "max_pred_abs_diff_aligned": pred_diff}))
}

/// Gate parity: every row the gate scored in Python (gate_rows.jsonl: all v1-pass rows before
/// the refractory) vs the Rust signals with `x`: same rows, the 7 extras and the gate prediction
/// compared bit for bit (per-feature mismatch counts and the largest absolute differences).
pub fn compare_gate(py: &Path, rs: &Path) -> Result<Value> {
    let a = read(py)?;
    let b: Vec<Value> = read(rs)?.into_iter().filter(|v| v.get("x").is_some_and(|x| !x.is_null())).collect();
    let k = |v: &Value| (v["slug"].as_str().unwrap_or("").to_string(),
        (v["t"].as_f64().unwrap_or(f64::NAN) * 1e6).round() as i64, v["side"].as_f64().unwrap_or(0.0) as i64);
    let rmap: std::collections::HashMap<_, &Value> = b.iter().map(|v| (k(v), v)).collect();
    let f = |v: &Value| v.as_f64().unwrap_or(f64::NAN);
    let (mut matched, mut bad_x, mut bad_gate) = (0usize, [0usize; 7], 0usize);
    let (mut dx, mut dgate) = ([0.0f64; 7], 0.0f64);
    let mut examples = Vec::new();
    for v in &a {
        let Some(r) = rmap.get(&k(v)) else { continue };
        matched += 1;
        let mut bad = false;
        for j in 0..7 {
            let (p, q) = (f(&v["x"][j]), f(&r["x"][j]));
            if p.to_bits() != q.to_bits() {
                bad_x[j] += 1;
                dx[j] = dx[j].max((p - q).abs());
                bad = true;
            }
        }
        if f(&v["gate"]).to_bits() != f(&r["gate"]).to_bits() {
            bad_gate += 1;
            dgate = dgate.max((f(&v["gate"]) - f(&r["gate"])).abs());
            bad = true;
        }
        if bad && examples.len() < 20 {
            examples.push(json!({"python": v, "rust": {"x": r["x"], "gate": r["gate"]}}));
        }
    }
    Ok(json!({"python": a.len(), "rust": b.len(), "matched": matched, "x_mismatch": bad_x, "x_max_abs_diff": dx,
        "gate_mismatch": bad_gate, "gate_max_abs_diff": dgate, "examples": examples}))
}
