//! btclat/paper/state/book.py `BookState`: one Binance bookTicker stream, decayed sums per
//! message, a 30 s depth EWMA and the log mid / log microprice history (330 s).
use crate::num::{pymax, pymin};
use crate::state::series::Series;

pub const LMID: usize = 0;
pub const LMIC: usize = 1;
/// decayed sums: (name, tau); order fixes the feature order
pub const SUMS: [(&str, f64); 11] = [("ofi0.025", 0.025), ("ofi0.1", 0.1), ("ofi0.4", 0.4), ("ofi1.6", 1.6),
    ("depb", 0.1), ("depa", 0.1), ("lam", 0.1), ("up0.4", 0.4), ("dn0.4", 0.4), ("up2", 2.0), ("dn2", 2.0)];
const TAUS: [f64; 5] = [0.025, 0.1, 0.4, 1.6, 2.0];

#[derive(Debug, Clone)]
pub struct BookState {
    pub tick: f64,
    pub t: Option<f64>,
    pub b: f64,
    pub a: f64,
    pub bq: f64,
    pub aq: f64,
    pub mid: f64,
    pub imb: f64,
    pub spr: f64,
    pub lq: f64,
    pub s: [f64; 11],
    num: f64,
    den: f64,
    pub depth: f64,
    pub hist: Series<2>,
    pub chg_t: Option<f64>,
    pub chg_dir: f64,
    pub mid_changed: bool,
}

fn tau_idx(tau: f64) -> usize {
    TAUS.iter().position(|&x| x == tau).expect("tau")
}

impl BookState {
    pub fn new(tick: f64) -> Self {
        let n = f64::NAN;
        BookState { tick, t: None, b: n, a: n, bq: n, aq: n, mid: n, imb: n, spr: n, lq: n, s: [0.0; 11],
            num: 0.0, den: 0.0, depth: n, hist: Series::new(330.0), chg_t: None, chg_dir: 0.0, mid_changed: false }
    }

    pub fn update(&mut self, t: f64, b: f64, a: f64, bq: f64, aq: f64) {
        let mid = (b + a) / 2.0;
        let q = bq + aq;
        let x_dep = q / 2.0;
        let (e, dep_b, dep_a, dm);
        match self.t {
            None => {
                e = 0.0;
                dep_b = 0.0;
                dep_a = 0.0;
                dm = 0.0;
                self.num = x_dep;
                self.den = 1.0;
                self.s = [0.0; 11];
            }
            Some(t0) => {
                let dt = t - t0;
                let (pb, pa, pbq, paq) = (self.b, self.a, self.bq, self.aq);
                let bit = |c: bool| if c { 1.0 } else { 0.0 };
                e = bit(b >= pb) * bq - bit(b <= pb) * pbq - bit(a <= pa) * aq + bit(a >= pa) * paq;
                dep_b = if b == pb { pymax(pbq - bq, 0.0) } else if b < pb { pbq } else { 0.0 };
                dep_a = if a == pa { pymax(paq - aq, 0.0) } else if a > pa { paq } else { 0.0 };
                dm = mid - self.mid;
                let d30 = (-dt / 30.0).exp();
                self.num = self.num * d30 + x_dep;
                self.den = self.den * d30 + 1.0;
                let dec: [f64; 5] = std::array::from_fn(|k| (-dt / TAUS[k]).exp());
                for (k, (_, tau)) in SUMS.iter().enumerate() {
                    self.s[k] *= dec[tau_idx(*tau)];
                }
            }
        }
        let up = if dm > 0.0 { 1.0 } else { 0.0 };
        let dn = if dm < 0.0 { 1.0 } else { 0.0 };
        for (k, x) in [e, e, e, e, dep_b, dep_a, 1.0, up, dn, up, dn].into_iter().enumerate() {
            self.s[k] += x;
        }
        self.depth = self.num / pymax(self.den, 1e-12);
        if dm != 0.0 {
            self.chg_t = Some(t);
            self.chg_dir = if dm > 0.0 { 1.0 } else { -1.0 };
        }
        self.mid_changed = dm != 0.0;
        let lmid = mid.ln();
        let lmic = if q > 0.0 { ((b * aq + a * bq) / q).ln() } else { lmid };
        self.imb = if q > 0.0 { (bq - aq) / q } else { 0.0 };
        self.spr = pymin(pymax(((a - b) / self.tick).round_ties_even(), 0.0), 50.0);
        self.lq = q.ln_1p();
        self.t = Some(t);
        (self.b, self.a, self.bq, self.aq, self.mid) = (b, a, bq, aq, mid);
        self.hist.add(t, [lmid, lmic]);
    }

    #[inline]
    pub fn lmic(&self, q: f64) -> f64 {
        self.hist.at(LMIC, q)
    }

    #[inline]
    pub fn lmid(&self, q: f64) -> f64 {
        self.hist.at(LMID, q)
    }

    #[inline]
    pub fn decayed(&self, k: usize, q: f64) -> f64 {
        match self.t {
            Some(t) => self.s[k] * (-(q - t) / SUMS[k].1).exp(),
            None => 0.0,
        }
    }
}
