//! Single-connection REST calls of btclat/trade/venue/client.py. Each returns the timed `Resp`
//! (parse:: turns it into a record); `trades` and the API-key calls return parsed data.

use anyhow::{bail, Result};
use reqwest::Method;
use serde_json::Value;

use super::conn::Req;
use super::pool::{Clob, GEOBLOCK};
use super::resp::Resp;
use crate::auth::l2::l2_headers;
use crate::creds::ApiCreds;
use crate::sign::Signer;

pub const BALANCE: &str = "/balance-allowance";
pub const TRADES: &str = "/data/trades";
const INITIAL_CURSOR: &str = "MA==";
const END_CURSOR: &str = "LTE=";

impl Clob {
    /// GET https://polymarket.com/api/geoblock (data connection).
    pub async fn geoblock(&self) -> Resp {
        self.on_data(Req { url: Some(GEOBLOCK), ..Req::get("") }).await
    }

    /// GET /version; `version_num()` reads the number.
    pub async fn version(&self) -> Resp {
        self.on(0, Req::get("/version")).await
    }

    /// GET /book?token_id= (data connection; parse::best).
    pub async fn book(&self, token_id: &str) -> Resp {
        let q = [("token_id", token_id.to_string())];
        self.on_data(Req { query: &q, ..Req::get("/book") }).await
    }

    /// GET /balance-allowance?asset_type=COLLATERAL&signature_type=N, L2-signed on the bare path.
    pub async fn balance(&self, api: &ApiCreds, address: &str, sig_type: u8) -> Resp {
        let h = l2_headers(api, address, "GET", BALANCE, None, self.auth_ts());
        let q = [("asset_type", "COLLATERAL".to_string()), ("signature_type", sig_type.to_string())];
        self.on(0, Req { query: &q, headers: &h, ..Req::get(BALANCE) }).await
    }

    /// GET /data/order/<id> (follow-up of a delayed order; parse::lookup).
    pub async fn get_order(&self, api: &ApiCreds, address: &str, oid: &str) -> Resp {
        let path = format!("/data/order/{oid}");
        let h = l2_headers(api, address, "GET", &path, None, self.auth_ts());
        self.on(0, Req { headers: &h, ..Req::get(&path) }).await
    }

    /// Our trades matched since `after` (unix s): GET /data/trades, L2-signed on the bare path,
    /// cursor-paginated up to `pages`. Errs on an error answer so a failed read is never "none".
    pub async fn trades(&self, api: &ApiCreds, address: &str, after: u64, pages: usize) -> Result<Vec<Value>> {
        let mut out = Vec::new();
        let mut cursor = INITIAL_CURSOR.to_string();
        for _ in 0..pages {
            let h = l2_headers(api, address, "GET", TRADES, None, self.auth_ts());
            let q = [("after", after.to_string()), ("next_cursor", cursor.clone())];
            let r = self.on(0, Req { query: &q, headers: &h, ..Req::get(TRADES) }).await;
            match (&r.code, r.body) {
                (200, Value::Array(a)) => {
                    out.extend(a);
                    return Ok(out);
                }
                (200, Value::Object(mut m)) => {
                    if let Some(Value::Array(a)) = m.remove("data") {
                        out.extend(a);
                    }
                    match m.get("next_cursor").and_then(Value::as_str) {
                        Some(c) if !c.is_empty() && c != END_CURSOR => cursor = c.to_string(),
                        _ => break,
                    }
                }
                (code, body) => {
                    let mut t = body.to_string();
                    t.truncate(200);
                    bail!("GET {TRADES}: HTTP {code} {t} {}", r.err.unwrap_or_default());
                }
            }
        }
        Ok(out)
    }

    /// L2 creds from the key: GET /auth/derive-api-key, else POST /auth/api-key (L1-signed).
    pub async fn derive_api_key(&self, signer: &Signer) -> Result<ApiCreds> {
        let h = signer.l1_headers(self.auth_ts(), 0)?;
        let r = self.on(0, Req { headers: &h, ..Req::get("/auth/derive-api-key") }).await;
        if r.ok() {
            if let Some(a) = api_from(&r.body) {
                return Ok(a);
            }
        }
        self.create_api_key(signer).await
    }

    /// POST /auth/api-key (L1-signed): new L2 creds.
    pub async fn create_api_key(&self, signer: &Signer) -> Result<ApiCreds> {
        let h = signer.l1_headers(self.auth_ts(), 0)?;
        let r = self.on(0, Req { method: Method::POST, headers: &h, ..Req::get("/auth/api-key") }).await;
        match (r.ok(), api_from(&r.body)) {
            (true, Some(a)) => Ok(a),
            _ => {
                let mut t = r.text();
                t.truncate(200);
                bail!("refusing: could not derive L2 API creds (HTTP {}: {t})", r.code)
            }
        }
    }
}

/// `{"apiKey","secret","passphrase"}` -> ApiCreds.
pub fn api_from(body: &Value) -> Option<ApiCreds> {
    let s = |k: &str| body.get(k).and_then(Value::as_str).map(str::to_string);
    Some(ApiCreds { key: s("apiKey")?, secret: s("secret")?, passphrase: s("passphrase")? })
}

/// The number of a GET /version answer, -1 when absent (client.py `version()`).
pub fn version_num(r: &Resp) -> i64 {
    r.body.get("version").and_then(|v| v.as_i64().or_else(|| v.as_str()?.parse().ok())).unwrap_or(-1)
}
