//! btclat/paper/state/series.py `Series`: append-only columns with an as-of lookup and the same
//! trimming schedule (every 256 appends; physical deletion when lo > 4096 and lo * 2 > len), so
//! lookups that reach the cut-off resolve exactly as in Python.
use crate::num::bisect_right;

#[derive(Debug, Clone)]
pub struct Series<const C: usize> {
    pub t: Vec<f64>,
    pub cols: [Vec<f64>; C],
    pub lo: usize,
    keep: f64,
}

impl<const C: usize> Series<C> {
    pub fn new(keep: f64) -> Self {
        Series { t: Vec::new(), cols: std::array::from_fn(|_| Vec::new()), lo: 0, keep }
    }

    pub fn add(&mut self, t: f64, vals: [f64; C]) {
        self.t.push(t);
        for (c, v) in self.cols.iter_mut().zip(vals) {
            c.push(v);
        }
        if self.t.len() & 255 == 0 {
            self.trim();
        }
    }

    fn trim(&mut self) {
        let cut = self.t[self.t.len() - 1] - self.keep;
        let i = bisect_right(&self.t, cut, self.lo) as isize - 1;
        if i > self.lo as isize {
            self.lo = i as usize;
        }
        if self.lo > 4096 && self.lo * 2 > self.t.len() {
            let lo = self.lo;
            self.t.drain(..lo);
            for c in self.cols.iter_mut() {
                c.drain(..lo);
            }
            self.lo = 0;
        }
    }

    pub fn len(&self) -> usize {
        self.t.len() - self.lo
    }

    pub fn is_empty(&self) -> bool {
        self.len() == 0
    }

    /// Index of the last element with t <= q, or None.
    #[inline]
    pub fn asof(&self, q: f64) -> Option<usize> {
        let i = bisect_right(&self.t, q, self.lo);
        if i > self.lo { Some(i - 1) } else { None }
    }

    #[inline]
    pub fn at(&self, col: usize, q: f64) -> f64 {
        match self.asof(q) {
            Some(i) => self.cols[col][i],
            None => f64::NAN,
        }
    }
}
