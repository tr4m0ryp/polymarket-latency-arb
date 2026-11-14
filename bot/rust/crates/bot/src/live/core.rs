//! The decision thread: owns the engine, the risk book and the executor. Per feed message:
//! update state, decide, send at once on an order, and only then write the log lines. Every
//! 50 ms: timers, marks, the stop conditions (kill file, loss cap, fatal venue error, hours).
use crossbeam_channel::{Receiver, RecvTimeoutError};
use serde_json::json;
use std::path::PathBuf;
use std::time::Duration;

use btl_signal::engine::{Decision, Engine};
use btl_signal::feed::Ev;
use btl_venue::{mono_ns, parse, wall_ns};

use super::exec::Exec;
use super::logfmt;
use super::msg::Msg;
use super::stats::Stats;
use crate::cli::LogFeeds;

pub struct Loop {
    pub eng: Engine,
    pub ex: Exec,
    pub rx: Receiver<Msg>,
    pub kill: PathBuf,
    pub until_mono: Option<u64>,
    pub log_feeds: LogFeeds,
    pub stats: Stats,
    pub n_sig: u64,
}

impl Loop {
    /// Run until a stop; returns the reason.
    pub fn run(&mut self) -> String {
        let mut next_tick = 0u64;
        loop {
            match self.rx.recv_timeout(Duration::from_millis(10)) {
                Ok(m) => {
                    if let Some(why) = self.handle(m) {
                        return why;
                    }
                }
                Err(RecvTimeoutError::Timeout) => {}
                Err(RecvTimeoutError::Disconnected) => return "feeds closed".into(),
            }
            let now = mono_ns();
            if now >= next_tick {
                next_tick = now + 50_000_000;
                if let Some(why) = self.tick(now) {
                    return why;
                }
            }
        }
    }

    fn handle(&mut self, m: Msg) -> Option<String> {
        match m {
            Msg::Ev(ev, recv) => {
                let sig = self.eng.on_event(&ev);
                let mut sent: Option<Result<String, &'static str>> = None;
                let mut sig_id = String::new();
                if let Some(s) = &sig {
                    self.n_sig += 1;
                    sig_id = format!("{}:{}", self.ex.run, self.n_sig);
                    if s.decision == Decision::Order {
                        sent = Some(self.ex.on_signal(s, &self.eng.world, recv, &sig_id));
                    }
                }
                let pm_top = if let Ev::Pm(p) = &ev {
                    self.eng.world.mkts.iter().find(|m| m.meta.start == p.mkt).map(|m| (m.book.bb, m.book.ba, true))
                } else { None };
                self.stats.feed(&ev, recv);
                if self.log_feeds == LogFeeds::All {
                    self.ex.log.log_raw("feed", recv.mono, recv.wall, logfmt::feed(&ev, &recv, pm_top));
                }
                if let Some(s) = sig {
                    self.stats.signal(&s);
                    let (dec, reason) = match s.decision {
                        Decision::Order => match sent {
                            Some(Err(r)) => ("skip", Some(r)),
                            _ => ("order", None),
                        },
                        Decision::Veto(r) => ("veto", Some(r)),
                    };
                    self.ex.log.log_at("signal", recv.mono, recv.wall, logfmt::signal(&s, &sig_id, ev.venue_t(), dec, reason));
                }
            }
            Msg::Market(meta) => {
                self.eng.world.add_market(&meta);
                self.ex.log.log("market", json!(*meta));
            }
            Msg::Conn { feed, conn, state, err } => {
                self.ex.log.log("conn", json!({"feed": feed, "conn": conn, "state": state, "err": err}));
            }
            Msg::Ack { cid, resp } => self.ex.on_ack(&cid, &resp, &self.eng.world),
            Msg::Lookup { cid, resp } => self.ex.on_lookup(&cid, &resp),
            Msg::DryAck { .. } => {}
            Msg::Cancel { what, reason, resps } => {
                for r in &resps {
                    self.ex.log.log("cancel", json!({"what": what, "reason": reason, "code": r.code, "ok": r.ok(),
                        "conn": r.conn, "latency_ns": r.t_ack_mono_ns.saturating_sub(r.t_send_mono_ns), "body": r.body}));
                }
            }
            Msg::User(u) => self.ex.on_user(u),
            Msg::Trades(r) => self.ex.on_trades(r),
            Msg::Balance(r) => {
                let b = parse::balance(&r);
                if r.ok() {
                    self.ex.risk.set_balance(Some(b.balance));
                }
                self.ex.log.log("balance", json!({"balance": b.balance, "allowance_ok": b.allowance_ok, "code": b.code}));
            }
            Msg::Settle { slug, outcome } => {
                self.ex.risk.resolve(&slug, outcome);
                self.ex.log.log("settle", json!({"slug": slug, "outcome": outcome, "pnl": self.ex.risk.pnl()}));
            }
            Msg::Stop(why) => return Some(why),
        }
        None
    }

    fn tick(&mut self, now: u64) -> Option<String> {
        self.ex.run_timers(&self.eng.world);
        let marks: Vec<(String, f64)> = self.ex.risk.positions().filter_map(|((slug, token), p)| {
            let m = self.eng.world.mkts.iter().find(|m| &m.meta.slug == slug)?;
            let mid = m.book.mid();
            (!mid.is_nan()).then(|| (token.clone(), if p.up { mid } else { 1.0 - mid }))
        }).collect();
        for (t, m) in marks {
            self.ex.risk.mark(&t, m);
        }
        if self.kill.exists() {
            return Some(format!("kill file {}", self.kill.display()));
        }
        self.ex.risk.roll(wall_ns() as f64 / 1e9);
        if self.ex.risk.breach() {
            return Some(self.ex.risk.stop_reason().unwrap_or("loss cap").to_string());
        }
        if let Some(r) = &self.ex.stop_reason {
            return Some(r.clone());
        }
        if self.until_mono.is_some_and(|u| now >= u) {
            return Some("hours elapsed".into());
        }
        if self.stats.due(now) {
            let line = self.stats.line(&self.eng, &mut self.ex, self.rx.len());
            self.ex.log.log("stats", line);
        }
        None
    }
}
