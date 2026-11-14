//! L2 headers: urlsafe-base64 HMAC-SHA256 of `ts + method + path + body` under the urlsafe-
//! base64-decoded API secret, as py_clob_client_v2 `build_hmac_signature`.

use base64::engine::general_purpose::{GeneralPurpose, GeneralPurposeConfig, URL_SAFE};
use base64::engine::DecodePaddingMode;
use base64::{alphabet, Engine};
use hmac::{Hmac, Mac};
use sha2::Sha256;

use crate::creds::ApiCreds;

const LENIENT: GeneralPurpose = GeneralPurpose::new(
    &alphabet::URL_SAFE,
    GeneralPurposeConfig::new().with_decode_padding_mode(DecodePaddingMode::Indifferent),
);

/// Python's `urlsafe_b64decode` accepts both alphabets ('+/' and '-_') and ignores stray
/// characters; map to the urlsafe alphabet and drop anything else before decoding.
fn decode_secret(secret: &str) -> Vec<u8> {
    let clean: String = secret
        .chars()
        .filter_map(|c| match c {
            '+' => Some('-'),
            '/' => Some('_'),
            c if c.is_ascii_alphanumeric() || c == '-' || c == '_' => Some(c),
            _ => None,
        })
        .collect();
    LENIENT.decode(clean).unwrap_or_default()
}

/// The POLY_SIGNATURE of an L2 request. `body` None or "" adds nothing (Python `if body:`);
/// single quotes in the body become double quotes as in the official client.
pub fn hmac_signature(secret: &str, ts: u64, method: &str, path: &str, body: Option<&str>) -> String {
    let mut mac = <Hmac<Sha256> as Mac>::new_from_slice(&decode_secret(secret)).expect("hmac accepts any key length");
    mac.update(ts.to_string().as_bytes());
    mac.update(method.as_bytes());
    mac.update(path.as_bytes());
    if let Some(b) = body.filter(|b| !b.is_empty()) {
        if b.contains('\'') {
            mac.update(b.replace('\'', "\"").as_bytes());
        } else {
            mac.update(b.as_bytes());
        }
    }
    URL_SAFE.encode(mac.finalize().into_bytes())
}

/// POLY_ADDRESS (the signer EOA), POLY_SIGNATURE, POLY_TIMESTAMP, POLY_API_KEY, POLY_PASSPHRASE.
pub fn l2_headers(
    api: &ApiCreds,
    address: &str,
    method: &str,
    path: &str,
    body: Option<&str>,
    ts: u64,
) -> Vec<(&'static str, String)> {
    vec![
        ("POLY_ADDRESS", address.to_string()),
        ("POLY_SIGNATURE", hmac_signature(&api.secret, ts, method, path, body)),
        ("POLY_TIMESTAMP", ts.to_string()),
        ("POLY_API_KEY", api.key.clone()),
        ("POLY_PASSPHRASE", api.passphrase.clone()),
    ]
}
