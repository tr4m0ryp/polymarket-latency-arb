//! POLY_1271 (deposit wallet) wrapping, exactly as py_clob_client_v2
//! `ExchangeOrderBuilderV2._build_poly_1271_order_signature`: Solady's nested TypedDataSign
//! digest signed by the EOA, then inner signature || app domain separator || contents hash ||
//! contents type string || its length (uint16 BE), all hex.

use super::eip712::{keccak, typed_digest, word_addr, word_u64, Word};
use super::order::{CHAIN_ID, ORDER_TYPE};

#[derive(Clone)]
pub struct Poly1271 {
    app_domain: Word,
    /// abi.encode(SOLADY_TYPEHASH, contents, nameHash, versionHash, chainId, signer, salt 0)
    base: [u8; 7 * 32],
    /// hex(app_domain), written between the inner signature and the contents hash
    domain_hex: String,
    /// hex(ORDER_TYPE) || hex(len(ORDER_TYPE) as u16 BE)
    tail_hex: String,
}

impl Poly1271 {
    /// `signer` is the order's signer field, i.e. the funder (deposit wallet) for type 3.
    pub fn new(app_domain: Word, signer: &[u8; 20]) -> Poly1271 {
        let solady = format!(
            "TypedDataSign(Order contents,string name,string version,uint256 chainId,\
             address verifyingContract,bytes32 salt){ORDER_TYPE}"
        );
        let mut base = [0u8; 7 * 32];
        base[..32].copy_from_slice(&keccak(solady.as_bytes()));
        base[64..96].copy_from_slice(&keccak(b"DepositWallet"));
        base[96..128].copy_from_slice(&keccak(b"1"));
        base[128..160].copy_from_slice(&word_u64(CHAIN_ID));
        base[160..192].copy_from_slice(&word_addr(signer));
        let mut tail_hex = hex::encode(ORDER_TYPE.as_bytes());
        tail_hex.push_str(&hex::encode((ORDER_TYPE.len() as u16).to_be_bytes()));
        Poly1271 { app_domain, base, domain_hex: hex::encode(app_domain), tail_hex }
    }

    /// The digest the EOA signs, from the order's struct hash (= Solady's `contents`).
    pub fn digest(&mut self, contents: &Word) -> Word {
        self.base[32..64].copy_from_slice(contents);
        typed_digest(&self.app_domain, &keccak(&self.base))
    }

    /// Append the wrapped signature (without "0x") to `out`.
    pub fn write_sig(&self, out: &mut String, inner: &[u8; 65], contents: &Word) {
        out.push_str(&hex::encode(inner));
        out.push_str(&self.domain_hex);
        out.push_str(&hex::encode(contents));
        out.push_str(&self.tail_hex);
    }
}
