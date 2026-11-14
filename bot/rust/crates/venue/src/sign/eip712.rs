//! EIP-712 / ABI building blocks: keccak, 32-byte words, address and uint256 parsing.

use anyhow::{bail, Result};
use sha3::{Digest, Keccak256};

pub type Word = [u8; 32];

#[inline]
pub fn keccak(data: &[u8]) -> Word {
    Keccak256::digest(data).into()
}

#[inline]
pub fn word_u64(v: u64) -> Word {
    let mut w = [0u8; 32];
    w[24..].copy_from_slice(&v.to_be_bytes());
    w
}

#[inline]
pub fn word_addr(a: &[u8; 20]) -> Word {
    let mut w = [0u8; 32];
    w[12..].copy_from_slice(a);
    w
}

/// 0x + 40 hex, any case (eth_abi encodes the bytes; the string itself goes into JSON verbatim).
pub fn parse_addr(s: &str) -> Result<[u8; 20]> {
    let h = s.strip_prefix("0x").unwrap_or(s);
    let mut a = [0u8; 20];
    if h.len() != 40 || hex::decode_to_slice(h, &mut a).is_err() {
        bail!("bad address {s:?}");
    }
    Ok(a)
}

/// A decimal uint256 (token ids are up to 78 digits) as a big-endian word.
pub fn parse_u256_dec(s: &str) -> Result<Word> {
    if s.is_empty() || s.len() > 78 || !s.bytes().all(|b| b.is_ascii_digit()) {
        bail!("bad uint256 {s:?}");
    }
    let mut limbs = [0u64; 4]; // little-endian limbs
    for b in s.bytes() {
        let mut carry = (b - b'0') as u128;
        for l in limbs.iter_mut() {
            let v = *l as u128 * 10 + carry;
            *l = v as u64;
            carry = v >> 64;
        }
        if carry != 0 {
            bail!("uint256 overflow {s:?}");
        }
    }
    let mut w = [0u8; 32];
    for (i, l) in limbs.iter().enumerate() {
        w[24 - 8 * i..32 - 8 * i].copy_from_slice(&l.to_be_bytes());
    }
    Ok(w)
}

/// keccak(abi.encode(typeHash(EIP712Domain), keccak(name), keccak(version), chainId[, verifyingContract])).
pub fn domain_separator(name: &str, version: &str, chain_id: u64, contract: Option<&[u8; 20]>) -> Word {
    let ty = match contract {
        Some(_) => "EIP712Domain(string name,string version,uint256 chainId,address verifyingContract)",
        None => "EIP712Domain(string name,string version,uint256 chainId)",
    };
    let mut buf = Vec::with_capacity(160);
    for w in [keccak(ty.as_bytes()), keccak(name.as_bytes()), keccak(version.as_bytes()), word_u64(chain_id)] {
        buf.extend_from_slice(&w);
    }
    if let Some(c) = contract {
        buf.extend_from_slice(&word_addr(c));
    }
    keccak(&buf)
}

/// keccak(0x19 0x01 || domainSeparator || structHash).
#[inline]
pub fn typed_digest(domain: &Word, struct_hash: &Word) -> Word {
    let mut buf = [0u8; 66];
    buf[0] = 0x19;
    buf[1] = 0x01;
    buf[2..34].copy_from_slice(domain);
    buf[34..].copy_from_slice(struct_hash);
    keccak(&buf)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn u256_decimal() {
        assert_eq!(parse_u256_dec("1").unwrap(), word_u64(1));
        assert_eq!(parse_u256_dec("18446744073709551616").unwrap()[23], 1);
        let max = "115792089237316195423570985008687907853269984665640564039457584007913129639935";
        assert_eq!(parse_u256_dec(max).unwrap(), [0xff; 32]);
        assert!(parse_u256_dec("115792089237316195423570985008687907853269984665640564039457584007913129639936").is_err());
        assert!(parse_u256_dec("12a").is_err());
    }

    #[test]
    fn keccak_empty() {
        assert_eq!(hex::encode(keccak(b"")), "c5d2460186f7233c927e7db2dcc703c0e500b653ca82273b7bfad8045d85a470");
    }
}
