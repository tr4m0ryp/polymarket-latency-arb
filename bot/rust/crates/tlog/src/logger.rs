//! The caller-facing handle: cheap to clone, never blocks on I/O.
use std::path::Path;
use std::sync::atomic::{AtomicBool, AtomicU64, Ordering::Relaxed};
use std::sync::{Arc, Mutex};
use std::thread::JoinHandle;
use std::time::Duration;

use anyhow::{anyhow, Result};
use crossbeam_channel::{bounded, Sender};
use serde_json::Value;

use crate::clock;
use crate::record::{Body, Msg, Record};
use crate::writer::Writer;

/// Tunables; `Config::default()` is what the bot uses.
#[derive(Clone, Debug)]
pub struct Config {
    /// Bounded queue length; a full queue drops (and counts) instead of blocking.
    pub capacity: usize,
    /// The writer flushes its `BufWriter` at least this often while records are pending.
    pub flush_every: Duration,
    /// Period of the internal `log_stats` line.
    pub stats_every: Duration,
}

impl Default for Config {
    fn default() -> Self {
        Config {
            capacity: 65_536,
            flush_every: Duration::from_millis(200),
            stats_every: Duration::from_secs(10),
        }
    }
}

pub(crate) struct Shared {
    pub seq: AtomicU64,
    pub dropped: AtomicU64,
    pub written: AtomicU64,
    pub closed: AtomicBool,
}

struct Inner {
    tx: Sender<Msg>,
    shared: Arc<Shared>,
    run: String,
    join: Mutex<Option<JoinHandle<()>>>,
}

/// Append-only JSONL event logger. `Clone` shares one writer thread; `Send + Sync`.
#[derive(Clone)]
pub struct Logger {
    inner: Arc<Inner>,
}

impl Logger {
    /// Open (create) `dir` and start the writer with the default [`Config`].
    pub fn open(dir: &Path, run: &str, prefix: &str) -> Result<Logger> {
        Self::open_with(dir, run, prefix, Config::default())
    }

    pub fn open_with(dir: &Path, run: &str, prefix: &str, cfg: Config) -> Result<Logger> {
        std::fs::create_dir_all(dir)?;
        let (tx, rx) = bounded(cfg.capacity.max(1));
        let shared = Arc::new(Shared {
            seq: AtomicU64::new(0),
            dropped: AtomicU64::new(0),
            written: AtomicU64::new(0),
            closed: AtomicBool::new(false),
        });
        let w = Writer::new(rx, shared.clone(), dir, prefix, run, cfg)?;
        let join = std::thread::Builder::new()
            .name("btl-log-writer".into())
            .spawn(move || w.run())?;
        let inner = Inner {
            tx,
            shared,
            run: run.to_string(),
            join: Mutex::new(Some(join)),
        };
        Ok(Logger {
            inner: Arc::new(inner),
        })
    }

    /// Log with timestamps taken now. `body` should be a JSON object; its fields are flattened
    /// into the line (non-objects are written under `"value"`).
    #[inline]
    pub fn log(&self, kind: &'static str, body: Value) {
        let (m, w) = clock::now();
        self.log_at(kind, m, w, body)
    }

    /// Log with caller-supplied timestamps (e.g. receipt time captured at the socket read).
    #[inline]
    pub fn log_at(&self, kind: &'static str, mono_ns: u64, wall_ns: u64, body: Value) {
        self.push(kind, mono_ns, wall_ns, Body::Value(body));
    }

    /// Fastest path: `json_fields` is the already-serialized field list without braces
    /// (`"a":1,"b":"x"`); the caller must not use the keys run/seq/mono_ns/wall_ns/kind.
    #[inline]
    pub fn log_raw(&self, kind: &'static str, mono_ns: u64, wall_ns: u64, json_fields: String) {
        self.push(kind, mono_ns, wall_ns, Body::Raw(json_fields));
    }

    #[inline]
    fn push(&self, kind: &'static str, mono_ns: u64, wall_ns: u64, body: Body) {
        let s = &self.inner.shared;
        let seq = s.seq.fetch_add(1, Relaxed);
        if s.closed.load(Relaxed) {
            s.dropped.fetch_add(1, Relaxed);
            return;
        }
        let rec = Record {
            seq,
            mono_ns,
            wall_ns,
            kind,
            body,
        };
        if self.inner.tx.try_send(Msg::Rec(rec)).is_err() {
            s.dropped.fetch_add(1, Relaxed);
        }
    }

    /// Records dropped so far (queue full or logger closed).
    pub fn dropped(&self) -> u64 {
        self.inner.shared.dropped.load(Relaxed)
    }

    /// Records the writer has written so far (excluding internal `log_stats` lines).
    pub fn written(&self) -> u64 {
        self.inner.shared.written.load(Relaxed)
    }

    pub fn run(&self) -> &str {
        &self.inner.run
    }

    /// Block until everything queued before this call is written and flushed to the OS.
    pub fn flush(&self) {
        let (ack_tx, ack_rx) = bounded(1);
        if self.inner.tx.send(Msg::Flush(ack_tx)).is_ok() {
            let _ = ack_rx.recv();
        }
    }

    #[doc(hidden)]
    pub fn stall_writer(&self, d: Duration) {
        let _ = self.inner.tx.send(Msg::Sleep(d));
    }

    /// Drain, flush, gzip every file, join the threads. Other clones then drop (and count) records.
    pub fn close(self) -> Result<()> {
        self.inner.shutdown()
    }
}

impl Inner {
    fn shutdown(&self) -> Result<()> {
        self.shared.closed.store(true, Relaxed);
        let h = self
            .join
            .lock()
            .map_err(|_| anyhow!("log mutex poisoned"))?
            .take();
        if let Some(h) = h {
            let _ = self.tx.send(Msg::Close);
            h.join()
                .map_err(|_| anyhow!("log writer thread panicked"))?;
        }
        Ok(())
    }
}

impl Drop for Inner {
    fn drop(&mut self) {
        let _ = self.shutdown();
    }
}
