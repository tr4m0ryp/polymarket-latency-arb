//! Gzip a finished hour file; the plain file is removed only after the .gz is fsynced.
use std::fs::{self, File};
use std::io::{self, BufWriter};
use std::path::{Path, PathBuf};

use flate2::{write::GzEncoder, Compression};

pub fn gz_path(plain: &Path) -> PathBuf {
    let mut s = plain.as_os_str().to_owned();
    s.push(".gz");
    PathBuf::from(s)
}

/// `X.jsonl` -> `X.jsonl.gz` (tmp file, fsync, rename, fsync dir, remove plain).
/// An empty plain file is just removed; an existing .gz is never overwritten.
pub fn compress(plain: &Path) -> io::Result<()> {
    let gz = gz_path(plain);
    if gz.exists() {
        return Err(io::Error::new(
            io::ErrorKind::AlreadyExists,
            format!("{} exists", gz.display()),
        ));
    }
    if fs::metadata(plain)?.len() == 0 {
        return fs::remove_file(plain);
    }
    let tmp = {
        let mut s = gz.as_os_str().to_owned();
        s.push(".tmp");
        PathBuf::from(s)
    };
    let mut src = File::open(plain)?;
    let mut enc = GzEncoder::new(BufWriter::new(File::create(&tmp)?), Compression::default());
    io::copy(&mut src, &mut enc)?;
    let file = enc.finish()?.into_inner().map_err(|e| e.into_error())?;
    file.sync_all()?;
    drop(file);
    fs::rename(&tmp, &gz)?;
    if let Some(dir) = gz.parent() {
        File::open(dir).and_then(|d| d.sync_all())?;
    }
    fs::remove_file(plain)
}
