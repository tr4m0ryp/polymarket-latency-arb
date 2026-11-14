//! Hedged sends against a local HTTP/1.1 mock: k copies on k separate TCP connections, each
//! with the identical body and identical L2 headers; plus the REST helpers' request shapes.

use std::collections::HashSet;
use std::sync::{Arc, Mutex};

use btl_venue::{ApiCreds, Clob, Creds, OrderSpec, OrderType, Side, Signer};
use tokio::io::{AsyncBufReadExt, AsyncReadExt, AsyncWriteExt, BufReader};
use tokio::net::TcpListener;

#[derive(Clone, Debug)]
struct Seen {
    peer: u16,
    line: String,
    headers: Vec<(String, String)>,
    body: String,
}

/// Answers every request 200 with a fixed JSON and a cf-ray; records what it saw.
async fn mock() -> (String, Arc<Mutex<Vec<Seen>>>) {
    let l = TcpListener::bind("127.0.0.1:0").await.unwrap();
    let host = format!("http://{}", l.local_addr().unwrap());
    let seen = Arc::new(Mutex::new(Vec::new()));
    let log = seen.clone();
    tokio::spawn(async move {
        loop {
            let (s, peer) = l.accept().await.unwrap();
            let log = log.clone();
            tokio::spawn(async move {
                let (r, mut w) = s.into_split();
                let mut r = BufReader::new(r);
                loop {
                    let mut line = String::new();
                    if r.read_line(&mut line).await.unwrap_or(0) == 0 {
                        return;
                    }
                    let mut headers = Vec::new();
                    loop {
                        let mut h = String::new();
                        r.read_line(&mut h).await.unwrap();
                        let h = h.trim_end().to_string();
                        if h.is_empty() {
                            break;
                        }
                        let (k, v) = h.split_once(": ").unwrap();
                        headers.push((k.to_lowercase(), v.to_string()));
                    }
                    let n: usize = headers.iter().find(|(k, _)| k == "content-length").map_or(0, |(_, v)| v.parse().unwrap());
                    let mut body = vec![0u8; n];
                    r.read_exact(&mut body).await.unwrap();
                    let body = String::from_utf8(body).unwrap();
                    log.lock().unwrap().push(Seen { peer: peer.port(), line: line.trim_end().into(), headers, body });
                    let out = r#"{"success":true,"orderID":"0xabc","status":"matched","makingAmount":"2.85","takingAmount":"5"}"#;
                    let resp = format!("HTTP/1.1 200 OK\r\ncontent-type: application/json\r\ncf-ray: 8f1e2d3c4b5a6978-AMS\r\n\
                                        x-ratelimit-remaining: 99\r\ncontent-length: {}\r\n\r\n{out}", out.len());
                    w.write_all(resp.as_bytes()).await.unwrap();
                }
            });
        }
    });
    (host, seen)
}

fn signer() -> Signer {
    let pk = "0x4c0883a69102937d6231471b5dbb6204fe5129617082792ae468d01a3f362318";
    Signer::new(&Creds::new(pk, "0x6E0C80c90ea6C15917308F820Eac91Ce2724B5b5", 3, None).unwrap()).unwrap()
}

fn api() -> ApiCreds {
    ApiCreds { key: "key-1".into(), secret: "c2VjcmV0LXRlc3Q=".into(), passphrase: "pp".into() }
}

