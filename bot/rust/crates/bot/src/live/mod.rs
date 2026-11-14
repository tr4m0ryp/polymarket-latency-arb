//! `btclat-bot run`: feeds -> decision thread -> taker orders, with the structured log.
//! Stop on SIGTERM / SIGINT, the KILL file, the loss cap, a fatal venue error or --hours;
//! every stop sends cancel-all (live) and closes the log (flush + gzip) before exit.
pub mod core;
pub mod exec;
pub mod feeds;
pub mod logfmt;
pub mod msg;
pub mod preflight;
pub mod stats;
pub mod tasks;

use anyhow::{bail, Context, Result};
use reqwest::Method;
use serde_json::json;
use std::path::{Path, PathBuf};
use std::sync::{Arc, Mutex};

use btl_log::Logger;
use btl_risk::{config_dir, offline_checks, LimitOverrides, Limits, RiskBook};
use btl_venue::{mono_ns, wall_ns};

use crate::cli::RunArgs;
use crate::setup;

fn run_name(a: &RunArgs) -> String {
    a.run.clone().unwrap_or_else(|| {
        let t = wall_ns() / 1_000_000_000;
        let host = host();
        let tm = btl_risk::utc_day(t as f64).replace('-', "");
        let hm = format!("{:02}{:02}", (t % 86400) / 3600, (t % 3600) / 60);
        format!("{tm}-{hm}-{}-{host}", if a.dry { "dry" } else { "live" })
    })
}

fn host() -> String {
    std::fs::read_to_string("/proc/sys/kernel/hostname").unwrap_or_default().trim().to_string()
}

fn limits(a: &RunArgs) -> Result<Limits> {
    Limits::default().lowered(LimitOverrides { max_shares: None, max_notional: a.max_notional,
        max_exposure: a.max_exposure, loss_cap: a.loss_cap, max_orders_hour: a.max_orders_hour, max_inflight: None,
        min_refractory_s: a.refractory }).map_err(|e| anyhow::anyhow!("refusing: {e}"))
}

