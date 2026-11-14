use futures_util::{SinkExt, StreamExt};
use serde_json::Value;
use tokio::net::TcpListener;
use tokio_tungstenite::tungstenite::Message;

use super::*;

fn api() -> ApiCreds {
    ApiCreds { key: "k".into(), secret: "s".into(), passphrase: "p".into() }
}

#[test]
fn frames() {
    assert!(events("PONG").is_empty() && events("").is_empty() && events("{bad").is_empty());
    assert_eq!(events(r#"{"event_type":"trade","id":"1"}"#).len(), 1);
    assert_eq!(events(r#"[{"event_type":"order"},{"x":1},3,{"event_type":"trade"}]"#).len(), 2);
    let h: Value = serde_json::from_str(&hello(&api(), &["0xm".into()])).unwrap();
    assert_eq!(h["auth"]["apiKey"], "k");
    assert_eq!((h["type"].as_str(), h["markets"][0].as_str()), (Some("user"), Some("0xm")));
}

#[tokio::test]
async fn local_server_roundtrip() {
    let l = TcpListener::bind("127.0.0.1:0").await.unwrap();
    let url = format!("ws://{}", l.local_addr().unwrap());
    let server = tokio::spawn(async move {
        let (s, _) = l.accept().await.unwrap();
        let mut ws = tokio_tungstenite::accept_async(s).await.unwrap();
        let hello = ws.next().await.unwrap().unwrap().into_text().unwrap();
        ws.send(Message::Text(r#"[{"event_type":"trade","id":"t1"},{"event_type":"order","id":"o1"}]"#.into()))
            .await
            .unwrap();
        ws.close(None).await.unwrap();
        hello
    });
    let (tx, mut rx) = mpsc::channel(16);
    let client = tokio::spawn(async move { run_url(&url, api(), vec!["0xm".into()], tx).await });
    let mut got = Vec::new();
    while got.len() < 4 {
        got.push(rx.recv().await.unwrap());
    }
    assert!(matches!(got[0], UserMsg::State { state: WsState::Connected, .. }));
    assert!(matches!(&got[1], UserMsg::Event { ev, t_mono_ns, .. } if ev["id"] == "t1" && *t_mono_ns > 0));
    assert!(matches!(&got[2], UserMsg::Event { ev, .. } if ev["id"] == "o1"));
    assert!(matches!(got[3], UserMsg::State { state: WsState::Closed | WsState::Error, .. }));
    let hello: Value = serde_json::from_str(&server.await.unwrap()).unwrap();
    assert_eq!(hello["markets"][0], "0xm");
    drop(rx);
    client.abort();
}
