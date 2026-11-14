//! The unit queued to the writer thread and its single-line JSON encoding.
use std::io::Write;
use std::time::Duration;

use crossbeam_channel::Sender;
use serde_json::Value;

/// Top-level keys the logger owns; a body field with one of these names is written as `body_<key>`.
const RESERVED: [&str; 5] = ["run", "seq", "mono_ns", "wall_ns", "kind"];

pub(crate) enum Body {
    /// Structured body: object fields are flattened into the top level.
    Value(Value),
    /// Pre-serialized fields without braces, e.g. `"a":1,"b":"x"`.
    Raw(String),
}

pub(crate) struct Record {
    pub seq: u64,
    pub mono_ns: u64,
    pub wall_ns: u64,
    pub kind: &'static str,
    pub body: Body,
}

pub(crate) enum Msg {
    Rec(Record),
    /// Writer flushes its buffer, then signals.
    Flush(Sender<()>),
    /// Test hook: stall the writer so the channel fills.
    Sleep(Duration),
    Close,
}

impl Record {
    /// Append `{"run":..,"seq":..,"mono_ns":..,"wall_ns":..,"kind":..,<fields>}\n` to `out`.
    pub fn encode(&self, run_json: &str, out: &mut Vec<u8>) {
        let _ = write!(
            out,
            "{{\"run\":{run_json},\"seq\":{},\"mono_ns\":{},\"wall_ns\":{},\"kind\":",
            self.seq, self.mono_ns, self.wall_ns
        );
        let _ = serde_json::to_writer(&mut *out, self.kind);
        match &self.body {
            Body::Raw(s) => {
                if !s.is_empty() {
                    out.push(b',');
                    out.extend_from_slice(s.as_bytes());
                }
            }
            Body::Value(Value::Object(m)) => {
                for (k, v) in m {
                    out.push(b',');
                    if RESERVED.contains(&k.as_str()) {
                        let _ = serde_json::to_writer(&mut *out, &format!("body_{k}"));
                    } else {
                        let _ = serde_json::to_writer(&mut *out, k);
                    }
                    out.push(b':');
                    let _ = serde_json::to_writer(&mut *out, v);
                }
            }
            Body::Value(Value::Null) => {}
            Body::Value(v) => {
                out.extend_from_slice(b",\"value\":");
                let _ = serde_json::to_writer(&mut *out, v);
            }
        }
        out.extend_from_slice(b"}\n");
    }
}
