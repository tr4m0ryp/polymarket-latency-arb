//! Order signing for the CTF Exchange V2 (chain 137, neg_risk false, tick 0.01) and the L1
//! (ClobAuth EIP-712) auth headers. Replaces py_clob_client_v2's OrderBuilder: same amounts,
//! same digest, same signature bytes, same JSON (tests/sign_vectors.rs).

pub mod amounts;
pub mod body;
pub mod ecdsa;
pub mod eip712;
pub mod order;
pub mod poly1271;

use std::fmt;
use std::sync::Mutex;

use anyhow::{anyhow, bail, Result};

use crate::clock::{mono_ns, wall_ms};
use crate::creds::Creds;
use crate::types::{OrderSpec, OrderType, SignedOrder};
use body::BodyParts;
use ecdsa::Key;
use order::{OrderFields, OrderHasher};
use poly1271::Poly1271;

struct Hot {
    order: OrderHasher,
    poly: Option<Poly1271>,
}

pub struct Signer {
    key: Key,
    sig_type: u8,
    funder: String,
    /// the order's `signer` field: the EOA for types 0-2, the funder for type 3
    order_signer: String,
    hot: Mutex<Hot>,
}

impl fmt::Debug for Signer {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "Signer(address={}, funder={}, sig_type={}, key=<redacted>)", self.key.address(), self.funder,
               self.sig_type)
    }
}

impl Signer {
    pub fn new(creds: &Creds) -> Result<Signer> {
        let key = Key::from_hex(&creds.private_key)?;
        let sig_type = creds.sig_type();
        if sig_type > 3 {
            bail!("signature type {sig_type} outside 0..3");
        }
        let funder = creds.funder().to_string();
        let maker = eip712::parse_addr(&funder)?;
        let (order_signer, signer_bytes) =
            if sig_type == 3 { (funder.clone(), maker) } else { (key.address().to_string(), *key.address_bytes()) };
        let order = OrderHasher::new(&maker, &signer_bytes, sig_type)?;
        let poly = (sig_type == 3).then(|| Poly1271::new(order.domain, &signer_bytes));
        Ok(Signer { key, sig_type, funder, order_signer, hot: Mutex::new(Hot { order, poly }) })
    }

    /// Checksummed EOA address (POLY_ADDRESS of L1 and L2 headers).
    pub fn address(&self) -> &str {
        self.key.address()
    }

    pub fn funder(&self) -> &str {
        &self.funder
    }

    pub fn sig_type(&self) -> u8 {
        self.sig_type
    }

    /// Build, sign and serialize one order. `salt` from `new_salt()` (or any u64 < 2^53 to stay
    /// JSON-number safe for the venue), `timestamp_ms` the order's ms timestamp.
    pub fn sign(&self, spec: &OrderSpec, owner_api_key: &str, salt: u64, timestamp_ms: u64) -> Result<SignedOrder> {
        let t0 = mono_ns();
        amounts::check(spec.size, spec.price)?;
        match (spec.order_type, spec.expiration) {
            (OrderType::Gtd, 0) => bail!("GTD needs an expiration (unix s, >= server now + 60)"),
            (OrderType::Fak | OrderType::Fok | OrderType::Gtc, e) if e != 0 => {
                bail!("expiration {e} set on a {} order (GTD only)", spec.order_type)
            }
            _ => {}
        }
        let (maker_amount, taker_amount) = amounts::order_amounts(spec.side, spec.size, spec.price);
        let fields = OrderFields { salt, token_id: &spec.token_id, maker_amount, taker_amount,
                                   side: spec.side.code(), timestamp_ms };
        let mut sig_hex = String::with_capacity(1100);
        let t1 = mono_ns();
        {
            let mut hot = self.hot.lock().map_err(|_| anyhow!("signer state poisoned"))?;
            let Hot { order, poly } = &mut *hot;
            let contents = order.struct_hash(&fields)?;
            match poly {
                Some(p) => {
                    let inner = self.key.sign_hash(&p.digest(&contents))?;
                    p.write_sig(&mut sig_hex, &inner, &contents);
                }
                None => sig_hex.push_str(&hex::encode(self.key.sign_hash(&order.digest(&contents))?)),
            }
        }
        let sign_ns = mono_ns() - t1;
        let body = body::order_body(spec, &BodyParts {
            salt, maker: &self.funder, signer: &self.order_signer, maker_amount, taker_amount, timestamp_ms,
            sig_type: self.sig_type, sig_hex: &sig_hex, owner: owner_api_key,
        });
        let build_ns = mono_ns() - t0;
        Ok(SignedOrder { body, sign_ns, build_ns, maker_amount, taker_amount, salt, timestamp_ms, spec: spec.clone() })
    }

    /// L1 headers (POLY_ADDRESS, POLY_SIGNATURE, POLY_TIMESTAMP, POLY_NONCE) for the
    /// /auth/* endpoints; `ts` in unix s on the server clock.
    pub fn l1_headers(&self, ts: u64, nonce: u64) -> Result<Vec<(&'static str, String)>> {
        crate::auth::l1::headers(&self.key, ts, nonce)
    }

    /// Sign an arbitrary 32-byte digest with the EOA key (r||s||v, v 27/28).
    pub fn sign_digest(&self, digest: &[u8; 32]) -> Result<[u8; 65]> {
        self.key.sign_hash(digest)
    }
}

/// Order salt like py_order_utils `generate_order_salt`: int(random() * now_ms).
pub fn new_salt() -> u64 {
    (rand::random::<f64>() * wall_ms() as f64) as u64
}
