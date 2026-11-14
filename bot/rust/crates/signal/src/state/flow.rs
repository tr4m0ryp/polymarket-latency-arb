//! Spot trade flow (research/predict/feats/flow.py `TradeStream`): signed taker volume (buyer
//! taker +) decayed at 0.05 / 0.2 / 1 s, arrival intensity and big-trade count at 0.2 s.
use crate::features::names::{Row, ST_BIG, ST_SV005, ST_TN};

const TAUS: [f64; 3] = [0.05, 0.2, 1.0];

#[derive(Debug, Clone)]
pub struct TradeFlow {
    big_q: f64,
    pub t: Option<f64>,
    sv: [f64; 3],
    n: f64,
    big: f64,
}

impl Default for TradeFlow {
    fn default() -> Self {
        TradeFlow { big_q: 0.5, t: None, sv: [0.0; 3], n: 0.0, big: 0.0 }
    }
}

impl TradeFlow {
    pub fn update(&mut self, t: f64, q: f64, m: f64) {
        let sgn = if m > 0.0 { -1.0 } else { 1.0 };
        if let Some(t0) = self.t {
            let dt = t - t0;
            for (v, k) in self.sv.iter_mut().zip(TAUS) {
                *v *= (-dt / k).exp();
            }
            let d = (-dt / 0.2).exp();
            self.n *= d;
            self.big *= d;
        }
        for v in self.sv.iter_mut() {
            *v += sgn * q;
        }
        self.n += 1.0;
        self.big += sgn * if q >= self.big_q { 1.0 } else { 0.0 };
        self.t = Some(t);
    }

    pub fn features(&self, q: f64, depth: f64, f: &mut Row) {
        let Some(t) = self.t else { return };
        let dt = q - t;
        for (k, (v, tau)) in self.sv.iter().zip(TAUS).enumerate() {
            f[ST_SV005 + k] = v * (-dt / tau).exp() / depth;
        }
        f[ST_TN] = (self.n * (-dt / 0.2).exp() / 0.2).ln_1p();
        f[ST_BIG] = self.big * (-dt / 0.2).exp();
    }
}
