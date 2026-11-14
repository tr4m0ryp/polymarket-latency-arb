//! Answers to an order: one `ack` line per copy; the first OK copy settles the order (fill from
//! the response, a delayed order looked up), else it is a miss once every copy has answered.
use reqwest::Method;
use serde_json::json;
use std::time::Duration;

use btl_risk::fee;
use btl_signal::engine::World;
use btl_venue::{mono_ns, parse, Resp};

use super::{book, Exec, Timer, FATAL};
use crate::cli::OType;
use crate::live::msg::Msg;

impl Exec {
    pub fn on_ack(&mut self, cid: &str, r: &Resp, w: &World) {
        let o = parse::order(r);
        let (dec_send, recv_send) = match self.orders.get(cid) {
            Some(p) => (r.t_send_mono_ns.saturating_sub(p.t_dec_mono), r.t_send_mono_ns.saturating_sub(p.t_recv_mono)),
            None => (0, 0),
        };
        if r.code != 0 {
            self.lat_dec_send.push(dec_send);
            self.lat_recv_send.push(recv_send);
        }
        self.log.log_at("ack", r.t_ack_mono_ns, r.t_ack_wall_ns, json!({"cid": cid, "copy": r.conn, "conn": r.conn,
            "code": r.code, "ok": o.ok, "status": o.status, "order_id": o.order_id, "latency_ns": r.t_ack_mono_ns.saturating_sub(r.t_send_mono_ns),
            "t_send_mono_ns": r.t_send_mono_ns, "t_send_wall_ns": r.t_send_wall_ns, "t_hdr_mono_ns": r.t_hdr_mono_ns,
            "dec_to_send_ns": dec_send, "recv_to_send_ns": recv_send,
            "t_ack_mono_ns": r.t_ack_mono_ns, "t_ack_wall_ns": r.t_ack_wall_ns, "idle_ns": r.idle_ns, "cf_ray": r.cf_ray,
            "pop": r.pop, "http": r.http, "err_kind": o.err_kind, "err": o.err, "fill_sh": o.fill_sh, "fill_cost": o.fill_cost,
            "px": o.px, "trade_ids": o.trade_ids, "body": r.body}));
        self.log.log_at("send", r.t_send_mono_ns, r.t_send_wall_ns, json!({"cid": cid, "copy": r.conn, "conn": r.conn,
            "t_send_mono_ns": r.t_send_mono_ns, "t_send_wall_ns": r.t_send_wall_ns, "dec_to_send_ns": dec_send}));
        if let Some(k) = o.err_kind.as_deref() {
            if FATAL.contains(&k) {
                self.stop_reason = Some(format!("order error: {k}: {}", o.err.clone().unwrap_or_default()));
            }
        }
        let Some(p) = self.orders.get_mut(cid) else { return };
        p.n_ack += 1;
        let first = !p.first_ack;
        p.first_ack = true;
        let (mkt, up, limit, size) = (p.mkt, p.intent.up, p.limit, p.intent.size);
        if first {
            let now = mono_ns();
            self.book_log(w, cid, mkt, up, limit, "ack");
            self.at(now + 3_000_000_000, Timer::Book { cid: cid.into(), at: "ack+3s" });
            self.at(now + 10_000_000_000, Timer::Book { cid: cid.into(), at: "ack+10s" });
        }
        let p = self.orders.get_mut(cid).unwrap();
        if r.code == 0 {
            p.n_transport += 1;
        }
        if p.resolved {
            // a later OK copy under ANOTHER order id = the venue did not dedupe the hedged copies
            if o.ok && o.order_id.is_some() && o.order_id != p.order_id {
                let (oid, sh, cost) = (o.order_id.clone(), o.fill_sh, o.fill_cost);
                self.log.log("error", json!({"where": "hedge", "cid": cid, "err": "copy accepted as a second order",
                    "order_id": oid, "first_order_id": p.order_id, "fill_sh": sh}));
                self.stop_reason = Some("hedged copies not deduplicated by the venue".into());
                if sh > 0.0 {
                    let it = p.intent.clone();
                    let f = fee(cost / sh, sh);
                    self.risk.fill(&it, sh, cost, f);
                    self.log.log("fill", json!({"cid": cid, "order_id": oid, "src": "post_dup", "sh": sh,
                        "px": cost / sh, "cost": cost, "fee": f, "booked": true}));
                }
            }
            return;
        }
        if o.ok {
            p.resolved = true;
            p.order_id = o.order_id.clone();
            if let Some(oid) = &o.order_id {
                self.by_oid.insert(oid.clone(), cid.to_string());
            }
            self.risk.release(cid);
            self.book_fill(cid, o.fill_sh, o.fill_cost, "post", None);
            let delayed = o.status.as_deref().is_some_and(|s| s.eq_ignore_ascii_case("delayed"));
            if let (true, Some(oid), Some(v)) = (delayed, o.order_id.clone(), &self.venue) {
                let (clob, api, addr, tx, c) = (v.clob.clone(), v.api.clone(), v.addr.clone(), self.tx.clone(), cid.to_string());
                tokio::spawn(async move {
                    for _ in 0..5 {
                        tokio::time::sleep(Duration::from_millis(200)).await;
                        let r = clob.get_order(&api, &addr, &oid).await;
                        let st = parse::lookup(&r).status.unwrap_or_default().to_lowercase();
                        let _ = tx.send(Msg::Lookup { cid: c.clone(), resp: Box::new(r) });
                        if !st.is_empty() && st != "delayed" && st != "live" {
                            break;
                        }
                    }
                });
            }
            if self.order_type == OType::Gtc && o.fill_sh + 1e-9 < size {
                self.at(mono_ns() + self.gtc_cancel_ms * 1_000_000, Timer::GtcCancel { cid: cid.into() });
            }
        } else if p.n_ack >= p.k {
            p.resolved = true;
            if p.n_transport >= p.k {
                // no copy reached an answer: the order may still have filled. Keep its worst case
                // reserved and stop (cancel-all at exit), as the Python micro executor does.
                self.log.log("error", json!({"where": "post", "cid": cid, "err": "transport error on every copy"}));
                self.stop_reason = Some("order transport error on every copy".into());
            } else {
                self.risk.release(cid);
                self.bump("missed");
            }
        }
    }

