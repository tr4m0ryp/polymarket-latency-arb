//! Settlement inputs (btclat/paper/state/spot.py `Settle`, `LockedTwap`, `p_model`): spot trade
//! log prices on the trade clock T (as received, so the list may be slightly unsorted; lookups
//! use CPython's bisect), the 60 s TWAP strike, sigma of 1 s log returns over 300 s, zscale.
use crate::num::cephes::ndtr;
use crate::num::{arange_at, arange_len, bisect_right, pymax, pymin, pysum};
use crate::state::series::Series;

const SIG_FLOOR: f64 = 0.03e-4;

#[derive(Debug, Clone)]
pub struct Settle {
    pub tt: Series<1>,
    pub last_lpx: f64,
    pub last_t: Option<f64>,
    pub prev_lpx: f64,
    sig: Vec<(i64, f64)>,
}

impl Default for Settle {
    fn default() -> Self {
        Settle { tt: Series::new(700.0), last_lpx: f64::NAN, last_t: None, prev_lpx: f64::NAN, sig: Vec::new() }
    }
}

impl Settle {
    pub fn update(&mut self, t: f64, tt: f64, px: f64) {
        let lpx = px.ln();
        self.prev_lpx = self.last_lpx;
        self.last_lpx = lpx;
        self.last_t = Some(t);
        self.tt.add(tt, [lpx]);
        if let Some(mx) = self.sig.iter().map(|x| x.0).max() {
            if tt <= mx as f64 {
                self.sig.clear(); // a late trade inside a cached window
            }
        }
    }

    pub fn first_t(&self) -> f64 {
        if self.tt.is_empty() { f64::INFINITY } else { self.tt.t[self.tt.lo] }
    }

    #[inline]
    pub fn at_t(&self, g: f64) -> f64 {
        let lo = self.tt.lo;
        let i = bisect_right(&self.tt.t, g, lo) as isize - 1;
        self.tt.cols[0][pymax(i as f64, lo as f64) as usize]
    }

    pub fn twap(&self, a: f64, b: f64) -> f64 {
        if self.tt.is_empty() || self.first_t() > a + 5.0 {
            return f64::NAN;
        }
        let n = arange_len(a, b, 0.25);
        if n == 0 {
            return f64::NAN;
        }
        let v: Vec<f64> = (0..n).map(|i| self.at_t(arange_at(a, 0.25, i)).exp()).collect();
        pysum::mean(&v)
    }

    pub fn sigma(&mut self, q: f64) -> f64 {
        let g = q.floor() as i64;
        if let Some(&(_, s)) = self.sig.iter().find(|x| x.0 == g) {
            return s;
        }
        let lv: Vec<f64> = (g - 300..=g).map(|x| self.at_t(x as f64)).collect();
        let r: Vec<f64> = lv.windows(2).map(|w| w[1] - w[0]).collect();
        let r2: Vec<f64> = r.iter().map(|x| x * x).collect();
        let m = pysum::pairwise(&r) / 300.0;
        let var = pysum::pairwise(&r2) / 300.0 - m * m;
        let s = pymax(var, SIG_FLOOR * SIG_FLOOR).sqrt();
        if self.sig.len() > 8 {
            self.sig.clear();
        }
        self.sig.push((g, s));
        s
    }

    pub fn zscale(&mut self, q: f64, end: f64) -> f64 {
        let tau = pymax(end - q, 3.0);
        let eff = if tau >= 60.0 { tau - 40.0 } else { tau / 3.0 };
        1.0 / (self.sigma(q) * eff.sqrt())
    }
}

/// Per-market cache of the last-minute TWAP points end - 60 + 0.25 k (>= 2 s old are final).
#[derive(Debug, Clone)]
pub struct LockedTwap {
    end: f64,
    pts: Vec<f64>,
}

impl LockedTwap {
    pub fn new(end: f64) -> Self {
        LockedTwap { end, pts: Vec::new() }
    }

    /// Fix the points that are >= 2 s old at q (the cache fill `value` does first). The Python
    /// bot fills it on every value candidate of the last minute; the Rust engine calls this on
    /// the same candidates even when it skips the row, so the cached points are the same.
    pub fn advance(&mut self, st: &Settle, q: f64, n: usize) -> usize {
        let a = self.end - 60.0;
        let settled = pymax(0.0, pymin(n as f64, ((q - 2.0 - a) / 0.25).trunc())) as usize;
        while self.pts.len() < settled {
            let g = arange_at(a, 0.25, self.pts.len());
            self.pts.push(st.at_t(g).exp());
        }
        settled
    }

    pub fn n_at(&self, q: f64) -> usize {
        arange_len(self.end - 60.0, q, 0.25)
    }

    pub fn value(&mut self, st: &Settle, q: f64) -> f64 {
        let a = self.end - 60.0;
        let n = arange_len(a, q, 0.25);
        if n == 0 {
            return f64::NAN;
        }
        let settled = self.advance(st, q, n);
        let mut vals: Vec<f64> = self.pts[..settled].to_vec();
        vals.extend((settled..n).map(|i| st.at_t(arange_at(a, 0.25, i)).exp()));
        pysum::mean(&vals)
    }
}

/// Level fair P(Up) from the TWAP rule with the last spot trade (Feeds.p_model).
pub fn p_model(st: &mut Settle, q: f64, end: f64, k: f64, lock: &mut LockedTwap) -> f64 {
    let tau = pymax(end - q, 3.0);
    let s = st.last_lpx.exp();
    let w = pymin(pymax(tau / 60.0, 0.0), 1.0);
    let zs = st.zscale(q, end);
    let z = if tau < 60.0 {
        let locked = if q > end - 60.0 { lock.value(st, q) } else { f64::NAN };
        let exp_close = (1.0 - w) * (if locked.is_nan() { 0.0 } else { locked }) + w * s;
        (exp_close / k).ln() * zs / w
    } else {
        (s / k).ln() * zs
    };
    ndtr(z)
}
