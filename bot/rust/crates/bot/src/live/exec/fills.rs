//! Fill confirmations that do not move risk (the POST answer / lookup already booked them):
//! our trades from GET /data/trades (polled while orders are recent) and the user websocket.
//! Logged per trade id with the order they belong to, for reconciliation in the report.
use serde_json::{json, Value};

use btl_venue::UserMsg;

use super::Exec;

fn order_ids(t: &Value) -> Vec<String> {
    let mut v: Vec<String> = t["taker_order_id"].as_str().map(|s| vec![s.to_string()]).unwrap_or_default();
    if let Some(m) = t["maker_orders"].as_array() {
        v.extend(m.iter().filter_map(|x| x["order_id"].as_str().map(String::from)));
    }
    v
}

impl Exec {
    fn confirm(&mut self, t: &Value, src: &str) {
        let id = t["id"].as_str().or_else(|| t["trade_id"].as_str()).unwrap_or("").to_string();
        let key = format!("{src}:{id}");
        if id.is_empty() || !self.trade_ids.insert(key) {
            return;
        }
        let oids = order_ids(t);
        let cid = oids.iter().find_map(|o| self.by_oid.get(o).cloned());
        let num = |k: &str| t[k].as_str().and_then(|s| s.parse::<f64>().ok()).or_else(|| t[k].as_f64());
        let (sh, px) = (num("size"), num("price"));
        self.log.log("fill", json!({"cid": cid, "order_id": oids.first(), "src": src, "sh": sh, "px": px,
            "cost": sh.zip(px).map(|(a, b)| a * b), "trade_id": id, "match_t": t["match_time"], "status": t["status"],
            "side": t["side"], "trader_side": t["trader_side"], "booked": false}));
    }

    pub fn on_trades(&mut self, r: Result<Vec<Value>, String>) {
        match r {
            Ok(v) => v.iter().for_each(|t| self.confirm(t, "trade_poll")),
            Err(e) => self.log.log("error", json!({"where": "trade_poll", "err": e})),
        }
    }

    pub fn on_user(&mut self, m: UserMsg) {
        match m {
            UserMsg::Event { ev, t_mono_ns, t_wall_ns } => {
                if ev["event_type"].as_str() == Some("trade") {
                    self.confirm(&ev, "user_ws");
                }
                self.log.log_at("user", t_mono_ns, t_wall_ns, json!({"ev": ev}));
            }
            UserMsg::State { state, err, t_mono_ns, t_wall_ns } => {
                self.log.log_at("conn", t_mono_ns, t_wall_ns, json!({"feed": "user_ws", "conn": 0,
                    "state": format!("{state:?}").to_lowercase(), "err": err}));
            }
        }
    }
}
