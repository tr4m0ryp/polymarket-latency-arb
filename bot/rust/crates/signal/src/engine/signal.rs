//! What the engine hands the live loop and the replay: one line per trigger candidate (the order
//! or the veto with everything logged) and the running counters.
use crate::engine::veto::Decision;
use crate::features::names::Row;
use crate::feed::event::Kind;

/// A value candidate on which the trigger fired: the order or the veto, with everything logged.
pub struct Signal {
    pub t: f64,
    pub kind: Kind,
    pub mkt: i64,
    pub slug: String,
    pub p_dmic: f64,
    pub s_dmic: f64,
    pub trig_side: f64,
    pub pu: f64,
    pub pdn: f64,
    pub edge: f64,
    pub side: f64,
    pub seen: f64,
    pub decision: Decision,
    /// gate prediction (NaN when the row was not gated: no gate configured, or v1 vetoed it)
    pub gate: f64,
    /// the gate's 7 book extras (research order, features::EXTRA) when it scored the row
    pub x: Option<[f32; 7]>,
    pub row: Box<Row>,
    pub feat_ns: u64,
    pub model_ns: u64,
}

#[derive(Debug, Default, Clone, serde::Serialize)]
pub struct Stats {
    pub events: u64,
    pub candidates: u64,
    pub triggers: u64,
    pub orders: u64,
}
