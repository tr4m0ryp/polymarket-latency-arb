//! Numerics that reproduce the Python reference bit for bit on the research host: scipy's cephes
//! `ndtr` / `ndtri`, numpy's pairwise summation, CPython's `bisect_right`, `round(x, 3)` and the
//! NaN behaviour of the builtins `max` / `min` (`max(nan, 1)` is nan, `max(1, nan)` is 1).
pub mod cephes;
pub mod pysum;

/// Python `max(a, b)`: a unless b > a.
#[inline]
pub fn pymax(a: f64, b: f64) -> f64 {
    if b > a { b } else { a }
}

/// Python `min(a, b)`: a unless b < a.
#[inline]
pub fn pymin(a: f64, b: f64) -> f64 {
    if b < a { b } else { a }
}

/// Round to float32 and back (numpy float32 storage, struct.pack("f")).
#[inline]
pub fn f32r(x: f64) -> f64 {
    x as f32 as f64
}

/// CPython `bisect.bisect_right(a, x, lo)`: the same probe sequence, so results agree even on a
/// list that is not perfectly sorted (spot trades keyed by trade time, in arrival order).
#[inline]
pub fn bisect_right(a: &[f64], x: f64, lo: usize) -> usize {
    let (mut lo, mut hi) = (lo, a.len());
    while lo < hi {
        let mid = (lo + hi) / 2;
        if x < a[mid] { hi = mid } else { lo = mid + 1 }
    }
    lo
}

/// Python `round(x, 3)`: the double nearest to x correctly rounded to 3 decimals (half-even on
/// the exact binary value); Rust's `{:.3}` formatting rounds the exact value the same way.
pub fn pyround3(x: f64) -> f64 {
    if !x.is_finite() {
        return x;
    }
    format!("{x:.3}").parse().unwrap_or(x)
}

/// numpy `np.sign` on a float: -1, 0, +1, NaN for NaN.
#[inline]
pub fn npsign(x: f64) -> f64 {
    if x > 0.0 { 1.0 } else if x < 0.0 { -1.0 } else if x == 0.0 { 0.0 } else { f64::NAN }
}

/// Length of `np.arange(a, b, step)` for float arguments (ceil((b - a) / step), floored at 0).
#[inline]
pub fn arange_len(a: f64, b: f64, step: f64) -> usize {
    let n = ((b - a) / step).ceil();
    if n > 0.0 { n as usize } else { 0 }
}

/// i-th element of `np.arange(a, b, step)`: numpy fills start + i * ((start + step) - start).
#[inline]
pub fn arange_at(a: f64, step: f64, i: usize) -> f64 {
    if i == 0 { a } else if i == 1 { a + step } else { a + (i as f64) * ((a + step) - a) }
}
