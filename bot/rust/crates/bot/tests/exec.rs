//! The live order path against a local mock CLOB (no network, no real orders): a veto order is
//! signed, posted as 3 identical copies on 3 connections, the first OK copy books the fill in
//! the risk book, every step is logged; shutdown sends cancel-all. Also times decision -> wire.
mod mock;

use clap::Parser;
use std::path::PathBuf;

use btl_bot::cli::RunArgs;
use btl_bot::live::exec::{ipolicy, Exec, Venue};
use btl_bot::live::msg::{Msg, Recv};
use btl_log::Logger;
use btl_risk::{Limits, RiskBook};
use btl_signal::engine::{Ctx, Decision, MarketMeta, World};
use btl_signal::features::names::{self, Row};
use btl_signal::features::Pzm;
use btl_signal::feed::{Ev, Kind, Pm};
use btl_signal::Signal;
use btl_venue::{mono_ns, wall_ns, ApiCreds, Clob, Creds, Signer};

#[derive(Parser)]
struct T {
    #[command(flatten)]
    a: RunArgs,
}

fn repo() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../../..")
}

fn world(start: i64) -> World {
    let mut w = World::new(Ctx::new(Pzm::load(&repo().join("data/out/strategy/fair-pzm.json")).unwrap()));
    let meta = MarketMeta { fam: "5m".into(), slug: format!("btc-updown-5m-{start}"), start, end: start + 300,
        condition_id: "0x1".into(), up: "111".into(), down: "222".into(), tick: 0.01 };
    w.add_market(&meta);
    let t = wall_ns() as f64 / 1e9;
    w.apply(&Ev::Pm(Pm { t, ts: t, mkt: start, snap: true, chg: vec![(1, 55, 100.0), (-1, 57, 100.0), (-1, 58, 200.0)] }));
    w
}

fn signal(start: i64) -> Signal {
    let mut row: Row = [f64::NAN; names::N];
    row[names::PM_BB] = 55.0;
    row[names::PM_BA] = 57.0;
    Signal { t: wall_ns() as f64 / 1e9, kind: Kind::Pm, mkt: start, slug: format!("btc-updown-5m-{start}"), p_dmic: 0.01,
        s_dmic: 0.0, trig_side: 1.0, pu: 0.05, pdn: -0.1, edge: 0.05, side: 1.0, seen: 0.57, decision: Decision::Order,
        gate: f64::NAN, x: None, row: Box::new(row), feat_ns: 0, model_ns: 0 }
}

