//! Live, public, unauthenticated reads only (GET /time, /version). Opt-in:
//!     cargo test -p btl_venue --test smoke -- --ignored --nocapture

use btl_venue::http::endpoints::version_num;
use btl_venue::{Clob, HOST};

#[tokio::test]
#[ignore]
async fn public_time_and_version() {
    let clob = Clob::new(HOST, 2).unwrap();
    let rs = clob.connect().await;
    for r in &rs {
        println!("conn {} {} {} {:.1} ms pop {:?} body {}", r.conn, r.code, r.http, r.ms(), r.pop, r.text());
        assert!(r.ok() && r.http == "HTTP/2");
    }
    let again = clob.warm().await;
    for r in &again {
        println!("warm conn {} {:.1} ms idle {:.1} ms", r.conn, r.ms(), r.idle_ns as f64 / 1e6);
    }
    println!("server offset {:.3} s, version {}", clob.offset_s(), version_num(&clob.version().await));
}
