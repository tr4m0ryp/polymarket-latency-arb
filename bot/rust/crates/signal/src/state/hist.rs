//! Book-survival state of one market's Up book (research/vetohold/label/extras.py inputs), kept
//! from the same Polymarket messages as `PmBook`, no look-ahead:
//! - the book as research's 5 ms grid holds it (research/strategy/sim/grid.py `_replay` on the
//!   receipt clock): row g = every message with ceil((t - t0) / DT - 1e-9) <= g applied in order,
//!   t0 = start - 2; read at floor((q - t0) / DT + 1e-9) for q = t, t - 0.25, t - 1. One lagged
//!   copy per offset, advanced eagerly (future queries never read an earlier row);
//! - per column the receipt time of the last message row touching it, and of the last snapshot;
//! - the running cumulative sum of the feed lag (receipt - venue stamp, NaN -> 0) per book row,
//!   numpy `cumsum` order, with the last 51 partial sums for the mean over the last 50 rows.
use std::collections::VecDeque;

use crate::state::pm::Chg;

pub const DT: f64 = 0.005;
/// read offsets (s) of the lagged grid books: now, 0.25 s, 1 s
pub const LAGS: [f64; 3] = [0.0, 0.25, 1.0];
const CLEAR: u8 = 255;

#[derive(Debug, Clone)]
struct Lagged {
    size: [f32; 200],
    /// absolute index of the next queue entry to apply
    next: u64,
}

#[derive(Debug, Clone)]
pub struct PmHist {
    t0: f64,
    n: i64,
    /// (grid row, column or CLEAR, size), message order
    q: VecDeque<(i64, u8, f32)>,
    base: u64,
    lag: [Lagged; 3],
    pub touch: [f64; 200],
    pub snap_t: f64,
    cs: VecDeque<f64>,
}

impl PmHist {
    pub fn new(start: f64, end: f64) -> PmHist {
        let (t0, t1) = (start - 2.0, end + 2.0);
        let n = ((t1 - t0) / DT).ceil() as i64 + 1;
        let l = Lagged { size: [0.0; 200], next: 0 };
        PmHist { t0, n, q: VecDeque::new(), base: 0, lag: [l.clone(), l.clone(), l], touch: [f64::NEG_INFINITY; 200],
            snap_t: f64::NEG_INFINITY, cs: VecDeque::from([0.0]) }
    }

    /// Row holding what was known by q (`Book.g_floor`, extras `g`).
    #[inline]
    pub fn g_floor(&self, q: f64) -> i64 {
        (((q - self.t0) / DT + 1e-9).floor() as i64).clamp(0, self.n - 1)
    }

    /// Row a message received at t first shows in (`_replay`).
    #[inline]
    fn g_ceil(&self, t: f64) -> i64 {
        (((t - self.t0) / DT - 1e-9).ceil() as i64).clamp(0, self.n - 1)
    }

    /// One message, after `PmBook::apply`: t receipt, ts venue stamp (s).
    pub fn on_msg(&mut self, t: f64, ts: f64, snap: bool, chg: &[Chg]) {
        let g = self.g_ceil(t);
        let lag = if (t - ts).is_finite() { t - ts } else { 0.0 };
        let row = |h: &mut PmHist| {
            let c = *h.cs.back().unwrap() + lag;
            h.cs.push_back(c);
            if h.cs.len() > 51 {
                h.cs.pop_front();
            }
        };
        if snap {
            self.q.push_back((g, CLEAR, 0.0));
            self.snap_t = t;
            row(self);
        }
        for &(side, k, s) in chg {
            if side == 0 {
                self.q.push_back((g, CLEAR, 0.0));
                self.snap_t = t;
            } else {
                let c = if side > 0 { k as usize } else { 100 + k as usize };
                self.q.push_back((g, c as u8, s as f32));
                self.touch[c] = t;
            }
            row(self);
        }
        for (i, w) in LAGS.iter().enumerate() {
            self.advance(i, self.g_floor(t - w));
        }
    }

    fn advance(&mut self, i: usize, g: i64) {
        let l = &mut self.lag[i];
        while let Some(&(eg, c, s)) = self.q.get((l.next - self.base) as usize) {
            if eg > g {
                break;
            }
            if c == CLEAR {
                l.size = [0.0; 200];
            } else {
                l.size[c as usize] = s;
            }
            l.next += 1;
        }
        let done = self.lag.iter().map(|l| l.next).min().unwrap_or(0);
        while self.base < done {
            self.q.pop_front();
            self.base += 1;
        }
    }

    /// The grid book read at q - LAGS[i] (q >= every earlier query and message time).
    pub fn book_at(&mut self, i: usize, q: f64) -> &[f32; 200] {
        let g = self.g_floor(q - LAGS[i]);
        self.advance(i, g);
        &self.lag[i].size
    }

    /// Mean feed lag over the last 50 book rows (0 before any row).
    pub fn rlag(&self) -> f64 {
        let (e, s) = (*self.cs.back().unwrap(), *self.cs.front().unwrap());
        (e - s) / ((self.cs.len() - 1).max(1) as f64)
    }
}