#[test]
fn live_order_path_against_mock_clob() {
    let rt = tokio::runtime::Builder::new_multi_thread().worker_threads(2).enable_all().build().unwrap();
    let _g = rt.enter();
    let (host, seen) = rt.block_on(mock::serve());
    let clob = Clob::new(&host, 3).unwrap();
    rt.block_on(clob.warm());
    let pk = "0x4c0883a69102937d6231471b5dbb6204fe5129617082792ae468d01a3f362318";
    let signer = Signer::new(&Creds::new(pk, "0x6E0C80c90ea6C15917308F820Eac91Ce2724B5b5", 3, None).unwrap()).unwrap();
    let api = ApiCreds { key: "key-1".into(), secret: "c2VjcmV0LXRlc3Q=".into(), passphrase: "pp".into() };
    let dir = std::env::temp_dir().join(format!("btl-exec-{}", std::process::id()));
    let _ = std::fs::remove_dir_all(&dir);
    std::fs::create_dir_all(&dir).unwrap();
    let log = Logger::open(&dir, "t", "bot").unwrap();
    let mut risk = RiskBook::open(Limits::default(), dir.join("state"), wall_ns() as f64 / 1e9).unwrap();
    risk.set_balance(Some(100.0));
    let a = T::parse_from(["t", "--i-approve", "--sizing", "fixed", "--size", "5"]).a;
    let (ipol, warn) = ipolicy::from_args(&a).unwrap();
    assert!(warn.is_empty());
    let (tx, rx) = crossbeam_channel::unbounded();
    let addr = signer.address().to_string();
    let venue = Venue { clob: clob.clone(), api: api.clone(), addr, sig_type: 3 };
    let mut ex = Exec::new("t".into(), log.clone(), risk, Some(venue), signer, "key-1".into(), ipol, tx, &a);
    let mut acks_ns = Vec::new();
    for n in 0..20 {
        let start = 1_760_000_100 + 300 * n as i64;
        let w = world(start);
        seen.lock().unwrap().clear();
        let recv = Recv { conn: 0, mono: mono_ns(), wall: wall_ns() };
        let cid = ex.on_signal(&signal(start), &w, recv, &format!("t:{n}")).unwrap_or_else(|r| panic!("skipped: {r}"));
        for _ in 0..3 {
            match rx.recv_timeout(std::time::Duration::from_secs(5)).unwrap() {
                Msg::Ack { cid: c, resp } => {
                    assert_eq!(c, cid);
                    acks_ns.push(resp.t_ack_mono_ns - resp.t_send_mono_ns);
                    ex.on_ack(&c, &resp, &w);
                }
                _ => panic!("expected an ack"),
            }
        }
        let s = seen.lock().unwrap().clone();
        let posts: Vec<_> = s.iter().filter(|x| x.line.starts_with("POST /order")).collect();
        assert_eq!(posts.len(), 3, "3 copies");
        assert!(posts.iter().all(|p| p.body == posts[0].body), "identical copies");
        assert_eq!(posts.iter().map(|p| p.peer).collect::<std::collections::HashSet<_>>().len(), 3, "3 connections");
        assert!(posts[0].body.contains("\"orderType\":\"FAK\"") && posts[0].body.contains("\"takerAmount\":\"5000000\""));
        assert!(ex.risk.exposure() > 2.85, "fill booked");
        ex.risk.resolve(&format!("btc-updown-5m-{start}"), 1.0);
    }
    assert_eq!(ex.n.get("filled"), Some(&20));
    assert!((ex.risk.realised() - 20.0 * (5.0 - 2.85 - 0.07 * 0.57 * 0.43 * 5.0)).abs() < 1e-6);
    let mut d = ex.lat_dec_send.clone();
    let mut sg = ex.lat_sign.clone();
    sg.sort();
    eprintln!("sign us p50 {:.1}", sg[sg.len() / 2] as f64 / 1e3);
    d.sort();
    acks_ns.sort();
    eprintln!("decision->send (each copy on the wire) us p50 {:.1} p90 {:.1} max {:.1}; mock round trip us p50 {:.1}",
        d[d.len() / 2] as f64 / 1e3, d[d.len() * 9 / 10] as f64 / 1e3, d[d.len() - 1] as f64 / 1e3, acks_ns[acks_ns.len() / 2] as f64 / 1e3);
    let v = ex.venue.as_ref().unwrap();
    assert_eq!(btl_bot::live::shutdown(&rt, &log, Some(v), "test"), Some(true));
    assert!(seen.lock().unwrap().iter().any(|x| x.line.starts_with("DELETE /cancel-all")));
    log.flush();
    log.close().unwrap();
    let mut kinds = std::collections::HashMap::<String, usize>::new();
    for e in std::fs::read_dir(&dir).unwrap() {
        let p = e.unwrap().path();
        if p.extension().is_some_and(|x| x == "gz") {
            let r = std::io::BufReader::new(flate2::read::MultiGzDecoder::new(std::fs::File::open(&p).unwrap()));
            for l in std::io::BufRead::lines(r) {
                let j: serde_json::Value = serde_json::from_str(&l.unwrap()).unwrap();
                *kinds.entry(j["kind"].as_str().unwrap().to_string()).or_default() += 1;
            }
        }
    }
    for (k, n) in [("order", 20), ("send", 60), ("ack", 60), ("fill", 20), ("book", 40), ("cancel", 3)] {
        assert_eq!(kinds.get(k).copied().unwrap_or(0), n, "{k} lines: {kinds:?}");
    }
}

#[test]
fn i_policy_guards() {
    let p = |args: &[&str]| ipolicy::from_args(&T::parse_from([&["t", "--dry"][..], args].concat()).a).map(|x| x.1);
    assert!(p(&[]).unwrap().is_empty(), "default i = 0, no warning");
    assert!(p(&["--i", "0.01"]).is_err(), "i > 0 needs --allow-i-positive");
    assert_eq!(p(&["--i", "0.01", "--allow-i-positive"]).unwrap().len(), 1);
    assert!(p(&["--i", "0.10", "--allow-i-positive"]).is_err(), "above the hard ceiling");
    assert!(p(&["--i-mode", "random", "--i-set", "0,0.01"]).is_err(), "experiment flag needed");
    assert!(p(&["--i-mode", "random", "--i-set", "0,0.01", "--i-random-experiment"]).is_ok());
    assert!(p(&["--i-mode", "predicted"]).is_err(), "no predictor plugged in");
    assert_eq!(ipolicy::limit(0.57, 0.0), 0.57);
    assert_eq!(ipolicy::limit(0.98, 0.02), 0.99);
}