pub fn run(home: &Path, a: RunArgs) -> Result<i32> {
    if !a.dry && !a.i_approve {
        bail!("refusing: give --dry, or --i-approve for real orders (with the user's explicit approval)");
    }
    if !(1..=btl_venue::MAX_CONNS).contains(&a.k) {
        bail!("refusing: --k {} outside 1..{}", a.k, btl_venue::MAX_CONNS);
    }
    let lim = limits(&a)?;
    let bank = a.bankroll().map_err(|e| anyhow::anyhow!("refusing: {e}"))?;
    let (ipol, warn) = exec::ipolicy::from_args(&a)?;
    let config = a.config.clone().unwrap_or_else(config_dir);
    let now = wall_ns() as f64 / 1e9;
    if a.dry {
        if btl_risk::killed(&config) {
            bail!("refusing: kill file {} exists", config.join("KILL").display());
        }
    } else {
        offline_checks(true, &config, now).map_err(|e| anyhow::anyhow!("{e}"))?;
        if a.model.model_sha256.is_none() {
            bail!("refusing: live runs need --model-sha256 (the model file is pinned by hash)");
        }
    }
    let (spec, pinned) = setup::model_spec(home, &a.model.model, a.model.model_sha256.as_deref())?;
    let loaded = setup::build(home, &spec, pinned, &a.model.fair, Default::default())?;
    let rt = tokio::runtime::Builder::new_multi_thread().worker_threads(2).enable_all().build()?;
    let (venue, signer, owner, info) = if a.dry {
        let (s, o) = preflight::dry_signer()?;
        (None, s, o, json!({"dry": true}))
    } else {
        let (v, s, o, i) = rt.block_on(preflight::live(&config, &a.clob_host, a.k))?;
        (Some(v), s, o, i)
    };
    let run = run_name(&a);
    let root = if a.root.is_absolute() { a.root.clone() } else { home.join(&a.root) };
    let dir = root.join(&run);
    std::fs::create_dir_all(&root)?;
    std::fs::create_dir(&dir).with_context(|| format!("refusing: run directory {} exists", dir.display()))?;
    let state: PathBuf = if a.dry { dir.join("state-dry") } else { config.join("state") };
    let risk = RiskBook::open(lim, &state, now).map_err(|e| anyhow::anyhow!("risk book: {e}"))?;
    let log = Logger::open(&dir, &run, "bot")?;
    for w in &warn {
        eprintln!("{w}");
    }
    log.log("start", json!({"mode": if a.dry { "dry" } else { "live" }, "args": a, "model": loaded.model,
        "limits": format!("{lim:?}"), "i_mode": ipol.mode(), "i": a.i, "i_set": a.i_set, "warnings": warn,
        "venue": info, "version": env!("CARGO_PKG_VERSION"), "host": host(), "pid": std::process::id(), "state": state,
        "pnl": risk.pnl(), "exposure": risk.exposure(), "orders_last_hour": risk.orders_last_hour(now)}));
    eprintln!("btclat-bot: run {run} ({}), logs {}", if a.dry { "DRY" } else { "LIVE" }, dir.display());
    let (tx, rx) = crossbeam_channel::bounded(262_144);
    let mut ex = exec::Exec::new(run.clone(), log.clone(), risk, venue, signer, owner, ipol, tx.clone(), &a);
    if let Some(b) = info.get("balance").and_then(|x| x.as_f64()) {
        ex.risk.set_balance(Some(b));
    } else if a.dry {
        ex.risk.set_balance(Some(a.dry_balance + a.reserve));   // dry bankroll = --dry-balance
    }
    ex.risk.set_bankroll(bank);   // again: the peak and day peak read the equity set just above
    log.log("bankroll", json!({"caps": format!("{bank:?}"), "equity": ex.risk.equity()}));
    let fans = {
        let _g = rt.enter();
        let fans: Vec<(&'static str, Arc<Mutex<feeds::binance::FanIn>>)> = vec![("spot", Default::default()), ("perp", Default::default())];
        feeds::binance::spawn(false, a.conns, tx.clone(), fans[0].1.clone());
        feeds::binance::spawn(true, a.conns, tx.clone(), fans[1].1.clone());
        let ends: tasks::Ends = Default::default();
        rt.spawn(tasks::discovery(tx.clone(), ends.clone()));
        rt.spawn(tasks::settle(tx.clone(), ends));
        if let Some(v) = &ex.venue {
            tasks::spawn_live(&tx, v, ex.last_send.clone());
            v.clob.spawn_keep_warm(1.0);
        }
        tasks::spawn_signals(tx.clone());
        fans
    };
    let until = a.hours.map(|h| mono_ns() + (h * 3600e9) as u64);
    let vshut = ex.venue.clone();   // cancel-all must work even if the decision thread dies
    let handle = rt.handle().clone();
    let lp = core::Loop { eng: loaded.engine, ex, rx, kill: config.join("KILL"), until_mono: until,
        log_feeds: a.log_feeds, stats: stats::Stats::new(60, fans), n_sig: 0 };
    let th = std::thread::Builder::new().name("decide".into()).spawn(move || {
        let _g = handle.enter();
        let mut lp = lp;
        let why = lp.run();
        (why, lp)
    })?;
    let (why, lp) = match th.join() {
        Ok(x) => (x.0, Some(x.1)),
        Err(_) => ("decision thread panicked".to_string(), None),
    };
    drop(tx);
    let ok = shutdown(&rt, &log, vshut.as_ref(), &why);
    log.log("stop", json!({"reason": why, "cancel_all_ok": ok, "pnl": lp.as_ref().map(|l| l.ex.risk.pnl()),
        "exec": lp.as_ref().map(|l| l.ex.n.clone())}));
    log.flush();
    log.close()?;
    rt.shutdown_timeout(std::time::Duration::from_secs(2));
    eprintln!("btclat-bot: stopped: {why}; cancel-all ok: {ok:?}; logs {}", dir.display());
    Ok(0)
}

/// Cancel-all on k connections, retried 3 times (live); None in dry.
pub fn shutdown(rt: &tokio::runtime::Runtime, log: &Logger, v: Option<&exec::Venue>, why: &str) -> Option<bool> {
    let v = v?;
    for attempt in 0..3 {
        let rs = rt.block_on(async {
            let h = btl_venue::l2_headers(&v.api, &v.addr, "DELETE", "/cancel-all", None, v.clob.auth_ts());
            v.clob.hedge_all(v.clob.k(), Method::DELETE, "/cancel-all", h, None).await
        });
        let ok = rs.iter().any(|r| r.ok());
        for r in &rs {
            log.log("cancel", json!({"what": "all", "reason": why, "attempt": attempt, "conn": r.conn, "code": r.code,
                "ok": r.ok(), "latency_ns": r.t_ack_mono_ns.saturating_sub(r.t_send_mono_ns), "body": r.body}));
        }
        if ok {
            return Some(true);
        }
        std::thread::sleep(std::time::Duration::from_millis(500 * (attempt + 1)));
    }
    Some(false)
}
