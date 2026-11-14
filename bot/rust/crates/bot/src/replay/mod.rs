//! Replay mode: the live decision engine over recorded raw tape, no network, no orders.
//! Writes `<out>/decisions.jsonl` (one line per order of the veto arm: t, slug, side, limit,
//! seen, pred_up, pred_dn, src, gate) and `<out>/signals.jsonl` (every trigger candidate with its
//! veto reason; gated rows add the gate prediction and its 7 book extras `x`); with
//! `--expect <python decisions.jsonl>` prints the decision parity.
pub mod compare;
pub mod source;

use anyhow::Result;
use serde_json::json;
use std::io::Write;
use std::path::Path;
use std::time::Instant;

use btl_signal::engine::{Decision, Engine};

pub struct Opts<'a> {
    pub root: &'a Path,
    pub hours: Vec<i64>,
    pub out: &'a Path,
    pub i: f64,
    pub expect: Option<&'a Path>,
    pub dump_rows: bool,
}

pub fn run(mut eng: Engine, model: serde_json::Value, o: Opts) -> Result<serde_json::Value> {
    std::fs::create_dir_all(o.out)?;
    let mut dec = std::io::BufWriter::new(std::fs::File::create(o.out.join("decisions.jsonl"))?);
    let mut sig = std::io::BufWriter::new(std::fs::File::create(o.out.join("signals.jsonl"))?);
    let (mut feat_ns, mut model_ns) = (Vec::new(), Vec::new());
    let wall = Instant::now();
    let mut err: Option<std::io::Error> = None;
    let n = source::replay(o.root, &o.hours, |ev| {
        let Some(s) = eng.on_event(ev) else { return };
        feat_ns.push(s.feat_ns);
        model_ns.push(s.model_ns);
        let m = &s;
        let reason = s.decision.reason();
        let line = json!({"t": s.t, "slug": m.slug, "src": s.kind.as_str(), "p_dmic": s.p_dmic, "s_dmic": s.s_dmic,
            "trig_side": s.trig_side, "pred_up": s.pu, "pred_dn": s.pdn, "side": s.side, "seen": s.seen,
            "decision": if reason.is_none() { "order" } else { "veto" }, "reason": reason});
        let mut line = line;
        if let Some(x) = s.x {
            line["gate"] = json!(s.gate);
            line["x"] = json!(x.map(|v| v as f64));
        }
        if o.dump_rows {
            line["features"] = crate::live::logfmt::features(&s.row);
        }
        let r1 = writeln!(sig, "{line}");
        let r2 = if s.decision == Decision::Order {
            let limit = (s.seen + o.i).min(0.99);
            let gate = if s.gate.is_nan() { None } else { Some(s.gate) };
            writeln!(dec, "{}", json!({"t": s.t, "slug": m.slug, "side": s.side, "limit": limit, "seen": s.seen,
                "pred_up": s.pu, "pred_dn": s.pdn, "src": s.kind.as_str(), "gate": gate}))
        } else { Ok(()) };
        if let Err(e) = r1.and(r2) {
            err.get_or_insert(e);
        }
    })?;
    if let Some(e) = err {
        return Err(e.into());
    }
    dec.flush()?;
    sig.flush()?;
    let mut st = json!({"root": o.root, "hours": o.hours, "events": n, "wall_s": wall.elapsed().as_secs_f64(),
        "stats": eng.stats, "model": model, "i": o.i,
        "feat_us": pct(&mut feat_ns), "model_us": pct(&mut model_ns)});
    if let Some(p) = o.expect {
        st["parity"] = compare::compare(p, &o.out.join("decisions.jsonl"))?;
        let g = p.with_file_name("gate_rows.jsonl");
        if g.exists() {
            st["gate_parity"] = compare::compare_gate(&g, &o.out.join("signals.jsonl"))?;
        }
    }
    std::fs::write(o.out.join("replay.json"), serde_json::to_string_pretty(&st)?)?;
    Ok(st)
}

pub fn pct(v: &mut [u64]) -> serde_json::Value {
    if v.is_empty() {
        return json!(null);
    }
    v.sort_unstable();
    let at = |p: f64| v[((v.len() - 1) as f64 * p).round() as usize] as f64 / 1e3;
    json!({"n": v.len(), "p50": at(0.5), "p90": at(0.9), "p99": at(0.99), "max": at(1.0)})
}
