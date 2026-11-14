//! `BookState.features`: the p_ / s_ block of a decision row at time q (q >= the last update).
use crate::features::names::Row;
use crate::num::{pymax, pymin};
use crate::state::book::BookState;

const DMIC_W: [f64; 5] = [0.025, 0.05, 0.1, 0.25, 1.0];
const DMID_W: [f64; 3] = [0.1, 1.0, 5.0];

fn plog(x: f64) -> f64 {
    if x > 0.0 { x.ln() } else if x == 0.0 { f64::NEG_INFINITY } else { f64::NAN }
}

impl BookState {
    /// Write the 29 columns starting at `off` (layout of features::names::BOOK).
    pub fn features(&self, q: f64, f: &mut Row, off: usize) {
        let have = self.t.is_some();
        f[off] = if have { self.imb } else { 0.0 };
        f[off + 1] = if have { self.spr } else { 1.0 };
        f[off + 2] = if have { self.lq } else { 0.0 };
        let dep = pymax(if have { self.depth } else { 1.0 }, 1e-6);
        let (lmic, lmid) = (self.lmic(q), self.lmid(q));
        for (k, w) in DMIC_W.iter().enumerate() {
            f[off + 3 + k] = 1e4 * (lmic - self.lmic(q - w));
        }
        for (k, w) in DMID_W.iter().enumerate() {
            f[off + 8 + k] = 1e4 * (lmid - self.lmid(q - w));
        }
        f[off + 11] = 1e4 * (lmic - lmid);
        for k in 0..11 {
            let v = self.decayed(k, q);
            f[off + 12 + k] = match k {
                0..=5 => v / dep,          // ofi*, depb, depa
                6 => (v / 0.1).ln_1p(),    // lam
                _ => v,                    // up / dn intensities
            };
        }
        let (bq, aq) = if have { (self.bq, self.aq) } else { (1.0, 1.0) };
        let rb = self.decayed(4, q) / 0.1 + 1e-3 * dep;
        let ra = self.decayed(5, q) / 0.1 + 1e-3 * dep;
        let (ttd_b, ttd_a) = (plog(bq / rb + 1e-4), plog(aq / ra + 1e-4));
        f[off + 23] = ttd_b;
        f[off + 24] = ttd_a;
        f[off + 25] = ttd_b - ttd_a;
        f[off + 26] = pymin(ttd_b, ttd_a);
        match self.chg_t {
            Some(ct) => {
                f[off + 27] = pymax(q - ct, 1e-3).ln();
                f[off + 28] = self.chg_dir;
            }
            None => {
                f[off + 27] = 3.0;
                f[off + 28] = 0.0;
            }
        }
    }
}
