//! secp256k1 key: RFC 6979 deterministic, low-s signatures as eth_account produces them
//! (r || s || v with v = 27/28), the EOA address and EIP-55 checksumming.

use std::fmt;

use anyhow::{anyhow, Result};
use k256::ecdsa::SigningKey;

use super::eip712::{keccak, Word};

pub struct Key {
    sk: SigningKey,
    addr: [u8; 20],
    addr_str: String,
}

impl fmt::Debug for Key {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "Key(address={}, secret=<redacted>)", self.addr_str)
    }
}

impl Key {
    pub fn from_hex(pk: &str) -> Result<Key> {
        let h = pk.strip_prefix("0x").unwrap_or(pk);
        let mut raw = [0u8; 32];
        hex::decode_to_slice(h, &mut raw).map_err(|_| anyhow!("private key must be 32 bytes hex"))?;
        let sk = SigningKey::from_slice(&raw).map_err(|_| anyhow!("private key out of range"))?;
        raw.fill(0);
        let pubkey = sk.verifying_key().to_encoded_point(false);
        let h = keccak(&pubkey.as_bytes()[1..]);
        let mut addr = [0u8; 20];
        addr.copy_from_slice(&h[12..]);
        Ok(Key { sk, addr_str: checksum(&addr), addr })
    }

    pub fn address(&self) -> &str {
        &self.addr_str
    }

    pub fn address_bytes(&self) -> &[u8; 20] {
        &self.addr
    }

    /// Sign a 32-byte digest: r (32) || s (32) || v (27 + recovery id).
    pub fn sign_hash(&self, digest: &Word) -> Result<[u8; 65]> {
        let (sig, rec) = self.sk.sign_prehash_recoverable(digest).map_err(|e| anyhow!("sign: {e}"))?;
        let mut out = [0u8; 65];
        out[..64].copy_from_slice(&sig.to_bytes());
        out[64] = 27 + rec.to_byte();
        Ok(out)
    }
}

/// EIP-55 mixed-case checksum address (what eth_account's `Account.address` returns).
pub fn checksum(addr: &[u8; 20]) -> String {
    let lower = hex::encode(addr);
    let h = keccak(lower.as_bytes());
    let mut out = String::with_capacity(42);
    out.push_str("0x");
    for (i, c) in lower.chars().enumerate() {
        let nib = (h[i / 2] >> if i % 2 == 0 { 4 } else { 0 }) & 0xf;
        out.push(if c.is_ascii_alphabetic() && nib >= 8 { c.to_ascii_uppercase() } else { c });
    }
    out
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn address_of_test_key() {
        let k = Key::from_hex("0x4c0883a69102937d6231471b5dbb6204fe5129617082792ae468d01a3f362318").unwrap();
        assert_eq!(k.address(), "0x2c7536E3605D9C16a7a3D7b1898e529396a65c23");
        assert!(!format!("{k:?}").contains("4c0883a6"));
    }

    #[test]
    fn eip55_vectors() {
        for a in ["0x5aAeb6053F3E94C9b9A09f33669435E7Ef1BeAed", "0xfB6916095ca1df60bB79Ce92cE3Ea74c37c5d359",
                  "0xdbF03B407c01E7cD3CBea99509d93f8DDDC8C6FB", "0xD1220A0cf47c7B9Be7A2E6BA89F429762e7b9aDb"] {
            let mut b = [0u8; 20];
            hex::decode_to_slice(a[2..].to_lowercase(), &mut b).unwrap();
            assert_eq!(checksum(&b), a);
        }
    }
}
