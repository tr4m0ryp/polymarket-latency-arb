//! Hard constants. Module constants, not config defaults: the CLI may only LOWER a limit.

pub const HARD_MAX_SHARES: f64 = 1e9; // uncapped (user 2026-10-14): size is the model design (60 sh)
pub const HARD_MAX_NOTIONAL: f64 = 1e9; // uncapped (user 2026-10-14)
pub const HARD_MAX_EXPOSURE: f64 = 1e9; // uncapped (user 2026-10-14): the wallet balance is the limit
pub const HARD_LOSS_CAP: f64 = 1e9; // uncapped (user 2026-10-14)
pub const HARD_MAX_ORDERS_HOUR: u32 = u32::MAX; // uncapped (user 2026-10-14): every veto order goes out
/// Orders in flight (reserve until the final ack). New for the Rust taker.
pub const HARD_MAX_INFLIGHT: u32 = 64; // effectively uncapped: concurrent orders as in the simulator
/// Seconds between sent orders on one market, floor (smaller is looser). New for the Rust taker.
pub const HARD_MIN_REFRACTORY_S: f64 = 0.2;
pub const VENUE_MIN_SHARES: f64 = 5.0;
pub const VENUE_MIN_NOTIONAL: f64 = 1.0; // $ marketable BUY (third-party figure)
pub const TICK: f64 = 0.01;
pub const FEE_RATE: f64 = 0.07; // taker fee per share = FEE_RATE * p * (1 - p), our 0% tier

/// Taker fee for `shares` at price `p`.
pub fn fee(p: f64, shares: f64) -> f64 {
    FEE_RATE * p * (1.0 - p) * shares
}
