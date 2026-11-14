//! Due timers on the decision thread: book snapshots after the ack (3 s, 10 s: markouts and
//! what the book did during and after the hold), GTC remainder cancels, dry simulated acks.
use serde_json::json;

use btl_signal::engine::World;
use btl_venue::mono_ns;

use super::{Exec, Timer};

impl Exec {
    pub fn run_timers(&mut self, w: &World) {
        let now = mono_ns();
        while let Some(std::cmp::Reverse((due, _, id))) = self.timers.peek().copied() {
            if due > now {
                break;
            }
            self.timers.pop();
            let Some(t) = self.timer_jobs.remove(&id) else { continue };
            match t {
                Timer::Book { cid, at } => {
                    if let Some(p) = self.orders.get(&cid) {
                        self.book_log(w, &cid, p.mkt, p.intent.up, p.limit, at);
                    }
                    if at == "ack+10s" {
                        self.orders.remove(&cid);
                    }
                }
                Timer::GtcCancel { cid } => {
                    if let Some(oid) = self.orders.get(&cid).and_then(|p| p.order_id.clone()) {
                        self.cancel(&oid, "gtc_rest");
                    }
                }
                Timer::DryAck { cid } => {
                    let Some(p) = self.orders.get_mut(&cid) else { continue };
                    p.resolved = true;
                    p.first_ack = true;
                    let (mkt, up, limit) = (p.mkt, p.intent.up, p.limit);
                    self.risk.release(&cid);
                    self.log.log("ack", json!({"cid": cid, "copy": 0, "conn": -1, "dry": true, "ok": false,
                        "status": "dry", "code": 0, "err_kind": "dry", "err": null, "order_id": null,
                        "latency_ns": self.dry_ack_ms * 1_000_000, "fill_sh": 0.0, "fill_cost": 0.0}));
                    self.book_log(w, &cid, mkt, up, limit, "ack");
                    self.at(now + 3_000_000_000, Timer::Book { cid: cid.clone(), at: "ack+3s" });
                    self.at(now + 10_000_000_000, Timer::Book { cid, at: "ack+10s" });
                }
            }
        }
    }
}
