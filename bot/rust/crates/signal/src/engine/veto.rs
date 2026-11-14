//! The veto arm `vt_v1_m0.02_trigger` (research/predict/sim/rules.py `vtaker` with
//! require="trigger", params of research/predict/sim/arms/sel1.py): the leaders' perp
//! microprice trigger (|perp dmic over 0.1 s| >= 0.002 bp, side = sign(perp + spot dmic)) kept
//! only when the value model's best side agrees and predicts >= margin $/share.
use crate::features::names::{Row, PM_BA, PM_BB, PM_MID, SECS_LEFT};
use crate::num::{npsign, pymax};

#[derive(Debug, Clone, Copy, serde::Serialize)]
pub struct VetoParams {
    pub margin: f64,
    pub thr: f64,
    pub refr: f64,
    pub band: (f64, f64),
    pub tleft: f64,
    pub fav_max: f64,
}

impl Default for VetoParams {
    fn default() -> Self {
        VetoParams { margin: 0.02, thr: 0.002, refr: 0.2, band: (0.05, 0.95), tleft: 20.0, fav_max: 0.97 }
    }
}

#[derive(Debug, Clone, Copy, PartialEq)]
pub enum Decision {
    Order,
    Veto(&'static str),
}

impl Decision {
    pub fn reason(&self) -> Option<&'static str> {
        match self {
            Decision::Order => None,
            Decision::Veto(r) => Some(r),
        }
    }
}

/// The trigger alone (no model): (fires, trigger side).
#[inline]
pub fn trigger(p: &VetoParams, p_dmic: f64, s_dmic: f64) -> (bool, f64) {
    (p_dmic.abs() >= p.thr, npsign(p_dmic + s_dmic))
}

/// vtaker on one row: (decision before refractory, side, edge, seen).
pub fn decide(p: &VetoParams, f: &Row, p_dmic: f64, s_dmic: f64, pu: f64, pdn: f64) -> (Decision, f64, f64, f64) {
    let side = if pu >= pdn { 1.0 } else { -1.0 };
    let edge = if pu.is_nan() || pdn.is_nan() { f64::NAN } else { pu.max(pdn) };
    let (bb, ba, mid) = (f[PM_BB], f[PM_BA], f[PM_MID]);
    let seen = if side > 0.0 { ba / 100.0 } else { 1.0 - bb / 100.0 };
    if !(pymax(pu, pdn) >= p.margin) {
        return (Decision::Veto("margin"), side, edge, seen);
    }
    let (fires, tside) = trigger(p, p_dmic, s_dmic);
    if !fires || tside != side {
        return (Decision::Veto(if fires { "side" } else { "trigger" }), side, edge, seen);
    }
    let gate = if !(seen >= p.band.0 && seen <= p.band.1) {
        Some("gate_band")
    } else if !(f[SECS_LEFT] >= p.tleft) {
        Some("gate_tleft")
    } else if !(mid.max(1.0 - mid) <= p.fav_max) || mid.is_nan() {
        Some("gate_fav")
    } else if !(bb > 0.0 && ba < 100.0 && mid.is_finite()) {
        Some("gate_book")
    } else {
        None
    };
    match gate {
        Some(g) => (Decision::Veto(g), side, edge, seen),
        None => (Decision::Order, side, edge, seen),
    }
}
