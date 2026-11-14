//! The 7 book-survival inputs of the hold-aware gate, research/vetohold/label/extras.py on one
//! decision (side +1 = buy Up at the Up ask, -1 = buy Down at 1 - Up bid; s_tick = seen in cents):
//!   x_dep0      shares at the seen tick (grid book now)
//!   x_dep2/5    shares at ticks <= seen + 2 / + 5 c (float32 sum in numpy's pairwise order)
//!   x_ddep0.25  x_dep2 minus the same ladder 0.25 s earlier (and 1 s for x_ddep1.0)
//!   x_age       s since the seen level's column was last touched or a snapshot arrived (cap 60)
//!   x_rlag      mean feed lag (receipt - venue stamp) of the last 50 book rows
//! Every value is float32, as the research label files store (and the gate was trained on) it.
use crate::num::pysum::pairwise_f32;
use crate::state::PmHist;

pub const EXTRA: [&str; 7] = ["x_dep0", "x_dep2", "x_dep5", "x_ddep0.25", "x_ddep1.0", "x_age", "x_rlag"];

/// `_ladder`: depth on the bought side at ticks 1 ..= s_tick + k (bought-token cents).
fn ladder(sz: &[f32; 200], side: f64, s_tick: i64, k: i64) -> f32 {
    let lim = (s_tick + k).min(99);
    let a: [f32; 99] = std::array::from_fn(|j| {
        if (j as i64) >= lim {
            0.0
        } else if side > 0.0 {
            sz[101 + j]
        } else {
            sz[99 - j]
        }
    });
    pairwise_f32(&a)
}

/// The 7 features at receipt time t (after this event's state update).
pub fn extras(h: &mut PmHist, t: f64, side: f64, seen: f64) -> [f32; 7] {
    let s_tick = (seen * 100.0).round_ties_even() as i64;
    let col = (if side > 0.0 { 100 + s_tick } else { 100 - s_tick }).clamp(0, 199) as usize;
    let now = h.book_at(0, t);
    let (dep0, dep2, dep5) = (now[col], ladder(now, side, s_tick, 2), ladder(now, side, s_tick, 5));
    let d025 = dep2 - ladder(h.book_at(1, t), side, s_tick, 2);
    let d1 = dep2 - ladder(h.book_at(2, t), side, s_tick, 2);
    let last = h.touch[col].max(h.snap_t);
    let age = (t - last).min(60.0);
    [dep0, dep2, dep5, d025, d1, age as f32, h.rlag() as f32]
}
