//! CLI defaults of `btclat-bot run`. PROVISIONAL (reports/bankroll-caps.md): the cap search was
//! stopped unfinished at the user's redirect to the pair strategy. These are the best stage-2
//! point on selection hours (v1, old hold) that met every ruin constraint, never scored on test
//! hours; its +0.5 c minimum edge is not implemented here. The floor halt is extra insurance.
pub const DEFAULT_SIZING: &str = "kelly";
pub const DEFAULT_FRAC: f64 = 0.01;
pub const DEFAULT_KELLY: f64 = 0.1;
pub const DEFAULT_MAX_SH: f64 = 500.0;
pub const DEFAULT_MARKET_FRAC: f64 = 0.10;
pub const DEFAULT_OPEN_FRAC: f64 = 0.25;
pub const DEFAULT_SIDE: &str = "any";
pub const DEFAULT_MAX_FILLS: u32 = 2;
pub const DEFAULT_DD_STOP: f64 = 0.15;
pub const DEFAULT_FLOOR: f64 = 0.5;
