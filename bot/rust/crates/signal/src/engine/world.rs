//! btclat/paper/engine/world.py: shared state plus the markets in insertion order; `apply`
//! returns what changed (the flag: mid changed for Binance books, top changed for a Polymarket
//! book, last trade price changed for a spot trade).
use crate::engine::market::{Ctx, MarketCtx};
use crate::feed::event::{Ev, Kind};

pub struct World {
    pub ctx: Ctx,
    pub mkts: Vec<MarketCtx>,
    pub n_ev: u64,
}

impl World {
    pub fn new(ctx: Ctx) -> World {
        World { ctx, mkts: Vec::new(), n_ev: 0 }
    }

    pub fn idx(&self, start: i64) -> Option<usize> {
        self.mkts.iter().position(|m| m.meta.start == start)
    }

    pub fn add_market(&mut self, m: &crate::engine::MarketMeta) -> usize {
        match self.idx(m.start) {
            Some(i) => i,
            None => {
                self.mkts.push(MarketCtx::new(m.clone()));
                self.mkts.len() - 1
            }
        }
    }

    pub fn drop_old(&mut self, now: f64) {
        self.mkts.retain(|m| m.end + 120.0 >= now);
    }

    /// The market whose decision window (start + 3, end - 5) contains t.
    pub fn active(&self, t: f64) -> Option<usize> {
        self.mkts.iter().position(|m| m.start + 3.0 < t && t < m.end - 5.0)
    }

    /// Update state; (kind, market index or None, flag).
    pub fn apply(&mut self, ev: &Ev) -> (Kind, Option<usize>, bool) {
        self.n_ev += 1;
        let c = &mut self.ctx;
        match ev {
            Ev::Pb(b) => {
                c.perp.update(b.t, b.b, b.a, b.bq, b.aq);
                (Kind::Pb, None, c.perp.mid_changed)
            }
            Ev::Sb(b) => {
                c.spot.update(b.t, b.b, b.a, b.bq, b.aq);
                (Kind::Sb, None, c.spot.mid_changed)
            }
            Ev::St(x) => {
                c.flow.update(x.t, x.q, x.m);
                c.settle.update(x.t, x.tt, x.px);
                let s = &c.settle;
                (Kind::St, None, !s.prev_lpx.is_nan() && s.prev_lpx != s.last_lpx)
            }
            Ev::Pt(_) => (Kind::Pt, None, false),
            Ev::Pm(p) => match self.idx(p.mkt) {
                None => (Kind::Pm, None, false),
                Some(i) => {
                    let m = &mut self.mkts[i];
                    let ch = m.book.apply(p.t, p.ts, p.snap, &p.chg);
                    m.hist.on_msg(p.t, p.ts, p.snap, &p.chg);
                    (Kind::Pm, Some(i), ch)
                }
            },
            Ev::Mk(t_meta) => (Kind::Mk, Some(self.add_market(&t_meta.1)), false),
        }
    }
}
