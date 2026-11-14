use std::fs;
use std::io::Read;
use std::path::{Path, PathBuf};
use std::time::{Duration, Instant};

use btl_log::{Config, Logger, HOUR_NS};
use flate2::read::GzDecoder;
use serde_json::{json, Value};

fn tmpdir(name: &str) -> PathBuf {
    let d = std::env::temp_dir().join(format!("btl_log_{name}_{}", std::process::id()));
    let _ = fs::remove_dir_all(&d);
    d
}

fn names(dir: &Path) -> Vec<String> {
    let mut v: Vec<String> = fs::read_dir(dir)
        .unwrap()
        .map(|e| e.unwrap().file_name().into_string().unwrap())
        .collect();
    v.sort();
    v
}

fn read_all(dir: &Path) -> Vec<Value> {
    let mut out = vec![];
    for n in names(dir) {
        let mut s = String::new();
        let p = dir.join(&n);
        if n.ends_with(".gz") {
            GzDecoder::new(fs::File::open(p).unwrap())
                .read_to_string(&mut s)
                .unwrap();
        } else {
            s = fs::read_to_string(p).unwrap();
        }
        out.extend(
            s.lines()
                .map(|l| serde_json::from_str::<Value>(l).expect("valid json line")),
        );
    }
    out
}

fn user(v: &[Value]) -> Vec<&Value> {
    v.iter().filter(|r| r["kind"] != "log_stats").collect()
}

#[test]
fn round_trip() {
    let d = tmpdir("rt");
    let lg = Logger::open(&d, "r1", "bot").unwrap();
    for i in 0..1000u64 {
        match i % 3 {
            0 => lg.log("signal", json!({"sig": format!("r1:{i}"), "features": {"a": 0.5, "b": null}, "arr": [[0.5, 10.0]]})),
            1 => lg.log_at("send", 111 + i, 1_700_000_000_000_000_000 + i, json!({"cid": "r1:1", "copy": i})),
            _ => lg.log_raw("feed", 5, 1_700_000_000_000_000_000, format!("\"src\":\"pb\",\"b\":{}.25", i)),
        }
    }
    lg.close().unwrap();
    assert_eq!(names(&d).len(), 1);
    assert!(names(&d)[0].ends_with(".jsonl.gz"));
    let all = read_all(&d);
    let u = user(&all);
    assert_eq!(u.len(), 1000);
    assert!(u
        .windows(2)
        .all(|w| w[0]["seq"].as_u64() < w[1]["seq"].as_u64()));
    assert_eq!(u[0]["run"], "r1");
    assert_eq!(u[0]["kind"], "signal");
    assert_eq!(u[0]["features"]["a"], 0.5);
    assert!(u[0]["features"]["b"].is_null());
    assert_eq!(u[0]["arr"][0][1], 10.0);
    assert_eq!(u[1]["mono_ns"], 112);
    assert_eq!(u[1]["wall_ns"], 1_700_000_000_000_000_001u64);
    assert_eq!(u[1]["copy"], 1);
    assert_eq!(u[2]["src"], "pb");
    assert_eq!(u[2]["b"], 2.25);
    assert!(
        u[0]["mono_ns"].as_u64().unwrap() > 0
            && u[0]["wall_ns"].as_u64().unwrap() > 1_700_000_000_000_000_000
    );
    let st = all.iter().rfind(|r| r["kind"] == "log_stats").unwrap();
    assert_eq!(st["written"], 1000);
    assert_eq!(st["dropped"], 0);
}

#[test]
fn reserved_keys_do_not_clash() {
    let d = tmpdir("res");
    let lg = Logger::open(&d, "r", "bot").unwrap();
    lg.log("x", json!({"seq": 99, "ok": 1}));
    lg.close().unwrap();
    let all = read_all(&d);
    assert_eq!(all[0]["body_seq"], 99);
    assert_eq!(all[0]["seq"], 0);
}

