//! The POST /order JSON, byte-identical to Python
//! `json.dumps(order_to_json_v2(order, owner, order_type, post_only, False), separators=(",", ":"))`.

use crate::types::OrderSpec;

pub const BYTES32_ZERO: &str = "0x0000000000000000000000000000000000000000000000000000000000000000";

/// JSON string literal as json.dumps(ensure_ascii=False) writes it (same escapes as serde_json).
pub fn json_str(out: &mut String, s: &str) {
    if s.bytes().all(|b| b >= 0x20 && b != b'"' && b != b'\\') {
        out.push('"');
        out.push_str(s);
        out.push('"');
    } else {
        out.push_str(&serde_json::to_string(s).unwrap_or_else(|_| "\"\"".into()));
    }
}

pub struct BodyParts<'a> {
    pub salt: u64,
    pub maker: &'a str,
    pub signer: &'a str,
    pub maker_amount: u64,
    pub taker_amount: u64,
    pub timestamp_ms: u64,
    pub sig_type: u8,
    /// signature hex without "0x"
    pub sig_hex: &'a str,
    pub owner: &'a str,
}

pub fn order_body(spec: &OrderSpec, p: &BodyParts) -> String {
    let mut s = String::with_capacity(900 + p.sig_hex.len());
    s.push_str("{\"order\":{\"salt\":");
    s.push_str(&p.salt.to_string());
    s.push_str(",\"maker\":");
    json_str(&mut s, p.maker);
    s.push_str(",\"signer\":");
    json_str(&mut s, p.signer);
    s.push_str(",\"tokenId\":");
    json_str(&mut s, &spec.token_id);
    s.push_str(",\"makerAmount\":\"");
    s.push_str(&p.maker_amount.to_string());
    s.push_str("\",\"takerAmount\":\"");
    s.push_str(&p.taker_amount.to_string());
    s.push_str("\",\"side\":\"");
    s.push_str(spec.side.as_str());
    s.push_str("\",\"expiration\":\"");
    s.push_str(&spec.expiration.to_string());
    s.push_str("\",\"signatureType\":");
    s.push_str(&p.sig_type.to_string());
    s.push_str(",\"timestamp\":\"");
    s.push_str(&p.timestamp_ms.to_string());
    s.push_str("\",\"metadata\":\"");
    s.push_str(BYTES32_ZERO);
    s.push_str("\",\"builder\":\"");
    s.push_str(BYTES32_ZERO);
    s.push_str("\",\"signature\":\"0x");
    s.push_str(p.sig_hex);
    s.push_str("\"},\"owner\":");
    json_str(&mut s, p.owner);
    s.push_str(",\"orderType\":\"");
    s.push_str(spec.order_type.as_str());
    s.push_str("\",\"deferExec\":false,\"postOnly\":");
    s.push_str(if spec.post_only { "true" } else { "false" });
    s.push('}');
    s
}
