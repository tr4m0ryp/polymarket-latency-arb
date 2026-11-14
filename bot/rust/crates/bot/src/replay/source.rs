//! Recorded hours (a paper run's raw/ dir or data/live: `<day>/<stream>-<hour>.tsv.gz`, lines
//! `<recv_ns>\t<raw>`) as one time-ordered event stream, like btclat/paper/replay/source.py
//! (quantize=False): markets first at their subscribe time, then spot, perp and CLOB events
//! merged by receipt time, ties in that source order. Each stream is read and parsed on its own
//! thread.
use anyhow::Result;
use crossbeam_channel::{bounded, Receiver};
use flate2::read::MultiGzDecoder;
use std::collections::{HashMap, HashSet};
use std::io::{BufRead, BufReader};
use std::path::{Path, PathBuf};

use btl_signal::feed::{binance, clob, Ev};
use btl_signal::MarketMeta;

pub fn files(root: &Path, stream: &str, hours: &[i64]) -> Vec<PathBuf> {
    let mut out = Vec::new();
    for h in hours {
        let mut v: Vec<PathBuf> = std::fs::read_dir(root).into_iter().flatten().filter_map(|e| e.ok())
            .map(|e| e.path().join(format!("{stream}-{h}.tsv.gz"))).filter(|p| p.exists()).collect();
        v.sort();
        out.extend(v);
    }
    out
}

/// Every (t seconds, raw) line of a stream; a truncated gzip ends its file quietly.
pub fn lines(root: &Path, stream: &str, hours: &[i64], mut f: impl FnMut(f64, &str) -> bool) {
    for p in files(root, stream, hours) {
        let Ok(fh) = std::fs::File::open(&p) else { continue };
        let mut rd = BufReader::with_capacity(1 << 20, MultiGzDecoder::new(fh));
        let mut line = String::new();
        loop {
            line.clear();
            match rd.read_line(&mut line) {
                Ok(0) | Err(_) => break,
                Ok(_) => {}
            }
            let l = line.trim_end_matches('\n');
            let Some((t, raw)) = l.split_once('\t') else { continue };
            if raw.is_empty() {
                continue;
            }
            let Ok(ns) = t.parse::<i64>() else { continue };
            if !f(ns as f64 / 1e9, raw) {
                return;
            }
        }
    }
}

/// 5m markets of the hours: slug -> (first seen t, meta), in first-seen order.
pub fn markets(root: &Path, hours: &[i64]) -> Vec<(f64, MarketMeta)> {
    let mut out: Vec<(f64, MarketMeta)> = Vec::new();
    lines(root, "markets", hours, |t, raw| {
        if let Ok(m) = serde_json::from_str::<MarketMeta>(raw) {
            if m.fam == "5m" && !out.iter().any(|x| x.1.slug == m.slug) {
                out.push((t, m));
            }
        }
        true
    });
    out
}

fn spawn_binance(root: PathBuf, hours: Vec<i64>, perp: bool) -> Receiver<Vec<Ev>> {
    let (tx, rx) = bounded(64);
    std::thread::spawn(move || {
        let mut seen: HashSet<binance::Key> = HashSet::new();
        let mut buf = Vec::with_capacity(4096);
        lines(&root, if perp { "binance_fut" } else { "binance" }, &hours, |t, raw| {
            if let Some((ev, key)) = binance::parse(t, raw, perp) {
                if seen.insert(key) {
                    if seen.len() > 200_000 {
                        seen.clear();
                    }
                    buf.push(ev);
                }
            }
            if buf.len() >= 4096 {
                return tx.send(std::mem::take(&mut buf)).is_ok();
            }
            true
        });
        let _ = tx.send(buf);
    });
    rx
}

fn spawn_clob(root: PathBuf, hours: Vec<i64>, ups: HashMap<String, i64>) -> Receiver<Vec<Ev>> {
    let (tx, rx) = bounded(64);
    std::thread::spawn(move || {
        let mut buf = Vec::with_capacity(4096);
        lines(&root, "clob_5m", &hours, |t, raw| {
            buf.extend(clob::parse(t, raw, &ups));
            if buf.len() >= 4096 {
                return tx.send(std::mem::take(&mut buf)).is_ok();
            }
            true
        });
        let _ = tx.send(buf);
    });
    rx
}

/// Pull-based cursor over one source's batches.
struct Src {
    rx: Option<Receiver<Vec<Ev>>>,
    buf: std::vec::IntoIter<Ev>,
    head: Option<Ev>,
}

impl Src {
    fn new(rx: Option<Receiver<Vec<Ev>>>, first: Vec<Ev>) -> Src {
        let mut s = Src { rx, buf: first.into_iter(), head: None };
        s.advance();
        s
    }

    fn advance(&mut self) {
        loop {
            if let Some(e) = self.buf.next() {
                self.head = Some(e);
                return;
            }
            match self.rx.as_ref().and_then(|r| r.recv().ok()) {
                Some(v) => self.buf = v.into_iter(),
                None => {
                    self.head = None;
                    return;
                }
            }
        }
    }
}

/// The merged stream, handed to `f` event by event (stable k-way merge on t, like heapq.merge).
pub fn replay(root: &Path, hours: &[i64], mut f: impl FnMut(&Ev)) -> Result<usize> {
    let mk = markets(root, hours);
    let ups: HashMap<String, i64> = mk.iter().map(|(_, m)| (m.up.clone(), m.start)).collect();
    let mut rows: Vec<Ev> = mk.into_iter().map(|(t, m)| Ev::Mk(Box::new((t, m)))).collect();
    rows.sort_by(|a, b| a.t().total_cmp(&b.t()));
    let mut srcs = [
        Src::new(None, rows),
        Src::new(Some(spawn_binance(root.into(), hours.to_vec(), false)), vec![]),
        Src::new(Some(spawn_binance(root.into(), hours.to_vec(), true)), vec![]),
        Src::new(Some(spawn_clob(root.into(), hours.to_vec(), ups)), vec![]),
    ];
    let mut n = 0;
    loop {
        let mut best: Option<(usize, f64)> = None;
        for (i, s) in srcs.iter().enumerate() {
            if let Some(e) = &s.head {
                let t = e.t();
                if best.is_none_or(|(_, bt)| t < bt) {
                    best = Some((i, t));
                }
            }
        }
        let Some((i, _)) = best else { break };
        let ev = srcs[i].head.take().unwrap();
        f(&ev);
        n += 1;
        srcs[i].advance();
    }
    Ok(n)
}