#[test]
fn rotates_by_wall_hour_and_gzips() {
    let d = tmpdir("rot");
    let lg = Logger::open(&d, "r", "bot").unwrap();
    let h = 490_000u64;
    lg.log_at("a", 1, h * HOUR_NS + 5, json!({"n": 1}));
    lg.log_at("a", 2, h * HOUR_NS + HOUR_NS - 1, json!({"n": 2}));
    lg.log_at("a", 3, (h + 1) * HOUR_NS, json!({"n": 3}));
    lg.log_at("a", 4, h * HOUR_NS + 7, json!({"n": 4})); // late stamp: stays in the open (later) hour
    lg.log_at("a", 5, (h + 3) * HOUR_NS + 1, json!({"n": 5}));
    // first hour is gzipped while the logger keeps running
    let t = Instant::now();
    while !d.join(format!("bot-{h}.jsonl.gz")).exists() || d.join(format!("bot-{h}.jsonl")).exists()
    {
        assert!(
            t.elapsed() < Duration::from_secs(5),
            "rotate gzip not done: {:?}",
            names(&d)
        );
        std::thread::sleep(Duration::from_millis(10));
    }
    lg.close().unwrap();
    assert_eq!(
        names(&d),
        vec![
            format!("bot-{h}.jsonl.gz"),
            format!("bot-{}.jsonl.gz", h + 1),
            format!("bot-{}.jsonl.gz", h + 3)
        ]
    );
    let g = |hh: u64| {
        let mut s = String::new();
        GzDecoder::new(fs::File::open(d.join(format!("bot-{hh}.jsonl.gz"))).unwrap())
            .read_to_string(&mut s)
            .unwrap();
        s.lines()
            .map(|l| serde_json::from_str::<Value>(l).unwrap())
            .filter(|r| r["kind"] == "a")
            .map(|r| r["n"].as_u64().unwrap())
            .collect::<Vec<_>>()
    };
    assert_eq!(g(h), vec![1, 2]);
    assert_eq!(g(h + 1), vec![3, 4]);
    assert_eq!(g(h + 3), vec![5]);
}

#[test]
fn restart_never_overwrites_or_reopens() {
    let d = tmpdir("restart");
    let h = 490_000u64;
    for run in ["a", "b", "c"] {
        let lg = Logger::open(&d, run, "bot").unwrap();
        lg.log_at("x", 1, h * HOUR_NS, json!({"run_n": run}));
        lg.close().unwrap();
    }
    assert_eq!(
        names(&d),
        vec![
            format!("bot-{h}.1.jsonl.gz"),
            format!("bot-{h}.2.jsonl.gz"),
            format!("bot-{h}.jsonl.gz")
        ]
    );
    assert_eq!(user(&read_all(&d)).len(), 3);
}

#[test]
fn crash_leftover_is_compressed_at_open() {
    let d = tmpdir("left");
    fs::create_dir_all(&d).unwrap();
    fs::write(
        d.join("bot-5.jsonl"),
        "{\"run\":\"old\",\"seq\":0,\"mono_ns\":1,\"wall_ns\":1,\"kind\":\"x\"}\n",
    )
    .unwrap();
    let lg = Logger::open(&d, "new", "bot").unwrap();
    lg.close().unwrap();
    assert!(
        names(&d).contains(&"bot-5.jsonl.gz".to_string()),
        "{:?}",
        names(&d)
    );
    assert!(!names(&d).contains(&"bot-5.jsonl".to_string()));
}

#[test]
fn drops_are_counted_never_block() {
    let d = tmpdir("drop");
    let cfg = Config {
        capacity: 8,
        ..Config::default()
    };
    let lg = Logger::open_with(&d, "r", "bot", cfg).unwrap();
    lg.stall_writer(Duration::from_millis(400));
    let t = Instant::now();
    for i in 0..100 {
        lg.log("e", json!({"i": i}));
    }
    assert!(
        t.elapsed() < Duration::from_millis(200),
        "log blocked: {:?}",
        t.elapsed()
    );
    let dropped = lg.dropped();
    assert!(dropped >= 90, "dropped {dropped}");
    lg.close().unwrap();
    let all = read_all(&d);
    let u = user(&all);
    assert_eq!(u.len() as u64 + dropped, 100);
    let st = all.iter().rfind(|r| r["kind"] == "log_stats").unwrap();
    assert_eq!(st["dropped"].as_u64().unwrap(), dropped);
}

