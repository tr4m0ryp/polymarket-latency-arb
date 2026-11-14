//! Order intent and open position records.
use crate::limits::fee;

#[derive(Debug, Clone, PartialEq)]
pub struct Intent {
    pub arm: String,
    pub slug: String,
    pub token: String,
    pub up: bool,
    pub price: f64,
    pub size: f64,
    pub end: f64,
}

impl Intent {
    pub fn notional(&self) -> f64 {
        self.price * self.size
    }

    /// Most this order can lose: notional plus taker fee.
    pub fn worst(&self) -> f64 {
        self.notional() + fee(self.price, self.size)
    }
}

#[derive(Debug, Clone, PartialEq)]
pub struct Pos {
    pub slug: String,
    pub up: bool,
    pub end: f64,
    pub sh: f64,
    pub cost: f64,
    pub fee: f64,
}
