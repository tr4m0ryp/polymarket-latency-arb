//! btclat/paper/state/pm.py `PMBook`: the Up token's book of one 5m market as received (both
//! sides on the 0.01 grid; the Down book is its mirror), the receipt time of the last top change
//! and the mid history (10 s). Columns 0..99 = bid ticks, 100..199 = ask ticks.
use crate::state::series::Series;

/// One level change: side +1 bid / -1 ask (0 = a full book follows, merged replay groups),
/// tick 1..99, size (float32-rounded, as parsed).
pub type Chg = (i8, u8, f64);
/// (price, size) levels of one side, best first.
pub type Levels = Vec<(f64, f64)>;

#[derive(Debug, Clone)]
pub struct PmBook {
    pub size: [f64; 200],
    pub bb: i32,
    pub ba: i32,
    pub top_t: Option<f64>,
    pub mids: Series<1>,
    pub n_msgs: u64,
    pub last_ts: f64,
}

impl Default for PmBook {
    fn default() -> Self {
        PmBook { size: [0.0; 200], bb: 0, ba: 100, top_t: None, mids: Series::new(10.0), n_msgs: 0, last_ts: f64::NAN }
    }
}

impl PmBook {
    /// Apply one message; true if our view's top changed (false for the very first top).
    pub fn apply(&mut self, t: f64, ts: f64, snap: bool, chg: &[Chg]) -> bool {
        let mut new: Option<Box<[f64; 200]>> = if snap { Some(Box::new([0.0; 200])) } else { None };
        for &(side, k, s) in chg {
            if side == 0 {
                new = Some(Box::new([0.0; 200]));
                continue;
            }
            let c = if side > 0 { k as usize } else { 100 + k as usize };
            match new.as_mut() {
                Some(n) => n[c] = s,
                None => self.size[c] = s,
            }
        }
        if let Some(n) = new {
            self.size[1..200].copy_from_slice(&n[1..200]);
        }
        if !ts.is_nan() {
            self.last_ts = ts;
        }
        self.n_msgs += 1;
        let (bb, ba) = top_of(&self.size);
        if (bb, ba) != (self.bb, self.ba) || self.top_t.is_none() {
            let changed = self.top_t.is_some();
            self.bb = bb;
            self.ba = ba;
            self.top_t = Some(t);
            let m = self.mid();
            self.mids.add(t, [m]);
            return changed;
        }
        false
    }

    pub fn mid(&self) -> f64 {
        if self.bb > 0 && self.ba < 100 { (self.bb + self.ba) as f64 / 200.0 } else { f64::NAN }
    }

    pub fn mid_at(&self, q: f64) -> f64 {
        self.mids.at(0, q)
    }

    /// Levels of the token bought, best first: up = the Up asks/bids, else the Down book
    /// (Down ask at 1 - Up bid). Returns (bids, asks) as (price, size), at most n each.
    pub fn levels(&self, up: bool, n: usize) -> (Levels, Levels) {
        let (mut bids, mut asks) = (Vec::new(), Vec::new());
        let ub = (1..100).rev().filter(|&k| self.size[k] > 0.0).map(|k| (k, self.size[k]));
        let ua = (1..100).filter(|&k| self.size[100 + k] > 0.0).map(|k| (k, self.size[100 + k]));
        if up {
            bids.extend(ub.take(n).map(|(k, s)| (k as f64 / 100.0, s)));
            asks.extend(ua.take(n).map(|(k, s)| (k as f64 / 100.0, s)));
        } else {
            bids.extend(ua.take(n).map(|(k, s)| ((100 - k) as f64 / 100.0, s)));
            asks.extend(ub.take(n).map(|(k, s)| ((100 - k) as f64 / 100.0, s)));
        }
        (bids, asks)
    }

    /// Shares offered at <= `limit` (bought token terms) on the side bought.
    pub fn depth_le(&self, up: bool, limit: f64) -> f64 {
        let lim = (limit * 100.0 + 1e-6).floor() as usize;
        if up {
            (1..100).filter(|&k| k <= lim).map(|k| self.size[100 + k]).sum()
        } else {
            (1..100).filter(|&k| 100 - k <= lim).map(|k| self.size[k]).sum()
        }
    }
}

pub fn top_of(sz: &[f64; 200]) -> (i32, i32) {
    let bb = (1..100).rev().find(|&k| sz[k] > 0.0).unwrap_or(0) as i32;
    let ba = (1..100).find(|&k| sz[100 + k] > 0.0).unwrap_or(100) as i32;
    (bb, ba)
}
