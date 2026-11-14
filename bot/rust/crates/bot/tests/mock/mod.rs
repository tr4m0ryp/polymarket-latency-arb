//! A local HTTP/1.1 stand-in for the CLOB REST API: answers by path, records every request.
use std::sync::{Arc, Mutex};

use tokio::io::{AsyncBufReadExt, AsyncReadExt, AsyncWriteExt, BufReader};
use tokio::net::TcpListener;

#[derive(Clone, Debug)]
pub struct Seen {
    pub peer: u16,
    pub line: String,
    pub body: String,
}

fn answer(line: &str) -> &'static str {
    if line.starts_with("POST /order") {
        r#"{"success":true,"orderID":"0xabc","status":"matched","makingAmount":"2.85","takingAmount":"5","tradeIDs":["t1"]}"#
    } else if line.contains("/cancel-all") {
        r#"{"canceled":[],"not_canceled":{}}"#
    } else if line.contains("/time") {
        "1760000000"
    } else {
        "{}"
    }
}

pub async fn serve() -> (String, Arc<Mutex<Vec<Seen>>>) {
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
                    let mut n = 0usize;
                    loop {
                        let mut h = String::new();
                        r.read_line(&mut h).await.unwrap();
                        let h = h.trim_end().to_lowercase();
                        if h.is_empty() {
                            break;
                        }
                        if let Some(v) = h.strip_prefix("content-length: ") {
                            n = v.parse().unwrap();
                        }
                    }
                    let mut body = vec![0u8; n];
                    r.read_exact(&mut body).await.unwrap();
                    let line = line.trim_end().to_string();
                    let out = answer(&line);
                    log.lock().unwrap().push(Seen { peer: peer.port(), line, body: String::from_utf8(body).unwrap() });
                    let resp = format!("HTTP/1.1 200 OK\r\ncontent-type: application/json\r\ncf-ray: 8f1e2d3c4b5a6978-DUB\r\n\
                                        content-length: {}\r\n\r\n{out}", out.len());
                    if w.write_all(resp.as_bytes()).await.is_err() {
                        return;
                    }
                }
            });
        }
    });
    (host, seen)
}
