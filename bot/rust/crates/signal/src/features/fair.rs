//! The strategy's `pzm` fair value (btclat/paper/features/fair.py, weights from
//! data/out/strategy/fair-pzm.json): fair = Phi(Phi^-1(mid) + w . x), x = lag-bucket log moves
//! (bp) of the perp mid, spot mid, perp microprice, spot microprice, times zscale * 1e-4.
use anyhow::{bail, Context, Result};
use std::path::Path;

use crate::state::book::{BookState, LMIC, LMID};

pub const BUCKETS: [(f64, f64); 7] = [(0.0, 0.05), (0.05, 0.1), (0.1, 0.2), (0.2, 0.4), (0.4, 0.8), (0.8, 1.6), (1.6, 3.2)];

#[derive(Debug, Clone)]
pub struct Pzm {
    pub w: [f64; 28],
}

impl Pzm {
    pub fn load(path: &Path) -> Result<Pzm> {
        let j: serde_json::Value = serde_json::from_slice(&std::fs::read(path).with_context(|| format!("read {}", path.display()))?)?;
        let srcs: Vec<&str> = j["srcs"].as_array().context("srcs")?.iter().filter_map(|v| v.as_str()).collect();
        if srcs != ["perp", "smid", "pmic", "smic"] || j["extra"].as_bool() != Some(false) || j["imb"].as_bool() != Some(false) {
            bail!("fair-pzm.json: unsupported layout {srcs:?}");
        }
        let w: Vec<f64> = j["w"].as_array().context("w")?.iter().filter_map(|v| v.as_f64()).collect();
        if w.len() != 28 {
            bail!("fair-pzm.json: {} weights, expected 28", w.len());
        }
        Ok(Pzm { w: w.try_into().unwrap() })
    }

    /// w . x, summed in index order (numpy's dot on the research host sums sequentially).
    pub fn dz(&self, q: f64, perp: &BookState, spot: &BookState, zs: f64) -> f64 {
        let mut s = 0.0;
        let mut k = 0;
        for (st, col) in [(perp, LMID), (spot, LMID), (perp, LMIC), (spot, LMIC)] {
            for (a, b) in BUCKETS {
                let r = 1e4 * (st.hist.at(col, q - a) - st.hist.at(col, q - b));
                let x = (if r.is_nan() { 0.0 } else { r }) * zs * 1e-4;
                s += x * self.w[k];
                k += 1;
            }
        }
        s
    }
}
