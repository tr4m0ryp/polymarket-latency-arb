//! File naming and the open-file state for hourly rotation.
use std::fs::{self, File, OpenOptions};
use std::io::{self, BufWriter};
use std::path::{Path, PathBuf};

use super::gzip::gz_path;

pub struct OpenFile {
    pub hour: u64,
    pub path: PathBuf,
    pub w: BufWriter<File>,
}

/// First unused `<prefix>-<hour>.jsonl`, then `<prefix>-<hour>.<n>.jsonl`: a name is used if
/// either the plain file or its .gz exists, so an earlier process's output is never reopened.
pub fn pick_path(dir: &Path, prefix: &str, hour: u64) -> PathBuf {
    let used = |p: &Path| p.exists() || gz_path(p).exists();
    let base = dir.join(format!("{prefix}-{hour}.jsonl"));
    if !used(&base) {
        return base;
    }
    (1u32..)
        .map(|n| dir.join(format!("{prefix}-{hour}.{n}.jsonl")))
        .find(|p| !used(p))
        .expect("unbounded range")
}

pub fn open_hour(dir: &Path, prefix: &str, hour: u64) -> io::Result<OpenFile> {
    let path = pick_path(dir, prefix, hour);
    let f = OpenOptions::new()
        .create_new(true)
        .append(true)
        .open(&path)?;
    Ok(OpenFile {
        hour,
        path,
        w: BufWriter::with_capacity(64 * 1024, f),
    })
}

/// Plain `<prefix>-*.jsonl` files without a .gz (left by a crashed process).
pub fn leftovers(dir: &Path, prefix: &str) -> Vec<PathBuf> {
    let Ok(rd) = fs::read_dir(dir) else {
        return vec![];
    };
    let pre = format!("{prefix}-");
    rd.filter_map(|e| e.ok().map(|e| e.path()))
        .filter(|p| {
            let n = p.file_name().and_then(|n| n.to_str()).unwrap_or("");
            n.starts_with(&pre) && n.ends_with(".jsonl") && !gz_path(p).exists()
        })
        .collect()
}
