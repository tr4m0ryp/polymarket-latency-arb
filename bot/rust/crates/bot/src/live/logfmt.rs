//! Hot-path log lines, pre-serialized for `Logger::log_raw` (feed receipts) and the signal line.
use serde_json::{json, Map, Value};
use std::fmt::Write;

use btl_signal::feed::Ev;
use btl_signal::features::names;
use btl_signal::Signal;

use crate::live::msg::Recv;

fn num(x: f64) -> String {
    if x.is_finite() { format!("{x}") } else { "null".into() }
}

/// `feed` fields of one accepted message (bb / ba / top for Polymarket after applying).
pub fn feed(ev: &Ev, r: &Recv, pm_top: Option<(i32, i32, bool)>) -> String {
    let mut s = String::with_capacity(160);
    let t = ev.t();
    match ev {
        Ev::Pb(b) | Ev::Sb(b) => {
            let src = if matches!(ev, Ev::Pb(_)) { "pb" } else { "sb" };
            let _ = write!(s, r#""src":"{src}","conn":{},"t":{t},"vts":{},"b":{},"a":{},"bq":{},"aq":{},"u":{}"#,
                r.conn, num(b.tt), b.b, b.a, b.bq, b.aq, b.u);
        }
        Ev::St(x) | Ev::Pt(x) => {
            let src = if matches!(ev, Ev::St(_)) { "st" } else { "pt" };
            let _ = write!(s, r#""src":"{src}","conn":{},"t":{t},"vts":{},"px":{},"q":{},"m":{},"id":{}"#,
                r.conn, num(x.tt), x.px, x.q, x.m, x.id);
        }
        Ev::Pm(p) => {
            let (bb, ba, top) = pm_top.unwrap_or((0, 100, false));
            let _ = write!(s, r#""src":"pm","conn":{},"t":{t},"vts":{},"mkt":{},"snap":{},"n":{},"bb":{bb},"ba":{ba},"top":{top}"#,
                r.conn, num(p.ts), p.mkt, p.snap, p.chg.len());
        }
        Ev::Mk(_) => {}
    }
    s
}

pub fn features(row: &names::Row) -> Value {
    let mut m = Map::with_capacity(names::N);
    for (k, v) in names::all().into_iter().zip(row.iter()) {
        m.insert(k, if v.is_finite() { json!(v) } else { Value::Null });
    }
    Value::Object(m)
}

pub fn signal(s: &Signal, sig: &str, vts: f64, decision: &str, reason: Option<&str>) -> Value {
    let r = &s.row;
    let f = |x: f64| if x.is_finite() { Some(x) } else { None };
    json!({"sig": sig, "slug": s.slug, "t": s.t, "src": s.kind.as_str(), "vts": f(vts), "trig_side": f(s.trig_side),
        "p_dmic": f(s.p_dmic), "s_dmic": f(s.s_dmic), "pu": s.pu, "pdn": s.pdn, "edge": f(s.edge), "side": s.side,
        "seen": f(s.seen), "bb": r[names::PM_BB], "ba": r[names::PM_BA], "secs_left": r[names::SECS_LEFT],
        "decision": decision, "reason": reason, "gate": f(s.gate), "x": s.x.map(|x| x.map(|v| v as f64)),
        "feat_ns": s.feat_ns, "model_ns": s.model_ns, "features": features(r)})
}
