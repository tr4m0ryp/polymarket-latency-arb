//! Clocks: CLOCK_MONOTONIC for intervals, SystemTime for wall stamps (both ns).

use std::time::{SystemTime, UNIX_EPOCH};

/// Monotonic clock in ns (`clock_gettime(CLOCK_MONOTONIC)`), for latencies and idle times.
pub fn mono_ns() -> u64 {
    let mut ts = libc::timespec { tv_sec: 0, tv_nsec: 0 };
    // SAFETY: `ts` is a valid, writable timespec and CLOCK_MONOTONIC always exists on Linux.
    unsafe { libc::clock_gettime(libc::CLOCK_MONOTONIC, &mut ts) };
    ts.tv_sec as u64 * 1_000_000_000 + ts.tv_nsec as u64
}

/// Wall clock in ns since the unix epoch (0 if the host clock is before 1970).
pub fn wall_ns() -> u64 {
    SystemTime::now().duration_since(UNIX_EPOCH).map(|d| d.as_nanos() as u64).unwrap_or(0)
}

/// Wall clock in ms since the unix epoch.
pub fn wall_ms() -> u64 {
    wall_ns() / 1_000_000
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn clocks_advance() {
        let (a, b) = (mono_ns(), mono_ns());
        assert!(b >= a);
        assert!(wall_ns() > 1_700_000_000_000_000_000);
    }
}
