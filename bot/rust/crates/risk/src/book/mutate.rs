//! State changes: positions, reservations, fills, resolution.
use super::ledger::{Leg, Row};
use super::{Intent, Pos, RiskBook};

impl RiskBook {
    // state changes ---------------------------------------------------------------------
    pub(super) fn add(&mut self, l: &Leg) {
        let p = self
            .pos
            .entry((l.slug.clone(), l.token.clone()))
            .or_insert_with(|| Pos {
                slug: l.slug.clone(),
                up: l.up,
                end: l.end,
                sh: 0.0,
                cost: 0.0,
                fee: 0.0,
            });
        p.sh += l.sh;
        p.cost += l.cost;
        p.fee += l.fee;
    }

    /// Drop the market's positions; returns the payout owed ($1 per winning share).
    pub(super) fn resolve_in_memory(&mut self, slug: &str, outcome: f64) -> f64 {
        let keys: Vec<_> = self.pos.keys().filter(|k| k.0 == slug).cloned().collect();
        let mut pay = 0.0;
        for k in keys {
            if let Some(p) = self.pos.remove(&k) {
                let won = if p.up { outcome } else { 1.0 - outcome };
                self.realised += p.sh * won - p.cost - p.fee;
                pay += p.sh * won;
            }
        }
        self.fills.retain(|k, _| k.0 != slug);
        self.first_side.remove(slug);
        pay
    }

    /// Order goes out: counts against exposure (worst case) and the hourly budget until
    /// `release`. `cid` is the client order id (signature).
    pub fn reserve(&mut self, cid: &str, it: &Intent, t: f64) {
        self.inflight.insert(cid.to_string(), it.worst());
        self.inflight_meta.insert(cid.to_string(), (it.slug.clone(), it.up, it.size));
        self.sends.push_back(t);
        self.last_send.insert(it.slug.clone(), t);
        self.last_send.retain(|_, &mut s| s > t - 3600.0);
        while self.sends.front().is_some_and(|&s| s <= t - 3600.0) {
            self.sends.pop_front();
        }
        if !t.is_finite() {
            return self.stop("ledger_io: non-finite send time".to_string());
        }
        self.log(Row::Send {
            t,
            oid: cid.to_string(),
        });
    }

    /// Final ack (fill or not): the order is no longer in flight.
    pub fn release(&mut self, cid: &str) {
        self.inflight.remove(cid);
        self.inflight_meta.remove(cid);
    }

    pub fn fill(&mut self, it: &Intent, sh: f64, cost: f64, fee: f64) {
        if sh <= 0.0 {
            return;
        }
        let l = Leg {
            slug: it.slug.clone(),
            token: it.token.clone(),
            up: it.up,
            end: it.end,
            sh,
            cost,
            fee,
        };
        self.add(&l);
        *self.fills.entry((it.slug.clone(), it.up)).or_default() += 1;
        self.first_side.entry(it.slug.clone()).or_insert(it.up);
        if let Some(b) = self.balance.as_mut() {
            *b -= cost + fee; // until the next venue balance read
        }
        if ![sh, cost, fee].iter().all(|v| v.is_finite()) {
            return self.stop("ledger_io: non-finite fill".to_string());
        }
        self.log(Row::Fill(l));
    }

    pub fn resolve(&mut self, slug: &str, outcome: f64) {
        if self.pos.keys().any(|k| k.0 == slug) {
            self.claim += self.resolve_in_memory(slug, outcome);
            self.log(Row::Resolve {
                slug: slug.to_string(),
                outcome,
            });
        }
    }

    /// Our book's mid for a token (positions are marked to it; at cost while unknown).
    pub fn mark(&mut self, token: &str, mid: f64) {
        self.marks.insert(token.to_string(), mid);
    }
}
