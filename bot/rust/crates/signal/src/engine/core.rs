//! The event loop body (btclat/paper/engine/core.py + arms/decide.py, veto arm only): update
//! state, decide whether this event is a value candidate (decision_times thinning), and on a
//! candidate whose leaders' trigger fires, build the row, score both sides and apply the veto.
//! Candidates without the trigger skip the row and the model: vtaker requires the trigger, so
//! the decisions are the same as the Python bot's, which scores every candidate.
use std::collections::HashMap;
use std::time::Instant;

use btl_model::Forest;

use crate::engine::gate::Gate;
use crate::engine::market::Ctx;
use crate::engine::signal::{Signal, Stats};
use crate::engine::veto::{self, Decision, VetoParams};
use crate::engine::world::World;
use crate::features::{extras, row, Vectorizer};
use crate::feed::event::{Ev, Kind};
use crate::num::pyround3;

pub struct ArmState {
    vt_last_t: f64,
    vt_last_m: f64,
    vt_prev_q: Option<f64>,
    fired: f64,
}

impl Default for ArmState {
    fn default() -> Self {
        ArmState { vt_last_t: f64::NEG_INFINITY, vt_last_m: f64::NAN, vt_prev_q: None, fired: f64::NEG_INFINITY }
    }
}

pub struct Engine {
    pub world: World,
    pub params: VetoParams,
    forest: Forest,
    vec: Vectorizer,
    /// hold-aware gate on the rows v1 keeps (None: plain v1 veto)
    gate: Option<Gate>,
    arms: HashMap<i64, ArmState>,
    last_drop: f64,
    xu: Vec<f64>,
    xd: Vec<f64>,
    pub stats: Stats,
}

impl Engine {
    pub fn new(ctx: Ctx, forest: Forest, vec: Vectorizer, params: VetoParams, gate: Option<Gate>) -> Engine {
        let n = vec.vf.len();
        Engine { world: World::new(ctx), params, forest, vec, gate, arms: HashMap::new(), last_drop: 0.0,
            xu: vec![0.0; n], xd: vec![0.0; n], stats: Stats::default() }
    }

    /// Engine.tradable: settlement inputs present (decided once, after start + 1).
    fn tradable(&mut self, i: usize, t: f64) -> bool {
        let w = &mut self.world;
        let m = &mut w.mkts[i];
        if let Some(ok) = m.ok {
            return ok;
        }
        if t < m.start + 1.0 {
            return false;
        }
        let st = &w.ctx.settle;
        let k = m.strike(st);
        let ok = st.first_t() <= m.start - 300.0 && !k.is_nan();
        m.ok = Some(ok);
        ok
    }

    pub fn on_event(&mut self, ev: &Ev) -> Option<Signal> {
        self.stats.events += 1;
        let (kind, mut m, flag) = self.world.apply(ev);
        let t = ev.t();
        match kind {
            Kind::Pb | Kind::Sb | Kind::St => m = self.world.active(t),
            Kind::Pm => {
                if let Some(i) = m {
                    let mk = &self.world.mkts[i];
                    let tr = pyround3(t);
                    if !(mk.start + 3.0 < tr && tr < mk.end - 5.0) {
                        m = None;
                    }
                }
            }
            _ => {}
        }
        let mut out = None;
        if let Some(i) = m {
            if self.world.ctx.perp.t.is_some() && self.tradable(i, t) {
                out = self.decide(kind, flag, t, i);
            }
        }
        if t - self.last_drop > 30.0 {
            self.world.drop_old(t);
            self.last_drop = t;
        }
        out
    }

    fn candidate(&mut self, kind: Kind, flag: bool, t: f64, mkt: i64) -> bool {
        if !matches!(kind, Kind::Pb | Kind::Sb | Kind::Pm) || (kind == Kind::Pm && !flag) {
            return false;
        }
        let mic = self.world.ctx.perp.lmic(t) * 1e4;
        let st = self.arms.entry(mkt).or_default();
        let keep = flag || kind == Kind::Pm || t - st.vt_last_t >= 0.02 || (mic - st.vt_last_m).abs() >= 0.002;
        if keep {
            st.vt_last_t = t;
            st.vt_last_m = mic;
            if st.vt_prev_q == Some(t) {
                return false;
            }
            st.vt_prev_q = Some(t);
        }
        keep
    }

    fn decide(&mut self, kind: Kind, flag: bool, t: f64, i: usize) -> Option<Signal> {
        let (start, end, mkt) = {
            let m = &self.world.mkts[i];
            (m.start, m.end, m.meta.start)
        };
        // NB: the market index is valid only within this event (drop_old runs after it)
        if !(start + 3.0 < t && t < end - 5.0) || !self.candidate(kind, flag, t, mkt) {
            return None;
        }
        self.stats.candidates += 1;
        if t > end - 60.0 {
            let w = &mut self.world;
            let m = &mut w.mkts[i];
            let n = m.lock.n_at(t);
            if n > 0 {
                m.lock.advance(&w.ctx.settle, t, n);
            }
        }
        let c = &self.world.ctx;
        let p_dmic = 1e4 * (c.perp.lmic(t) - c.perp.lmic(t - 0.1));
        let s_dmic = 1e4 * (c.spot.lmic(t) - c.spot.lmic(t - 0.1));
        let (fires, trig_side) = veto::trigger(&self.params, p_dmic, s_dmic);
        if !fires {
            return None;
        }
        self.stats.triggers += 1;
        let t0 = Instant::now();
        let w = &mut self.world;
        let r = Box::new(row(t, &mut w.ctx, &mut w.mkts[i]));
        let t1 = Instant::now();
        self.vec.sides(&r, &mut self.xu, &mut self.xd);
        let (pu, pdn) = (self.forest.predict(&self.xu), self.forest.predict(&self.xd));
        let (mut d, side, edge, seen) = veto::decide(&self.params, &r, p_dmic, s_dmic, pu, pdn);
        let (mut gate, mut x) = (f64::NAN, None);
        if let (Decision::Order, Some(g)) = (d, self.gate.as_mut()) {
            let ex = extras(&mut self.world.mkts[i].hist, t, side, seen);
            gate = g.score(if side > 0.0 { &self.xu } else { &self.xd }, edge, &ex);
            x = Some(ex);
            if !(gate >= g.tau) {
                d = Decision::Veto("gate");
            }
        }
        let t2 = Instant::now();
        let st = self.arms.entry(mkt).or_default();
        if d == Decision::Order {
            if t - st.fired >= self.params.refr {
                st.fired = t;
                self.stats.orders += 1;
            } else {
                d = Decision::Veto("refractory");
            }
        }
        let slug = self.world.mkts[i].meta.slug.clone();
        Some(Signal { t, kind, mkt, slug, p_dmic, s_dmic, trig_side, pu, pdn, edge, side, seen, decision: d, gate, x,
            row: r, feat_ns: (t1 - t0).as_nanos() as u64, model_ns: (t2 - t1).as_nanos() as u64 })
    }
}
