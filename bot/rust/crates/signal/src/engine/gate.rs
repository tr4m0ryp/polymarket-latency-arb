//! Hold-aware gate on top of the v1 veto (research/vetohold/label: variant G, exported as e.g.
//! `v1h_G_h250x_L0`): on a row v1 keeps (trigger fires, gates pass, v1 >= margin on the trigger
//! side), predict the 250 ms-hold value from [v1's trigger-side inputs, v1 value, the 7 book
//! extras] and send only if it is >= tau. Inputs are rounded to float32 first: research stores
//! the label rows as float32 and both trained and scored the gate on them.
use anyhow::{bail, Result};
use btl_model::Forest;

use crate::features::EXTRA;

pub struct Gate {
    forest: Forest,
    pub tau: f64,
    n_base: usize,
    x: Vec<f64>,
}

impl Gate {
    /// `vf`: the gate's input list, which must be the base model's list + v1_value + EXTRA.
    pub fn new(forest: Forest, vf: &[String], base_vf: &[String], tau: f64) -> Result<Gate> {
        let n = base_vf.len();
        let tail: Vec<&str> = std::iter::once("v1_value").chain(EXTRA).collect();
        if vf.len() != n + tail.len() || vf[..n] != *base_vf || vf[n..].iter().map(|s| s.as_str()).ne(tail) {
            bail!("refusing: gate inputs are not [base model inputs, v1_value, {EXTRA:?}]");
        }
        if !tau.is_finite() || forest.n_features != vf.len() {
            bail!("refusing: gate tau {tau} or input count {} invalid", forest.n_features);
        }
        Ok(Gate { forest, tau, n_base: n, x: vec![0.0; vf.len()] })
    }

    /// Gate prediction for the trigger side: xs = v1's input vector of that side, v1 its value.
    pub fn score(&mut self, xs: &[f64], v1: f64, ex: &[f32; 7]) -> f64 {
        for (d, &s) in self.x.iter_mut().zip(&xs[..self.n_base]) {
            *d = s as f32 as f64;
        }
        self.x[self.n_base] = v1 as f32 as f64;
        for (d, &e) in self.x[self.n_base + 1..].iter_mut().zip(ex) {
            *d = e as f64;
        }
        self.forest.predict(&self.x)
    }
}
