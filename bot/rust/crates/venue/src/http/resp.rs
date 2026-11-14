//! The timed response record every venue call returns. Transport errors are code 0 with `err`
//! set; nothing here panics or raises.

use serde_json::Value;

/// Response headers worth keeping: Cloudflare ray (its suffix is the POP), rate limits.
pub fn keep_header(name: &str) -> bool {
    name == "cf-ray" || name == "retry-after" || name.starts_with("x-ratelimit")
}

#[derive(Clone, Debug)]
pub struct Resp {
    pub method: String,
    pub path: String,
    /// HTTP status; 0 = transport error (see `err`)
    pub code: u16,
    /// parsed JSON, or the raw text as a JSON string when it is not JSON, Null on error
    pub body: Value,
    pub t_send_mono_ns: u64,
    /// response headers received (monotonic)
    pub t_hdr_mono_ns: u64,
    /// full body received (monotonic); `ms()` is ack - send
    pub t_ack_mono_ns: u64,
    pub t_send_wall_ns: u64,
    pub t_ack_wall_ns: u64,
    /// "HTTP/2", "HTTP/1.1", "" on transport error
    pub http: String,
    /// silence on this connection before the send (u64::MAX: first request)
    pub idle_ns: u64,
    pub cf_ray: Option<String>,
    /// Cloudflare POP: last dash-separated part of cf-ray
    pub pop: Option<String>,
    pub hdr: Vec<(String, String)>,
    pub err: Option<String>,
    /// connection index in the pool
    pub conn: usize,
}

impl Resp {
    pub fn ok(&self) -> bool {
        self.code == 200
    }

    /// Round trip in ms (send to full body).
    pub fn ms(&self) -> f64 {
        self.t_ack_mono_ns.saturating_sub(self.t_send_mono_ns) as f64 / 1e6
    }

    /// The body as text: a string body as-is, anything else as compact JSON.
    pub fn text(&self) -> String {
        match &self.body {
            Value::String(s) => s.clone(),
            v => v.to_string(),
        }
    }

    pub fn header(&self, name: &str) -> Option<&str> {
        self.hdr.iter().find(|(k, _)| k == name).map(|(_, v)| v.as_str())
    }

    /// A transport-level failure record (no response at all).
    pub fn transport_error(method: &str, path: &str, conn: usize, t: (u64, u64), idle_ns: u64, err: String) -> Resp {
        let (m, w) = (crate::clock::mono_ns(), crate::clock::wall_ns());
        Resp {
            method: method.into(), path: path.into(), code: 0, body: Value::Null, t_send_mono_ns: t.0,
            t_hdr_mono_ns: m, t_ack_mono_ns: m, t_send_wall_ns: t.1, t_ack_wall_ns: w, http: String::new(),
            idle_ns, cf_ray: None, pop: None, hdr: Vec::new(), err: Some(err), conn,
        }
    }
}

/// Body bytes to JSON, or the text as a JSON string.
pub fn parse_body(bytes: &[u8]) -> Value {
    serde_json::from_slice(bytes).unwrap_or_else(|_| Value::String(String::from_utf8_lossy(bytes).into_owned()))
}
