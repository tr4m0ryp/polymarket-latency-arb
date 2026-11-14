//! Order inputs and the signed result.

use std::fmt;

#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash)]
pub enum Side {
    Buy,
    Sell,
}

impl Side {
    pub fn as_str(self) -> &'static str {
        match self {
            Side::Buy => "BUY",
            Side::Sell => "SELL",
        }
    }

    /// uint8 value in the signed struct (BUY 0, SELL 1).
    pub fn code(self) -> u8 {
        match self {
            Side::Buy => 0,
            Side::Sell => 1,
        }
    }
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash)]
pub enum OrderType {
    Fak,
    Fok,
    Gtc,
    Gtd,
}

impl OrderType {
    pub fn as_str(self) -> &'static str {
        match self {
            OrderType::Fak => "FAK",
            OrderType::Fok => "FOK",
            OrderType::Gtc => "GTC",
            OrderType::Gtd => "GTD",
        }
    }
}

impl fmt::Display for OrderType {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str(self.as_str())
    }
}

/// A limit order on a tick-0.01, non-neg-risk market. `expiration` (unix s, server clock) is
/// for GTD only (the venue wants >= now + 60 s) and must be 0 for the other types.
#[derive(Clone, Debug, PartialEq)]
pub struct OrderSpec {
    pub token_id: String,
    pub price: f64,
    pub size: f64,
    pub side: Side,
    pub order_type: OrderType,
    pub post_only: bool,
    pub expiration: u64,
}

/// The exact JSON to POST /order (and HMAC-sign), with its build timings.
#[derive(Clone, Debug)]
pub struct SignedOrder {
    pub body: String,
    /// EIP-712 hashing + secp256k1 signature only.
    pub sign_ns: u64,
    /// Whole build: amounts, hashing, signature, JSON.
    pub build_ns: u64,
    pub maker_amount: u64,
    pub taker_amount: u64,
    pub salt: u64,
    pub timestamp_ms: u64,
    pub spec: OrderSpec,
}
