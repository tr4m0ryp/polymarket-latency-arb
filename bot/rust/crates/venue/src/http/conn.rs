//! One HTTP/2 connection: its own reqwest::Client (own pool, so its own TCP + TLS session and
//! its own Cloudflare edge connection), TCP_NODELAY, HTTP/2 keep-alive pings, timed requests.

use std::sync::atomic::{AtomicU64, Ordering};
use std::time::Duration;

use anyhow::Result;
use reqwest::header::{HeaderMap, HeaderValue, ACCEPT, CONTENT_TYPE, USER_AGENT};
use reqwest::{Method, Version};

use super::resp::{keep_header, parse_body, Resp};
use crate::clock::{mono_ns, wall_ns};

pub const TIMEOUT: Duration = Duration::from_secs(5);

/// One request. `url` overrides host + path (other hosts, e.g. the geoblock check).
pub struct Req<'a> {
    pub method: Method,
    pub path: &'a str,
    pub query: &'a [(&'a str, String)],
    pub headers: &'a [(&'static str, String)],
    pub body: Option<&'a str>,
    pub url: Option<&'a str>,
}

impl<'a> Req<'a> {
    pub fn get(path: &'a str) -> Req<'a> {
        Req { method: Method::GET, path, query: &[], headers: &[], body: None, url: None }
    }
}

pub struct Conn {
    pub id: usize,
    host: String,
    client: reqwest::Client,
    /// monotonic ns at the end of the last request (0: never used)
    last: AtomicU64,
}

pub fn version_str(v: Version) -> &'static str {
    match v {
        Version::HTTP_2 => "HTTP/2",
        Version::HTTP_11 => "HTTP/1.1",
        Version::HTTP_10 => "HTTP/1.0",
        Version::HTTP_3 => "HTTP/3",
        _ => "HTTP/?",
    }
}

impl Conn {
    pub fn new(id: usize, host: &str) -> Result<Conn> {
        let mut h = HeaderMap::new();
        h.insert(USER_AGENT, HeaderValue::from_static("btl-venue/0.1"));
        h.insert(ACCEPT, HeaderValue::from_static("*/*"));
        let client = reqwest::Client::builder()
            .use_rustls_tls()
            .default_headers(h)
            .tcp_nodelay(true)
            .tcp_keepalive(Duration::from_secs(30))
            .http2_keep_alive_interval(Duration::from_secs(5))
            .http2_keep_alive_timeout(Duration::from_secs(3))
            .http2_keep_alive_while_idle(true)
            .pool_idle_timeout(None)
            .pool_max_idle_per_host(1)
            .connect_timeout(Duration::from_secs(3))
            .timeout(TIMEOUT)
            .build()?;
        Ok(Conn { id, host: host.trim_end_matches('/').to_string(), client, last: AtomicU64::new(0) })
    }

    /// ns since this connection last finished a request (u64::MAX if never).
    pub fn idle_ns(&self) -> u64 {
        match self.last.load(Ordering::Relaxed) {
            0 => u64::MAX,
            t => mono_ns().saturating_sub(t),
        }
    }

    pub async fn req(&self, r: Req<'_>) -> Resp {
        let url = match r.url {
            Some(u) => u.to_string(),
            None => format!("{}{}", self.host, r.path),
        };
        let mut rb = self.client.request(r.method.clone(), url);
        if !r.query.is_empty() {
            rb = rb.query(r.query);
        }
        for (k, v) in r.headers {
            rb = rb.header(*k, v.as_str());
        }
        if let Some(b) = r.body {
            rb = rb.header(CONTENT_TYPE, "application/json").body(b.to_string());
        }
        let idle = self.idle_ns();
        let (t0, w0) = (mono_ns(), wall_ns());
        let res = rb.send().await;
        let method = r.method.as_str();
        let resp = match res {
            Err(e) => Resp::transport_error(method, r.path, self.id, (t0, w0), idle, short_err(&e)),
            Ok(resp) => {
                let t_hdr = mono_ns();
                let code = resp.status().as_u16();
                let http = version_str(resp.version()).to_string();
                let hdr: Vec<(String, String)> = resp
                    .headers()
                    .iter()
                    .filter(|(k, _)| keep_header(k.as_str()))
                    .map(|(k, v)| (k.as_str().to_string(), String::from_utf8_lossy(v.as_bytes()).into_owned()))
                    .collect();
                match resp.bytes().await {
                    Err(e) => {
                        let mut x = Resp::transport_error(method, r.path, self.id, (t0, w0), idle, short_err(&e));
                        (x.code, x.http, x.hdr, x.t_hdr_mono_ns) = (code, http, hdr, t_hdr);
                        x
                    }
                    Ok(bytes) => {
                        let (t1, w1) = (mono_ns(), wall_ns());
                        let cf_ray = hdr.iter().find(|(k, _)| k == "cf-ray").map(|(_, v)| v.clone());
                        let pop = cf_ray.as_ref().and_then(|c| c.rsplit('-').next()).map(str::to_string);
                        Resp {
                            method: method.into(), path: r.path.into(), code, body: parse_body(&bytes),
                            t_send_mono_ns: t0, t_hdr_mono_ns: t_hdr, t_ack_mono_ns: t1, t_send_wall_ns: w0,
                            t_ack_wall_ns: w1, http, idle_ns: idle, cf_ray, pop, hdr, err: None, conn: self.id,
                        }
                    }
                }
            }
        };
        self.last.store(mono_ns(), Ordering::Relaxed);
        resp
    }
}

fn short_err(e: &reqwest::Error) -> String {
    let mut s = format!("{e:?}");
    s.truncate(300);
    s
}
