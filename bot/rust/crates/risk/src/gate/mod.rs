//! Offline half of `gate/preflight.py`: approval, kill file, day lock. No network.
use std::path::{Path, PathBuf};

use thiserror::Error;

use crate::book::{lock_path, utc_day};

#[derive(Debug, Error, PartialEq)]
pub enum Refused {
    #[error("refusing: live orders need --i-approve (and the user's explicit approval)")]
    NotApproved,
    #[error("refusing: kill file {} exists (remove it to allow a start)", .0.display())]
    Killed(PathBuf),
    #[error("refusing: UTC day {day} is locked by the loss cap ({})", .path.display())]
    DayLocked { day: String, path: PathBuf },
}

/// Config dir: `$BTCLAT_CONFIG` (a leading `~` expands to `$HOME`), else `~/.config/btclat`.
pub fn config_dir() -> PathBuf {
    let raw = std::env::var("BTCLAT_CONFIG").unwrap_or_else(|_| "~/.config/btclat".into());
    let home = std::env::var("HOME").unwrap_or_default();
    match raw.strip_prefix('~') {
        Some(rest) => PathBuf::from(format!("{home}{rest}")),
        None => PathBuf::from(raw),
    }
}

pub fn kill_path(config: &Path) -> PathBuf {
    config.join("KILL")
}
pub fn state_dir(config: &Path) -> PathBuf {
    config.join("state")
}
pub fn creds_path(config: &Path) -> PathBuf {
    config.join("polymarket.env")
}

/// Cheap check for the main loop: does `<config>/KILL` exist.
pub fn killed(config: &Path) -> bool {
    kill_path(config).exists()
}

/// Approval given, no kill file, today's UTC day not locked by the loss cap.
pub fn offline_checks(approve: bool, config: &Path, now: f64) -> Result<(), Refused> {
    if !approve {
        return Err(Refused::NotApproved);
    }
    let kill = kill_path(config);
    if kill.exists() {
        return Err(Refused::Killed(kill));
    }
    let day = utc_day(now);
    let path = lock_path(&state_dir(config), &day);
    if path.exists() {
        return Err(Refused::DayLocked { day, path });
    }
    Ok(())
}
