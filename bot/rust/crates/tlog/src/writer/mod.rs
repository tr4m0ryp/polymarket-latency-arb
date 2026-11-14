//! The single writer thread: encode, buffer, rotate by wall hour, gzip finished hours.
mod gzip;
mod rotate;

use std::io::Write;
use std::path::{Path, PathBuf};
use std::sync::atomic::Ordering::Relaxed;
use std::sync::Arc;
use std::thread::JoinHandle;
use std::time::Instant;

use anyhow::Result;
use crossbeam_channel::{Receiver, RecvTimeoutError};

use crate::clock::{self, HOUR_NS};
use crate::logger::{Config, Shared};
use crate::record::{Body, Msg, Record};
use rotate::OpenFile;

pub(crate) struct Writer {
    rx: Receiver<Msg>,
    shared: Arc<Shared>,
    dir: PathBuf,
    prefix: String,
    run_json: String,
    cfg: Config,
    cur: Option<OpenFile>,
    gzips: Vec<JoinHandle<()>>,
    buf: Vec<u8>,
    io_errors: u64,
    dirty: bool,
    last_flush: Instant,
    last_stats: Instant,
}

impl Writer {
    pub fn new(
        rx: Receiver<Msg>,
        shared: Arc<Shared>,
        dir: &Path,
        prefix: &str,
        run: &str,
        cfg: Config,
    ) -> Result<Self> {
        let gzips = rotate::leftovers(dir, prefix)
            .into_iter()
            .map(spawn_gzip)
            .collect();
        Ok(Writer {
            rx,
            shared,
            dir: dir.to_path_buf(),
            prefix: prefix.to_string(),
            run_json: serde_json::to_string(run)?,
            cfg,
            cur: None,
            gzips,
            buf: Vec::with_capacity(4096),
            io_errors: 0,
            dirty: false,
            last_flush: Instant::now(),
            last_stats: Instant::now(),
        })
    }

    pub fn run(mut self) {
        let tick = self.cfg.flush_every.min(self.cfg.stats_every);
        loop {
            match self.rx.recv_timeout(tick) {
                Ok(Msg::Rec(r)) => self.write_rec(&r, true),
                Ok(Msg::Flush(ack)) => {
                    self.flush();
                    let _ = ack.send(());
                }
                Ok(Msg::Sleep(d)) => std::thread::sleep(d),
                Ok(Msg::Close) | Err(RecvTimeoutError::Disconnected) => break,
                Err(RecvTimeoutError::Timeout) => {}
            }
            if self.dirty && self.last_flush.elapsed() >= self.cfg.flush_every {
                self.flush();
            }
            if self.last_stats.elapsed() >= self.cfg.stats_every {
                self.stats();
            }
        }
        while let Ok(m) = self.rx.try_recv() {
            if let Msg::Rec(r) = m {
                self.write_rec(&r, true);
            }
        }
        self.stats();
        self.finish_file();
        for h in self.gzips.drain(..) {
            let _ = h.join();
        }
    }

    /// `rotate`: user records may move the file forward; internal lines never rotate.
    fn write_rec(&mut self, r: &Record, rotate: bool) {
        let hour = r.wall_ns / HOUR_NS;
        if rotate && self.cur.as_ref().is_some_and(|c| hour > c.hour) {
            self.finish_file();
        }
        if self.cur.is_none() {
            match rotate::open_hour(&self.dir, &self.prefix, hour) {
                Ok(f) => self.cur = Some(f),
                Err(_) => {
                    self.io_errors += 1;
                    return;
                }
            }
        }
        self.buf.clear();
        r.encode(&self.run_json, &mut self.buf);
        let cur = self.cur.as_mut().expect("file open");
        if cur.w.write_all(&self.buf).is_err() {
            self.io_errors += 1;
        }
        self.dirty = true;
        if rotate {
            self.shared.written.fetch_add(1, Relaxed);
        }
    }

    fn flush(&mut self) {
        if let Some(c) = self.cur.as_mut() {
            if c.w.flush().is_err() {
                self.io_errors += 1;
            }
        }
        self.dirty = false;
        self.last_flush = Instant::now();
    }

    fn stats(&mut self) {
        let (m, w) = clock::now();
        let body = format!(
            "\"written\":{},\"dropped\":{},\"queued\":{},\"io_errors\":{}",
            self.shared.written.load(Relaxed),
            self.shared.dropped.load(Relaxed),
            self.rx.len(),
            self.io_errors
        );
        let rec = Record {
            seq: self.shared.seq.fetch_add(1, Relaxed),
            mono_ns: m,
            wall_ns: w,
            kind: "log_stats",
            body: Body::Raw(body),
        };
        self.write_rec(&rec, false);
        self.last_stats = Instant::now();
    }

    /// Flush, close the open file and gzip it in the background.
    fn finish_file(&mut self) {
        self.flush();
        if let Some(c) = self.cur.take() {
            let OpenFile { path, w, .. } = c;
            match w.into_inner() {
                Ok(f) => {
                    let _ = f.sync_all();
                    self.gzips.push(spawn_gzip(path));
                }
                Err(_) => self.io_errors += 1,
            }
        }
    }
}

fn spawn_gzip(plain: PathBuf) -> JoinHandle<()> {
    std::thread::Builder::new()
        .name("btl-log-gzip".into())
        .spawn(move || {
            if let Err(e) = gzip::compress(&plain) {
                eprintln!(
                    "btl_log: gzip {} failed: {e} (plain file kept)",
                    plain.display()
                );
            }
        })
        .expect("spawn gzip thread")
}
