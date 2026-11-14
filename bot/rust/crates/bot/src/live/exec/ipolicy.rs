//! The limit offset i (limit = seen ask + i). Binding default: i = 0 (orders at the seen ask,
//! never above: reports/live-hold.md). Any i > 0 needs --allow-i-positive and is logged loudly;
//! the randomized-i experiment needs --i-random-experiment; `predicted` is the hook for a
//! slippage model (trait `IPolicy`) and is refused until one is plugged in.
use anyhow::{bail, Result};
use rand::Rng;

use crate::cli::{IMode, RunArgs};
use btl_signal::Signal;

/// Hard ceiling on i whatever the flags say.
pub const I_MAX: f64 = 0.05;

pub trait IPolicy: Send {
    fn mode(&self) -> &'static str;
    /// i ($) for this signal's order.
    fn choose(&mut self, sig: &Signal) -> f64;
}

pub struct Fixed(pub f64);

impl IPolicy for Fixed {
    fn mode(&self) -> &'static str {
        "fixed"
    }
    fn choose(&mut self, _: &Signal) -> f64 {
        self.0
    }
}

pub struct Random {
    pub set: Vec<f64>,
    rng: rand::rngs::StdRng,
}

impl IPolicy for Random {
    fn mode(&self) -> &'static str {
        "random"
    }
    fn choose(&mut self, _: &Signal) -> f64 {
        self.set[self.rng.gen_range(0..self.set.len())]
    }
}

fn check_i(i: f64) -> Result<()> {
    if !(0.0..=I_MAX).contains(&i) || (i * 100.0 - (i * 100.0).round()).abs() > 1e-9 {
        bail!("refusing: i = {i} must be a multiple of 0.01 in [0, {I_MAX}]");
    }
    Ok(())
}

/// The policy plus the loud warnings to print and log at start.
pub fn from_args(a: &RunArgs) -> Result<(Box<dyn IPolicy>, Vec<String>)> {
    let mut warn = Vec::new();
    match a.i_mode {
        IMode::Fixed => {
            check_i(a.i)?;
            if a.i > 0.0 {
                if !a.allow_i_positive {
                    bail!("refusing: --i {} > 0 buys above the seen ask (binding default i = 0); add --allow-i-positive", a.i);
                }
                warn.push(format!("WARNING: limit offset i = {} > 0: every order pays up to {} above the seen ask", a.i, a.i));
            }
            Ok((Box::new(Fixed(a.i)), warn))
        }
        IMode::Random => {
            if !a.i_random_experiment {
                bail!("refusing: --i-mode random is the randomized-i experiment; add --i-random-experiment");
            }
            if a.i_set.is_empty() {
                bail!("refusing: --i-mode random needs --i-set (e.g. 0,0.01)");
            }
            for &i in &a.i_set {
                check_i(i)?;
            }
            warn.push(format!("WARNING: randomized-i experiment: i drawn uniformly from {:?} per order", a.i_set));
            if a.i_set.iter().any(|&i| i > 0.0) {
                warn.push("WARNING: the experiment set contains i > 0 (orders above the seen ask)".into());
            }
            Ok((Box::new(Random { set: a.i_set.clone(), rng: rand::SeedableRng::from_entropy() }), warn))
        }
        IMode::Predicted => bail!("refusing: --i-mode predicted has no predictor plugged in yet (implement IPolicy)"),
    }
}

/// limit = seen + i rounded to the 0.01 tick, capped at 0.99.
pub fn limit(seen: f64, i: f64) -> f64 {
    (((seen + i).min(0.99)) * 100.0).round() / 100.0
}
