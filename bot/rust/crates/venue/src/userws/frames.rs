//! Subscription message and frame decoding of the user channel.

use serde_json::Value;

use crate::creds::ApiCreds;

/// The subscription: `{"auth": {apiKey, secret, passphrase}, "type": "user", "markets": [...]}`.
pub fn hello(api: &ApiCreds, markets: &[String]) -> String {
    let j = |s: &str| serde_json::to_string(s).unwrap_or_else(|_| "\"\"".into());
    let mk: Vec<String> = markets.iter().map(|m| j(m)).collect();
    format!(
        "{{\"auth\": {{\"apiKey\": {}, \"secret\": {}, \"passphrase\": {}}}, \"type\": \"user\", \"markets\": [{}]}}",
        j(&api.key), j(&api.secret), j(&api.passphrase), mk.join(", ")
    )
}

/// The event objects of one frame: one event or a list; PONG and non-events yield none.
pub fn events(raw: &str) -> Vec<Value> {
    if !raw.starts_with(['[', '{']) {
        return Vec::new();
    }
    let keep = |v: &Value| v.get("event_type").is_some_and(crate::parse::truthy);
    match serde_json::from_str::<Value>(raw) {
        Ok(Value::Array(a)) => a.into_iter().filter(|v| v.is_object() && keep(v)).collect(),
        Ok(v) if v.is_object() && keep(&v) => vec![v],
        _ => Vec::new(),
    }
}
