//! Signal -> order: i, limit, risk check, sign, hedged send (or the dry would-send).
use reqwest::Method;
use serde_json::json;

use btl_risk::Intent;
use btl_signal::engine::World;
use btl_signal::Signal;
use btl_venue::{mono_ns, new_salt, wall_ns, OrderSpec, OrderType, Side};

use super::{book, ipolicy, Exec, Pending, Timer};
use crate::cli::OType;
use crate::live::msg::{Msg, Recv};

impl Exec {
    /// Handle an order decision: Ok(cid) if it went out (or would have, dry), Err(skip reason).
    pub fn on_signal(&mut self, s: &Signal, w: &World, recv: Recv, sig_id: &str) -> Result<String, &'static str> {
        let t_dec = mono_ns();
        let m = w.mkts.iter().find(|m| m.meta.start == s.mkt).ok_or("no_market")?;
        let up = s.side > 0.0;
        let i = self.ipol.choose(s);
        let limit = ipolicy::limit(s.seen, i);
        let mut it = Intent { arm: "vt_v1_m0.02_trigger".into(), slug: m.meta.slug.clone(),
            token: if up { m.meta.up.clone() } else { m.meta.down.clone() }, up, price: limit, size: 0.0, end: m.end };
        let now = wall_ns() as f64 / 1e9;
        // size from the live equity and the bankroll caps (btl_risk::bankroll), then the hard caps
        let reason = if (m.meta.tick - 0.01).abs() > 1e-9 { Some("tick") }
            else if self.stop_reason.is_some() { Some("stopped") }
            else {
                match self.risk.size_for(&it, s.edge) {
                    Ok(q) => {
                        it.size = q;
                        self.risk.check(&it, now)
                    }
                    Err(r) => Some(r),
                }
            };
        let size = it.size;
        if let Some(r) = reason {
            self.bump("skipped");
            self.log.log("skip", json!({"sig": sig_id, "cid": sig_id, "reason": r, "slug": it.slug, "limit": limit, "i": i}));
            return Err(r);
        }
        let cid = sig_id.to_string();
        let spec = OrderSpec { token_id: it.token.clone(), price: limit, size, side: Side::Buy,
            order_type: match self.order_type { OType::Fak => OrderType::Fak, OType::Fok => OrderType::Fok, OType::Gtc => OrderType::Gtc },
            post_only: false, expiration: 0 };
        let ts_ms = match &self.venue { Some(v) => (v.clob.server_now_s() * 1e3) as u64, None => wall_ns() / 1_000_000 };
        let signed = match self.signer.sign(&spec, &self.owner, new_salt(), ts_ms) {
            Ok(x) => x,
            Err(e) => {
                self.log.log("error", json!({"where": "sign", "cid": cid, "err": format!("{e:#}")}));
                self.stop_reason = Some(format!("sign error: {e:#}"));
                return Err("sign_error");
            }
        };
        self.risk.reserve(&cid, &it, now);
        let t_wire = mono_ns();
        if let Some(v) = &self.venue {
            let headers = v.clob.post_headers(&signed, &v.api, &v.addr);
            let mut rx = v.clob.hedge(self.k, Method::POST, "/order", headers, Some(signed.body.clone()));
            let (tx, c) = (self.tx.clone(), cid.clone());
            tokio::spawn(async move {
                while let Some(r) = rx.recv().await {
                    let _ = tx.send(Msg::Ack { cid: c.clone(), resp: Box::new(r) });
                }
            });
        } else {
            self.at(t_wire + self.dry_ack_ms * 1_000_000, Timer::DryAck { cid: cid.clone() });
        }
        self.bump("sent");
        self.last_send.store(now as u64, std::sync::atomic::Ordering::Relaxed);
        if self.venue.is_none() {   // dry: the would-send instant; live: each copy's send (ack.rs)
            self.lat_dec_send.push(t_wire.saturating_sub(t_dec));
            self.lat_recv_send.push(t_wire.saturating_sub(recv.mono));
        }
        self.lat_sign.push(signed.sign_ns);
        let dry = self.dry();
        self.log.log("order", json!({"sig": sig_id, "cid": cid, "slug": it.slug, "token": it.token, "up": up,
            "side": s.side, "seen": s.seen, "i": i, "i_mode": self.ipol.mode(), "limit": limit, "size": size,
            "order_type": signed.spec.order_type.as_str(), "k": self.k, "dry": dry, "t": s.t, "t_dec_mono_ns": t_dec,
            "t_recv_mono_ns": recv.mono, "t_wire_mono_ns": t_wire, "dec_to_wire_ns": t_wire - t_dec, "build_ns": signed.build_ns, "sign_ns": signed.sign_ns,
            "maker_amount": signed.maker_amount, "taker_amount": signed.taker_amount, "salt": signed.salt,
            "ts_ms": signed.timestamp_ms, "pred": if up { s.pu } else { s.pdn }, "edge": s.edge,
            "body": if dry { Some(&signed.body) } else { None }}));
        if dry {
            self.log.log_at("send", t_wire, wall_ns(), json!({"cid": cid, "copy": 0, "conn": -1, "dry": true,
                "t_send_mono_ns": t_wire}));
        }
        if let Some(b) = book::snapshot(w, s.mkt, up, limit) {
            let mut b = b;
            b["cid"] = json!(cid);
            b["at"] = json!("send");
            self.log.log("book", b);
        }
        self.orders.insert(cid.clone(), Pending { intent: it, mkt: s.mkt, limit, k: if dry { 1 } else { self.k },
            n_ack: 0, resolved: false, first_ack: false, filled_sh: 0.0, order_id: None, n_transport: 0, t_dec_mono: t_dec,
            t_recv_mono: recv.mono });
        Ok(cid)
    }
}

/// Shares for one order: `base`, raised to the venue's $1 minimum (btl_risk::bankroll).
pub fn min_notional_size(base: f64, limit: f64) -> f64 {
    btl_risk::bankroll::min_notional_size(base, limit)
}
