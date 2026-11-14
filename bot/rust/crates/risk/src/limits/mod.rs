//! [`Limits`]: tunable caps that can only be tightened relative to the hard constants.
mod hard;

pub use hard::*;

use thiserror::Error;

#[derive(Debug, Clone, PartialEq, Error)]
#[error("{0}")]
pub struct LimitError(pub String);

#[derive(Debug, Clone, Copy, PartialEq)]
pub struct Limits {
    pub max_shares: f64,
    pub max_notional: f64,
    pub max_exposure: f64,
    pub loss_cap: f64,
    pub max_orders_hour: u32,
    pub max_inflight: u32,
    pub min_refractory_s: f64,
}

/// Requested tightenings for [`Limits::lowered`]; `None` keeps the current value.
#[derive(Debug, Clone, Copy, Default)]
pub struct LimitOverrides {
    pub max_shares: Option<f64>,
    pub max_notional: Option<f64>,
    pub max_exposure: Option<f64>,
    pub loss_cap: Option<f64>,
    pub max_orders_hour: Option<u32>,
    pub max_inflight: Option<u32>,
    pub min_refractory_s: Option<f64>,
}

impl Default for Limits {
    fn default() -> Self {
        Limits {
            max_shares: HARD_MAX_SHARES,
            max_notional: HARD_MAX_NOTIONAL,
            max_exposure: HARD_MAX_EXPOSURE,
            loss_cap: HARD_LOSS_CAP,
            max_orders_hour: HARD_MAX_ORDERS_HOUR,
            max_inflight: HARD_MAX_INFLIGHT,
            min_refractory_s: HARD_MIN_REFRACTORY_S,
        }
    }
}

fn bad(name: &str, v: f64, hard: f64) -> LimitError {
    LimitError(format!(
        "limit {name}={v} is looser than the hard limit {hard}; refusing"
    ))
}

/// `up_is_loose`: a value above `hard` is looser (everything except the refractory floor).
fn ok(name: &str, v: f64, hard: f64, up_is_loose: bool) -> Result<(), LimitError> {
    let loose = if up_is_loose { v > hard } else { v < hard };
    if v.is_nan() || v <= 0.0 || loose {
        return Err(bad(name, v, hard));
    }
    Ok(())
}

impl Limits {
    /// A copy with some limits tightened. Loosening one past its hard value is refused.
    pub fn lowered(&self, o: LimitOverrides) -> Result<Limits, LimitError> {
        let out = Limits {
            max_shares: o.max_shares.unwrap_or(self.max_shares),
            max_notional: o.max_notional.unwrap_or(self.max_notional),
            max_exposure: o.max_exposure.unwrap_or(self.max_exposure),
            loss_cap: o.loss_cap.unwrap_or(self.loss_cap),
            max_orders_hour: o.max_orders_hour.unwrap_or(self.max_orders_hour),
            max_inflight: o.max_inflight.unwrap_or(self.max_inflight),
            min_refractory_s: o.min_refractory_s.unwrap_or(self.min_refractory_s),
        };
        out.checked()
    }

    /// Re-validate every value against the hard constants (an edited `Limits` is refused).
    pub fn checked(self) -> Result<Limits, LimitError> {
        ok("max_shares", self.max_shares, HARD_MAX_SHARES, true)?;
        ok("max_notional", self.max_notional, HARD_MAX_NOTIONAL, true)?;
        ok("max_exposure", self.max_exposure, HARD_MAX_EXPOSURE, true)?;
        ok("loss_cap", self.loss_cap, HARD_LOSS_CAP, true)?;
        ok(
            "max_orders_hour",
            self.max_orders_hour as f64,
            HARD_MAX_ORDERS_HOUR as f64,
            true,
        )?;
        ok(
            "max_inflight",
            self.max_inflight as f64,
            HARD_MAX_INFLIGHT as f64,
            true,
        )?;
        ok(
            "min_refractory_s",
            self.min_refractory_s,
            HARD_MIN_REFRACTORY_S,
            false,
        )?;
        Ok(self)
    }
}
