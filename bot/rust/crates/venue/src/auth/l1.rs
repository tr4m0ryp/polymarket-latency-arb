//! L1 headers: EIP-712 `ClobAuth(address address,string timestamp,uint256 nonce,string message)`
//! under domain {name "ClobAuthDomain", version "1", chainId 137}, as py_clob_client_v2
//! `create_level_1_headers` builds them.

use anyhow::Result;

use crate::sign::ecdsa::Key;
use crate::sign::eip712::{domain_separator, keccak, typed_digest, word_addr, word_u64};
use crate::sign::order::CHAIN_ID;

pub const MSG_TO_SIGN: &str = "This message attests that I control the given wallet";
const CLOB_AUTH_TYPE: &str = "ClobAuth(address address,string timestamp,uint256 nonce,string message)";

/// The L1 signature ("0x" + 130 hex) over (address, ts, nonce).
pub fn signature(key: &Key, ts: u64, nonce: u64) -> Result<String> {
    let domain = domain_separator("ClobAuthDomain", "1", CHAIN_ID, None);
    let mut buf = [0u8; 5 * 32];
    buf[..32].copy_from_slice(&keccak(CLOB_AUTH_TYPE.as_bytes()));
    buf[32..64].copy_from_slice(&word_addr(key.address_bytes()));
    buf[64..96].copy_from_slice(&keccak(ts.to_string().as_bytes()));
    buf[96..128].copy_from_slice(&word_u64(nonce));
    buf[128..].copy_from_slice(&keccak(MSG_TO_SIGN.as_bytes()));
    let sig = key.sign_hash(&typed_digest(&domain, &keccak(&buf)))?;
    Ok(format!("0x{}", hex::encode(sig)))
}

pub fn headers(key: &Key, ts: u64, nonce: u64) -> Result<Vec<(&'static str, String)>> {
    Ok(vec![
        ("POLY_ADDRESS", key.address().to_string()),
        ("POLY_SIGNATURE", signature(key, ts, nonce)?),
        ("POLY_TIMESTAMP", ts.to_string()),
        ("POLY_NONCE", nonce.to_string()),
    ])
}