    /// Book a fill once per order: risk, `fill` line. `sh` / `cost` are the order's totals so far.
    pub fn book_fill(&mut self, cid: &str, sh: f64, cost: f64, src: &str, extra: Option<serde_json::Value>) {
        let Some(p) = self.orders.get_mut(cid) else { return };
        let d_sh = sh - p.filled_sh;
        if d_sh <= 1e-9 {
            return;
        }
        let d_cost = cost * d_sh / sh;
        p.filled_sh = sh;
        let px = d_cost / d_sh;
        let f = fee(px, d_sh);
        let it = p.intent.clone();
        let oid = p.order_id.clone();
        self.risk.fill(&it, d_sh, d_cost, f);
        self.bump("filled");
        self.log.log("fill", json!({"cid": cid, "order_id": oid, "src": src, "sh": d_sh, "px": px, "cost": d_cost,
            "fee": f, "booked": true, "extra": extra}));
    }

    pub fn on_lookup(&mut self, cid: &str, r: &Resp) {
        let l = parse::lookup(r);
        self.log.log("lookup", json!({"cid": cid, "code": r.code, "found": l.found, "status": l.status,
            "fill_sh": l.fill_sh, "px": l.px, "latency_ns": r.t_ack_mono_ns.saturating_sub(r.t_send_mono_ns)}));
        if l.fill_sh > 0.0 {
            self.book_fill(cid, l.fill_sh, l.fill_cost, "lookup", None);
        }
    }

    pub fn book_log(&self, w: &World, cid: &str, mkt: i64, up: bool, limit: f64, at: &str) {
        if let Some(mut b) = book::snapshot(w, mkt, up, limit) {
            b["cid"] = json!(cid);
            b["at"] = json!(at);
            self.log.log("book", b);
        }
    }

    pub fn cancel(&self, oid: &str, reason: &str) {
        let Some(v) = &self.venue else { return };
        let (clob, api, addr, tx, k) = (v.clob.clone(), v.api.clone(), v.addr.clone(), self.tx.clone(), self.k);
        let (oid, reason) = (oid.to_string(), reason.to_string());
        tokio::spawn(async move {
            let (body, headers) = clob.cancel_req(&oid, &api, &addr);
            let resps = clob.hedge_all(k, Method::DELETE, "/order", headers, Some(body)).await;
            let _ = tx.send(Msg::Cancel { what: oid, reason, resps });
        });
    }
}