fn resp(conn: usize, code: u16, body: serde_json::Value) -> btl_venue::Resp {
    let t = mono_ns();
    btl_venue::Resp { method: "POST".into(), path: "/order".into(), code, body, t_send_mono_ns: t, t_hdr_mono_ns: t,
        t_ack_mono_ns: t + 1000, t_send_wall_ns: wall_ns(), t_ack_wall_ns: wall_ns(), http: "HTTP/2".into(), idle_ns: 0,
        cf_ray: None, pop: None, hdr: vec![], err: if code == 0 { Some("timeout".into()) } else { None }, conn }
}

fn exec_offline(tag: &str) -> (Exec, tokio::runtime::Runtime) {
    let rt = tokio::runtime::Builder::new_multi_thread().worker_threads(1).enable_all().build().unwrap();
    let pk = "0x4c0883a69102937d6231471b5dbb6204fe5129617082792ae468d01a3f362318";
    let signer = Signer::new(&Creds::new(pk, "0x6E0C80c90ea6C15917308F820Eac91Ce2724B5b5", 3, None).unwrap()).unwrap();
    let api = ApiCreds { key: "key-1".into(), secret: "c2VjcmV0LXRlc3Q=".into(), passphrase: "pp".into() };
    let dir = std::env::temp_dir().join(format!("btl-exec-{tag}-{}", std::process::id()));
    let _ = std::fs::remove_dir_all(&dir);
    let log = Logger::open(&dir, "t", "bot").unwrap();
    let mut risk = RiskBook::open(Limits::default(), dir.join("state"), wall_ns() as f64 / 1e9).unwrap();
    risk.set_balance(Some(100.0));
    let a = T::parse_from(["t", "--i-approve", "--sizing", "fixed", "--size", "5"]).a;
    let (ipol, _) = ipolicy::from_args(&a).unwrap();
    let (tx, _rx) = crossbeam_channel::unbounded();
    std::mem::forget(_rx);
    let venue = Venue { clob: Clob::new("http://127.0.0.1:9", 3).unwrap(), api, addr: signer.address().into(), sig_type: 3 };
    (Exec::new("t".into(), log, risk, Some(venue), signer, "key-1".into(), ipol, tx, &a), rt)
}

#[test]
fn transport_error_on_every_copy_keeps_reservation_and_stops() {
    let (mut ex, rt) = exec_offline("transport");
    let _g = rt.enter();
    let w = world(1_760_000_100);
    let cid = ex.on_signal(&signal(1_760_000_100), &w, Recv { conn: 0, mono: mono_ns(), wall: wall_ns() }, "t:1").unwrap();
    for c in 0..3 {
        ex.on_ack(&cid, &resp(c, 0, serde_json::Value::Null), &w);
    }
    assert!(ex.stop_reason.as_deref().unwrap().contains("transport"));
    assert!(ex.risk.exposure() > 2.85, "worst case stays reserved");
}

#[test]
fn second_order_id_from_a_copy_is_booked_and_stops() {
    let (mut ex, rt) = exec_offline("dedupe");
    let _g = rt.enter();
    let w = world(1_760_000_100);
    let cid = ex.on_signal(&signal(1_760_000_100), &w, Recv { conn: 0, mono: mono_ns(), wall: wall_ns() }, "t:1").unwrap();
    let ok = |oid: &str| serde_json::json!({"success": true, "orderID": oid, "status": "matched", "makingAmount": "2.85", "takingAmount": "5"});
    ex.on_ack(&cid, &resp(0, 200, ok("0xa")), &w);
    ex.on_ack(&cid, &resp(1, 400, serde_json::json!({"error": "order duplicated"})), &w);
    assert!(ex.stop_reason.is_none());
    let one = ex.risk.exposure();
    ex.on_ack(&cid, &resp(2, 200, ok("0xb")), &w);
    assert!(ex.stop_reason.as_deref().unwrap().contains("deduplicated"));
    assert!((ex.risk.exposure() - 2.0 * one).abs() < 1e-9, "both fills booked");
}

#[test]
fn fak_no_match_releases_after_all_copies() {
    let (mut ex, rt) = exec_offline("miss");
    let _g = rt.enter();
    let w = world(1_760_000_100);
    let cid = ex.on_signal(&signal(1_760_000_100), &w, Recv { conn: 0, mono: mono_ns(), wall: wall_ns() }, "t:1").unwrap();
    let nm = serde_json::json!({"error": "no orders found to match with FAK order"});
    ex.on_ack(&cid, &resp(0, 400, nm.clone()), &w);
    assert!(ex.risk.exposure() > 0.0, "reserved until every copy answered");
    ex.on_ack(&cid, &resp(1, 400, serde_json::json!({"error": "order duplicated"})), &w);
    ex.on_ack(&cid, &resp(2, 400, nm), &w);
    assert_eq!(ex.risk.exposure(), 0.0);
    assert!(ex.stop_reason.is_none());
}