#[tokio::test(flavor = "multi_thread", worker_threads = 4)]
async fn hedged_copies_are_identical_on_separate_connections() {
    let (host, seen) = mock().await;
    assert!(Clob::new(&host, 4).is_err() && Clob::new(&host, 0).is_err());
    let clob = Clob::new(&host, 3).unwrap();
    let warm = clob.warm().await;
    assert!(warm.iter().all(|r| r.ok() && r.http == "HTTP/1.1"));
    seen.lock().unwrap().clear();
    let s = signer();
    let spec = OrderSpec { token_id: "12345".into(), price: 0.57, size: 5.0, side: Side::Buy,
                           order_type: OrderType::Fak, post_only: false, expiration: 0 };
    let signed = s.sign(&spec, "key-1", 99, 1_760_000_000_000).unwrap();
    let rs = clob.post_order(&signed, &api(), s.address(), 3).await;
    assert_eq!(rs.iter().map(|r| r.conn).collect::<Vec<_>>(), [0, 1, 2]);
    for r in &rs {
        assert_eq!((r.code, r.pop.as_deref(), r.header("x-ratelimit-remaining")), (200, Some("AMS"), Some("99")));
        assert!(r.err.is_none() && r.t_ack_mono_ns >= r.t_send_mono_ns && r.idle_ns < u64::MAX);
        assert!(btl_venue::parse::order(r).ok);
    }
    let seen = seen.lock().unwrap().clone();
    assert_eq!(seen.len(), 3);
    assert_eq!(seen.iter().map(|x| x.peer).collect::<HashSet<_>>().len(), 3, "copies must use 3 connections");
    let poly = |x: &Seen| -> Vec<(String, String)> {
        let mut h: Vec<_> = x.headers.iter().filter(|(k, _)| k.starts_with("poly_")).cloned().collect();
        h.sort();
        h
    };
    for x in &seen {
        assert_eq!(x.line, "POST /order HTTP/1.1");
        assert_eq!(x.body, signed.body);
        assert_eq!(poly(x), poly(&seen[0]));
        assert_eq!(poly(x).len(), 5);
    }
    assert!(seen[0].headers.contains(&("content-type".into(), "application/json".into())));
    assert!(seen[0].headers.contains(&("poly_address".into(), s.address().into())));
}

#[tokio::test]
async fn first_ack_cancel_and_reads() {
    let (host, seen) = mock().await;
    let clob = Clob::new(&host, 2).unwrap();
    clob.connect().await;
    assert!(clob.offset_s().abs() < 1e9);
    let s = signer();
    let spec = OrderSpec { token_id: "12345".into(), price: 0.4, size: 6.0, side: Side::Sell,
                           order_type: OrderType::Gtd, post_only: true, expiration: 1_760_003_600 };
    let signed = s.sign(&spec, "key-1", 7, 1_760_000_000_000).unwrap();
    let (first, rest) = clob.post_order_first(&signed, &api(), s.address(), 2).await;
    assert_eq!(first.code, 200);
    assert_eq!(rest.await.unwrap().len(), 2);
    seen.lock().unwrap().clear();
    let c = clob.cancel("0xabc", &api(), s.address(), 2).await;
    assert_eq!(c.len(), 2);
    let all = clob.cancel_all(&api(), s.address(), 1).await;
    assert_eq!(all.len(), 1);
    clob.balance(&api(), s.address(), 3).await;
    clob.get_order(&api(), s.address(), "0xabc").await;
    clob.book("123").await;
    let seen = seen.lock().unwrap().clone();
    let lines: Vec<&str> = seen.iter().map(|x| x.line.as_str()).collect();
    assert_eq!(&lines[..3], ["DELETE /order HTTP/1.1"; 2].iter().copied().chain(["DELETE /cancel-all HTTP/1.1"]).collect::<Vec<_>>());
    assert_eq!(seen[0].body, r#"{"orderID":"0xabc"}"#);
    assert_eq!(lines[3], "GET /balance-allowance?asset_type=COLLATERAL&signature_type=3 HTTP/1.1");
    assert_eq!(lines[4], "GET /data/order/0xabc HTTP/1.1");
    assert_eq!(lines[5], "GET /book?token_id=123 HTTP/1.1");
    let ka = clob.spawn_keep_warm(0.05);
    tokio::time::sleep(std::time::Duration::from_millis(300)).await;
    ka.abort();
    assert!(clob.ping_ns().iter().all(|&p| p > 0));
}

#[tokio::test]
async fn transport_error_is_code_zero() {
    let clob = Clob::new("http://127.0.0.1:1", 1).unwrap();
    let r = clob.time().await;
    assert_eq!(r.code, 0);
    assert!(r.err.is_some() && btl_venue::parse::order(&r).err_kind.as_deref() == Some("transport"));
}
