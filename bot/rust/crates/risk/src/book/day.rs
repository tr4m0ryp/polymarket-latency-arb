//! UTC day arithmetic and the day lock path.
use std::path::{Path, PathBuf};

/// `YYYY-MM-DD` of a unix time (UTC), like `time.strftime("%Y-%m-%d", time.gmtime(t))`.
pub fn utc_day(t: f64) -> String {
    let days = (t / 86400.0).floor() as i64;
    // Howard Hinnant's civil_from_days.
    let z = days + 719_468;
    let era = z.div_euclid(146_097);
    let doe = z.rem_euclid(146_097);
    let yoe = (doe - doe / 1460 + doe / 36_524 - doe / 146_096) / 365;
    let y = yoe + era * 400;
    let doy = doe - (365 * yoe + yoe / 4 - yoe / 100);
    let mp = (5 * doy + 2) / 153;
    let d = doy - (153 * mp + 2) / 5 + 1;
    let m = if mp < 10 { mp + 3 } else { mp - 9 };
    let y = if m <= 2 { y + 1 } else { y };
    format!("{y:04}-{m:02}-{d:02}")
}

pub fn lock_path(state: &Path, day: &str) -> PathBuf {
    state.join(format!("lock-{day}"))
}

pub(crate) fn ledger_path(state: &Path, day: &str) -> PathBuf {
    state.join(format!("ledger-{day}.jsonl"))
}

pub(crate) fn unix_now() -> f64 {
    std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .map(|d| d.as_secs_f64())
        .unwrap_or(0.0)
}
