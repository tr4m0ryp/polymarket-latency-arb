//! Hedged sends: one signed order (or cancel) on k connections at once, the SAME body and the
//! SAME L2 headers (same timestamp and HMAC) on each, so the venue sees identical payloads and
//! dedupes them (measured live by hold/dup.py). Each copy runs in its own task, so a caller
//! can act on the first ack while the rest land.

use std::sync::Arc;

use reqwest::Method;
use tokio::sync::mpsc;
use tokio::task::JoinHandle;

use super::conn::Req;
use super::pool::Clob;
use super::resp::Resp;
use crate::auth::l2::l2_headers;
use crate::creds::ApiCreds;
use crate::types::SignedOrder;

pub type Headers = Vec<(&'static str, String)>;

impl Clob {
    /// Fire identical copies on order connections 0..k (k clamped to 1..=pool size). Results
    /// arrive on the returned channel in completion order.
    pub fn hedge(&self, k: usize, method: Method, path: &str, headers: Headers, body: Option<String>) -> mpsc::Receiver<Resp> {
        let k = k.clamp(1, self.k());
        let (tx, rx) = mpsc::channel(k);
        let shared = Arc::new((method, path.to_string(), headers, body));
        for i in 0..k {
            let (clob, tx, s) = (self.clone(), tx.clone(), shared.clone());
            tokio::spawn(async move {
                let (method, path, headers, body) = &*s;
                let r = clob
                    .on(i, Req { method: method.clone(), path, query: &[], headers, body: body.as_deref(), url: None })
                    .await;
                let _ = tx.send(r).await;
            });
        }
        rx
    }

    /// All k results, ordered by connection index.
    pub async fn hedge_all(&self, k: usize, method: Method, path: &str, headers: Headers, body: Option<String>) -> Vec<Resp> {
        let mut rx = self.hedge(k, method, path, headers, body);
        let mut out = Vec::new();
        while let Some(r) = rx.recv().await {
            out.push(r);
        }
        out.sort_by_key(|r| r.conn);
        out
    }

    /// The first answer that is not a transport error (or the last error if all fail), and a
    /// handle yielding all k results.
    pub async fn hedge_first(&self, k: usize, method: Method, path: &str, headers: Headers, body: Option<String>)
        -> (Resp, JoinHandle<Vec<Resp>>) {
        let mut rx = self.hedge(k, method, path, headers, body);
        let mut seen = Vec::new();
        let mut first = None;
        while let Some(r) = rx.recv().await {
            let done = r.code != 0;
            seen.push(r);
            if done {
                first = seen.last().cloned();
                break;
            }
        }
        let first = first.or_else(|| seen.last().cloned()).unwrap_or_else(|| {
            Resp::transport_error("?", path, 0, (crate::mono_ns(), crate::wall_ns()), 0, "no copy sent".into())
        });
        let rest = tokio::spawn(async move {
            while let Some(r) = rx.recv().await {
                seen.push(r);
            }
            seen.sort_by_key(|r| r.conn);
            seen
        });
        (first, rest)
    }

    /// L2 headers of a POST /order, built once and reused by every copy.
    pub fn post_headers(&self, signed: &SignedOrder, api: &ApiCreds, address: &str) -> Headers {
        l2_headers(api, address, "POST", "/order", Some(&signed.body), self.auth_ts())
    }

    /// POST /order on k connections at once; all k results by connection.
    pub async fn post_order(&self, signed: &SignedOrder, api: &ApiCreds, address: &str, k: usize) -> Vec<Resp> {
        let h = self.post_headers(signed, api, address);
        self.hedge_all(k, Method::POST, "/order", h, Some(signed.body.clone())).await
    }

    /// POST /order on k connections; returns at the first ack, the rest on the handle.
    pub async fn post_order_first(&self, signed: &SignedOrder, api: &ApiCreds, address: &str, k: usize)
        -> (Resp, JoinHandle<Vec<Resp>>) {
        let h = self.post_headers(signed, api, address);
        self.hedge_first(k, Method::POST, "/order", h, Some(signed.body.clone())).await
    }

    /// Body and L2 headers of DELETE /order {"orderID": oid}, reusable for identical copies.
    pub fn cancel_req(&self, oid: &str, api: &ApiCreds, address: &str) -> (String, Headers) {
        let body = serde_json::json!({ "orderID": oid }).to_string();
        let h = l2_headers(api, address, "DELETE", "/order", Some(&body), self.auth_ts());
        (body, h)
    }

    /// DELETE /order on k connections.
    pub async fn cancel(&self, oid: &str, api: &ApiCreds, address: &str, k: usize) -> Vec<Resp> {
        let (body, h) = self.cancel_req(oid, api, address);
        self.hedge_all(k, Method::DELETE, "/order", h, Some(body)).await
    }

    /// DELETE /cancel-all on k connections.
    pub async fn cancel_all(&self, api: &ApiCreds, address: &str, k: usize) -> Vec<Resp> {
        let h = l2_headers(api, address, "DELETE", "/cancel-all", None, self.auth_ts());
        self.hedge_all(k, Method::DELETE, "/cancel-all", h, None).await
    }
}
