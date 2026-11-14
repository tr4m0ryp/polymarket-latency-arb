//! Decision row -> the two side-oriented model inputs (btclat/paper/model/vector.py), driven by
//! the model's own feature list `vf`, so a retrained model with another list needs no code
//! change. Float32 arithmetic of the offline table is emulated per operation; NaN / inf -> 0.
//! Column roles (research/predict/model/{derive,orient}.py): SCALED columns get a `_c` twin
//! (times delta), SWAP pairs exchange for the Down side, NEUTRAL columns keep their value, every
//! other column flips sign; tok_mid / seen / half_spread are built per side.
use anyhow::{bail, Result};

use crate::features::names::{self, Row, FAIR_P, PM_BA, PM_BB, PM_MID, ZS};
use crate::num::cephes::ndtri;
use crate::num::{f32r, pymax, pymin};

pub const SCALED: [&str; 16] = ["p_dmic0.025", "p_dmic0.05", "p_dmic0.1", "p_dmic0.25", "p_dmic1", "s_dmic0.1",
    "s_dmic0.25", "p_micoff", "s_micoff", "p_imb", "s_imb", "p_ofi0.1", "p_ofi0.4", "st_sv0.2", "mic_dev", "basis_dev"];
pub const SWAP: [(&str, &str); 9] = [("p_depb", "p_depa"), ("s_depb", "s_depa"), ("p_ttdb", "p_ttda"),
    ("s_ttdb", "s_ttda"), ("p_up0.4", "p_dn0.4"), ("p_up2", "p_dn2"), ("s_up0.4", "s_dn0.4"), ("s_up2", "s_dn2"),
    ("fair_edge_up", "fair_edge_dn")];
pub const NEUTRAL: [&str; 18] = ["p_spr", "p_lq", "p_lam", "p_ttd_min", "p_tsm", "s_spr", "s_lq", "s_lam",
    "s_ttd_min", "s_tsm", "st_tn", "ft_tn", "pm_spr", "secs_left", "lzs", "sigma", "pm_tsc", "delta"];

#[derive(Debug, Clone, Copy, PartialEq)]
enum Src {
    Row(usize),
    Delta,
    Scaled(usize),
    EdgeUp,
    EdgeDn,
}

#[derive(Debug, Clone, Copy)]
enum Col {
    Plain { up: Src, dn: Src, neg: bool },
    TokMid,
    Seen,
    HalfSpread,
}

#[derive(Debug, Clone)]
pub struct Vectorizer {
    cols: Vec<Col>,
    pub vf: Vec<String>,
}

fn src(name: &str) -> Result<Src> {
    if let Some(i) = names::index(name) {
        return Ok(Src::Row(i));
    }
    match name {
        "delta" => return Ok(Src::Delta),
        "fair_edge_up" => return Ok(Src::EdgeUp),
        "fair_edge_dn" => return Ok(Src::EdgeDn),
        _ => {}
    }
    if let Some(base) = name.strip_suffix("_c") {
        if SCALED.contains(&base) {
            if let Some(i) = names::index(base) {
                return Ok(Src::Scaled(i));
            }
        }
    }
    bail!("model feature {name:?} is not built by the Rust bot (unknown column)")
}

impl Vectorizer {
    pub fn new(vf: &[String]) -> Result<Vectorizer> {
        let mut cols = Vec::with_capacity(vf.len());
        for c in vf {
            let col = match c.as_str() {
                "tok_mid" => Col::TokMid,
                "seen" => Col::Seen,
                "half_spread" => Col::HalfSpread,
                "pm_mid" | "t" => bail!("model feature {c:?} cannot be a model input"),
                name => {
                    let up = src(name)?;
                    if NEUTRAL.contains(&name) {
                        Col::Plain { up, dn: up, neg: false }
                    } else if let Some(&(a, b)) = SWAP.iter().find(|(a, b)| *a == name || *b == name) {
                        Col::Plain { up, dn: src(if a == name { b } else { a })?, neg: false }
                    } else {
                        Col::Plain { up, dn: up, neg: true }
                    }
                }
            };
            cols.push(col);
        }
        Ok(Vectorizer { cols, vf: vf.to_vec() })
    }

    /// (x_up, x_down) as float64, written into the given buffers (length vf.len()).
    pub fn sides(&self, f: &Row, xu: &mut [f64], xd: &mut [f64]) {
        let mid = f32r(f[PM_MID]);
        let zq = if mid.is_nan() { f64::NAN } else { ndtri(pymin(pymax(mid, 0.02), 0.98)) };
        let delta = 100.0 * (-(zq * zq) / 2.0).exp() / (2.0 * std::f64::consts::PI).sqrt() * f32r(f[ZS]) * 1e-4;
        let ba = f32r(f32r(f[PM_BA]) / 100.0);
        let bb = f32r(f32r(f[PM_BB]) / 100.0);
        let fp = f32r(f[FAIR_P]);
        let edge_up = f32r(f32r(fp - ba) - fee32(ba));
        let b1 = f32r(1.0 - bb);
        let edge_dn = f32r(f32r(f32r(1.0 - fp) - b1) - fee32(b1));
        let val = |s: Src| match s {
            Src::Row(i) => f32r(f[i]),
            Src::Delta => f32r(delta),
            Src::Scaled(i) => f32r(f32r(f[i]) * delta),
            Src::EdgeUp => edge_up,
            Src::EdgeDn => edge_dn,
        };
        let (su, sd, mdn) = (ba, f32r(1.0 - bb), f32r(1.0 - mid));
        for (j, c) in self.cols.iter().enumerate() {
            let (u, d) = match *c {
                Col::TokMid => (mid, mdn),
                Col::Seen => (su, sd),
                Col::HalfSpread => (f32r(su - mid), f32r(sd - mdn)),
                Col::Plain { up, dn, neg } => {
                    let d = val(dn);
                    (val(up), if neg { -d } else { d })
                }
            };
            xu[j] = clean(u);
            xd[j] = clean(d);
        }
    }
}

#[inline]
fn clean(x: f64) -> f64 {
    if x.is_finite() { x } else { 0.0 }
}

#[inline]
fn fee32(p: f64) -> f64 {
    let f007 = f32r(0.07);
    f32r(f32r(f007 * p) * f32r(1.0 - p))
}
