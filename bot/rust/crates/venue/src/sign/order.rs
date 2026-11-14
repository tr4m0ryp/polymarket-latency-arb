//! CTF Exchange V2 order struct hash and digest, with every static word precomputed: the hot
//! path writes six dynamic words into a fixed buffer and runs two keccaks.

use anyhow::Result;

use super::eip712::{domain_separator, keccak, parse_u256_dec, typed_digest, word_addr, word_u64, Word};

pub const EXCHANGE_V2: &str = "0xE111180000d2663C0091e4f400237545B87B996B";
pub const CHAIN_ID: u64 = 137;
pub const DOMAIN_NAME: &str = "Polymarket CTF Exchange";
pub const DOMAIN_VERSION: &str = "2";
pub const ORDER_TYPE: &str = "Order(uint256 salt,address maker,address signer,uint256 tokenId,\
uint256 makerAmount,uint256 takerAmount,uint8 side,uint8 signatureType,uint256 timestamp,\
bytes32 metadata,bytes32 builder)";

// Word slots of abi.encode(ORDER_TYPEHASH, salt, maker, signer, tokenId, makerAmount,
// takerAmount, side, signatureType, timestamp, metadata, builder).
const SALT: usize = 1;
const TOKEN: usize = 4;
const MAKER_AMT: usize = 5;
const TAKER_AMT: usize = 6;
const SIDE: usize = 7;
const TIMESTAMP: usize = 9;

/// Dynamic fields of one order.
pub struct OrderFields<'a> {
    pub salt: u64,
    pub token_id: &'a str,
    pub maker_amount: u64,
    pub taker_amount: u64,
    pub side: u8,
    pub timestamp_ms: u64,
}

#[derive(Clone)]
pub struct OrderHasher {
    pub domain: Word,
    base: [u8; 12 * 32],
    last_token: Option<(String, Word)>,
}

impl OrderHasher {
    /// maker = funder, signer = EOA (types 0-2) or funder (type 3); metadata and builder zero.
    pub fn new(maker: &[u8; 20], signer: &[u8; 20], sig_type: u8) -> Result<OrderHasher> {
        let exchange = super::eip712::parse_addr(EXCHANGE_V2)?;
        let domain = domain_separator(DOMAIN_NAME, DOMAIN_VERSION, CHAIN_ID, Some(&exchange));
        let mut base = [0u8; 12 * 32];
        base[..32].copy_from_slice(&keccak(ORDER_TYPE.as_bytes()));
        base[64..96].copy_from_slice(&word_addr(maker));
        base[96..128].copy_from_slice(&word_addr(signer));
        base[256..288].copy_from_slice(&word_u64(sig_type as u64));
        Ok(OrderHasher { domain, base, last_token: None })
    }

    fn put(&mut self, slot: usize, w: &Word) {
        self.base[slot * 32..slot * 32 + 32].copy_from_slice(w);
    }

    /// hashStruct(order); the token id word is cached across calls for the same token.
    pub fn struct_hash(&mut self, f: &OrderFields) -> Result<Word> {
        let tok = match &self.last_token {
            Some((t, w)) if t == f.token_id => *w,
            _ => {
                let w = parse_u256_dec(f.token_id)?;
                self.last_token = Some((f.token_id.to_string(), w));
                w
            }
        };
        self.put(TOKEN, &tok);
        self.put(SALT, &word_u64(f.salt));
        self.put(MAKER_AMT, &word_u64(f.maker_amount));
        self.put(TAKER_AMT, &word_u64(f.taker_amount));
        self.put(SIDE, &word_u64(f.side as u64));
        self.put(TIMESTAMP, &word_u64(f.timestamp_ms));
        Ok(keccak(&self.base))
    }

    /// The EIP-712 digest signed for types 0-2.
    pub fn digest(&self, struct_hash: &Word) -> Word {
        typed_digest(&self.domain, struct_hash)
    }
}
