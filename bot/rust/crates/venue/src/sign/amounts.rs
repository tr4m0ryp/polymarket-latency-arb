//! Order amounts for tick 0.01 (RoundConfig price 2, size 2, amount 4), reproducing
//! py_clob_client_v2 `OrderBuilder.get_order_amounts` bit for bit.
//!
//! The Python works on IEEE doubles: `round` is round-half-even, `floor(x * 10**d) / 10**d` is an
//! int/int true division (correctly rounded, like an f64 division of exact operands), and
//! `decimal_places` reads the shortest round-trip repr (`Decimal(str(x))`). Every step below is
//! the same IEEE operation in the same order, so the results are identical, not approximate;
//! tests/amounts.rs checks the full price x size grid against Python-generated vectors.

use anyhow::{bail, Result};

use crate::types::Side;

const PRICE_DP: i32 = 2;
const SIZE_DP: i32 = 2;
const AMOUNT_DP: u32 = 4;

#[inline]
fn p10(d: i32) -> f64 {
    10f64.powi(d) // exact for 0 <= d <= 22, same value as Python's int 10**d converted to float
}

#[inline]
fn round_down(x: f64, d: i32) -> f64 {
    (x * p10(d)).floor() / p10(d)
}

#[inline]
fn round_normal(x: f64, d: i32) -> f64 {
    (x * p10(d)).round_ties_even() / p10(d)
}

#[inline]
fn round_up(x: f64, d: i32) -> f64 {
    (x * p10(d)).ceil() / p10(d)
}

/// `abs(Decimal(repr(x)).as_tuple().exponent)`: CPython's repr is the shortest round-trip
/// digit string, in fixed notation for decimal exponents -4..=15 (always with a fractional
/// part, "5.0") and scientific otherwise. Rust's `{:e}` yields the same shortest digits.
pub fn decimal_places(x: f64) -> u32 {
    if x == 0.0 || !x.is_finite() {
        return 1; // repr "0.0"; non-finite never reaches here from valid orders
    }
    let s = format!("{:e}", x.abs());
    let (mant, exp) = s.split_once('e').unwrap_or((&s, "0"));
    let e: i64 = exp.parse().unwrap_or(0);
    let n = mant.bytes().filter(|b| b.is_ascii_digit()).count() as i64;
    if (-4..16).contains(&e) {
        (n - 1 - e).max(1) as u32
    } else {
        (e - (n - 1)).unsigned_abs() as u32
    }
}

/// `to_token_decimals`: 6-decimal base units.
#[inline]
pub fn to_token_decimals(x: f64) -> u64 {
    let mut f = 1e6 * x;
    if decimal_places(f) > 0 {
        f = round_normal(f, 0);
    }
    f as u64
}

/// Python's amount step: product with more than 4 decimals is rounded up at 8, then down at 4.
#[inline]
fn fix_amount(mut a: f64) -> f64 {
    if decimal_places(a) > AMOUNT_DP {
        a = round_up(a, AMOUNT_DP as i32 + 4);
        if decimal_places(a) > AMOUNT_DP {
            a = round_down(a, AMOUNT_DP as i32);
        }
    }
    a
}

/// (maker_amount, taker_amount) in base units, exactly as `get_order_amounts(side, size, price,
/// ROUNDING_CONFIG["0.01"])`. BUY: maker = pUSD paid, taker = shares; SELL the reverse.
pub fn order_amounts(side: Side, size: f64, price: f64) -> (u64, u64) {
    let raw_price = round_normal(price, PRICE_DP);
    let shares = round_down(size, SIZE_DP);
    let notional = fix_amount(shares * raw_price);
    match side {
        Side::Buy => (to_token_decimals(notional), to_token_decimals(shares)),
        Side::Sell => (to_token_decimals(shares), to_token_decimals(notional)),
    }
}

/// Inputs the venue would refuse (the official client checks the price range before building).
pub fn check(size: f64, price: f64) -> Result<()> {
    if !price.is_finite() || !size.is_finite() {
        bail!("price/size must be finite");
    }
    let p = round_normal(price, PRICE_DP);
    if !(0.01..=0.99).contains(&p) {
        bail!("price {price} outside 0.01..0.99 at tick 0.01");
    }
    if round_down(size, SIZE_DP) <= 0.0 {
        bail!("size {size} rounds to 0 shares");
    }
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn repr_decimal_places() {
        let cases = [(5.0, 1), (0.57, 2), (2.85, 2), (1.4000000000000001, 16), (1e-05, 5), (1.5e-05, 6),
                     (1e16, 16), (1.2345e20, 16), (100.0, 1), (0.0001, 4), (123.456, 3), (2850000.0, 1)];
        for (x, dp) in cases {
            assert_eq!(decimal_places(x), dp, "{x}");
        }
    }

    #[test]
    fn known_amounts() {
        assert_eq!(order_amounts(Side::Buy, 5.0, 0.57), (2_850_000, 5_000_000));
        assert_eq!(order_amounts(Side::Sell, 5.5, 0.43), (5_500_000, 2_365_000));
        assert_eq!(order_amounts(Side::Buy, 12.345, 0.33), (4_072_200, 12_340_000));
    }
}
