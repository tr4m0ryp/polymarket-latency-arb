//! Timestamps: CLOCK_MONOTONIC and wall clock, both in integer nanoseconds.
use std::time::{SystemTime, UNIX_EPOCH};

/// Nanoseconds in one epoch hour (`HOUR = wall_ns / HOUR_NS`).
pub const HOUR_NS: u64 = 3_600_000_000_000;

/// CLOCK_MONOTONIC in ns (vDSO call, no syscall).
#[inline]
pub fn mono_ns() -> u64 {
    let mut ts = libc::timespec {
        tv_sec: 0,
        tv_nsec: 0,
    };
    // SAFETY: ts is a valid out-pointer; CLOCK_MONOTONIC always exists on Linux.
    unsafe { libc::clock_gettime(libc::CLOCK_MONOTONIC, &mut ts) };
    ts.tv_sec as u64 * 1_000_000_000 + ts.tv_nsec as u64
}

/// Unix wall clock in ns.
#[inline]
pub fn wall_ns() -> u64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|d| d.as_nanos() as u64)
        .unwrap_or(0)
}

/// `(mono_ns, wall_ns)` captured back to back.
#[inline]
pub fn now() -> (u64, u64) {
    (mono_ns(), wall_ns())
}
