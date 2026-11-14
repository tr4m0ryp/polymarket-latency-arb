//! Event types. Times are SNTP/system-clock receipt times in seconds (t_ns / 1e9, as Python).
use crate::engine::market::MarketMeta;
use crate::state::pm::Chg;

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum Kind {
    Pb,
    Sb,
    St,
    Pt,
    Pm,
    Mk,
}

impl Kind {
    pub fn as_str(&self) -> &'static str {
        match self {
            Kind::Pb => "pb",
            Kind::Sb => "sb",
            Kind::St => "st",
            Kind::Pt => "pt",
            Kind::Pm => "pm",
            Kind::Mk => "mk",
        }
    }
}

/// bookTicker: tt = Binance transaction time (s; NaN for spot), sizes float32-rounded.
#[derive(Debug, Clone, Copy)]
pub struct Book {
    pub t: f64,
    pub tt: f64,
    pub b: f64,
    pub a: f64,
    pub bq: f64,
    pub aq: f64,
    pub u: u64,
}

/// trade: m = 1.0 if the buyer is the maker.
#[derive(Debug, Clone, Copy)]
pub struct Trade {
    pub t: f64,
    pub tt: f64,
    pub px: f64,
    pub q: f64,
    pub m: f64,
    pub id: u64,
}

/// Up-token book change of market `mkt` (= its start, unique per 5m market); ts = venue s.
#[derive(Debug, Clone)]
pub struct Pm {
    pub t: f64,
    pub ts: f64,
    pub mkt: i64,
    pub snap: bool,
    pub chg: Vec<Chg>,
}

#[derive(Debug, Clone)]
pub enum Ev {
    Pb(Book),
    Sb(Book),
    St(Trade),
    Pt(Trade),
    Pm(Pm),
    Mk(Box<(f64, MarketMeta)>),
}

impl Ev {
    pub fn t(&self) -> f64 {
        match self {
            Ev::Pb(b) | Ev::Sb(b) => b.t,
            Ev::St(x) | Ev::Pt(x) => x.t,
            Ev::Pm(p) => p.t,
            Ev::Mk(m) => m.0,
        }
    }

    pub fn kind(&self) -> Kind {
        match self {
            Ev::Pb(_) => Kind::Pb,
            Ev::Sb(_) => Kind::Sb,
            Ev::St(_) => Kind::St,
            Ev::Pt(_) => Kind::Pt,
            Ev::Pm(_) => Kind::Pm,
            Ev::Mk(_) => Kind::Mk,
        }
    }

    /// The venue / exchange stamp (s) of the event, NaN when it has none.
    pub fn venue_t(&self) -> f64 {
        match self {
            Ev::Pb(b) | Ev::Sb(b) => b.tt,
            Ev::St(x) | Ev::Pt(x) => x.tt,
            Ev::Pm(p) => p.ts,
            Ev::Mk(_) => f64::NAN,
        }
    }
}