#[test]
fn concurrent_threads() {
    let d = tmpdir("conc");
    let lg = Logger::open(&d, "r", "bot").unwrap();
    let hs: Vec<_> = (0..8)
        .map(|t| {
            let lg = lg.clone();
            std::thread::spawn(move || {
                for i in 0..5000 {
                    lg.log("c", json!({"t": t, "i": i}));
                }
            })
        })
        .collect();
    for h in hs {
        h.join().unwrap();
    }
    lg.flush();
    let n = lg.written();
    let dropped = lg.dropped();
    lg.close().unwrap();
    assert_eq!(n + dropped, 40_000);
    let all = read_all(&d);
    let u = user(&all);
    assert_eq!(u.len() as u64, n);
    let mut seqs: Vec<u64> = u.iter().map(|r| r["seq"].as_u64().unwrap()).collect();
    seqs.sort();
    seqs.dedup();
    assert_eq!(seqs.len() as u64, n, "seq must be unique");
    for t in 0..8 {
        let mine: Vec<u64> = u
            .iter()
            .filter(|r| r["t"] == t)
            .map(|r| r["i"].as_u64().unwrap())
            .collect();
        assert!(
            mine.windows(2).all(|w| w[0] < w[1]),
            "per-thread order kept"
        );
    }
}

#[test]
fn flush_blocks_until_written() {
    let d = tmpdir("flush");
    let lg = Logger::open(&d, "r", "bot").unwrap();
    lg.log("a", json!({"x": 1}));
    lg.flush();
    let plain: Vec<_> = names(&d)
        .into_iter()
        .filter(|n| n.ends_with(".jsonl"))
        .collect();
    let s = fs::read_to_string(d.join(&plain[0])).unwrap();
    assert!(s.contains("\"kind\":\"a\""));
    lg.close().unwrap();
}

#[test]
#[ignore]
fn bench_ns_per_call() {
    let d = tmpdir("bench");
    let n = 200_000u64;
    let cfg = Config {
        capacity: 1 << 20,
        ..Config::default()
    };
    let lg = Logger::open_with(&d, "r", "bot", cfg).unwrap();
    let (m, w) = btl_log::now();
    let time = |f: &dyn Fn(u64)| {
        let t = Instant::now();
        for i in 0..n {
            f(i);
        }
        t.elapsed().as_nanos() as f64 / n as f64
    };
    let raw = time(&|i| {
        lg.log_raw(
            "feed",
            m,
            w,
            format!(
                "\"src\":\"pb\",\"b\":{},\"a\":{},\"u\":{}",
                70000.1, 70000.2, i
            ),
        )
    });
    lg.flush();
    let pre = String::from("\"src\":\"pb\",\"b\":70000.1,\"a\":70000.2,\"u\":12345");
    let push = time(&|_| lg.log_raw("feed", m, w, pre.clone()));
    lg.flush();
    let val = time(&|i| {
        lg.log_at(
            "feed",
            m,
            w,
            json!({"src": "pb", "b": 70000.1, "a": 70000.2, "u": i}),
        )
    });
    lg.flush();
    let sig = time(&|i| {
        lg.log("signal", json!({"sig": "r:1", "pu": 0.61, "features": {"a": 1.0, "b": 2.0, "c": 3.0, "d": 4.0}, "i": i}))
    });
    println!(
        "ns/call: log_raw+format {raw:.0}, log_raw(clone only) {push:.0}, log_at(json!) {val:.0}, log(json! nested) {sig:.0}; dropped {}",
        lg.dropped()
    );
    lg.close().unwrap();
}
