//! Binance combined-stream messages (raw @trade and @bookTicker), parse.py `binance`.
use serde::Deserialize;

use crate::feed::event::{Book, Ev, Trade};

#[derive(Deserialize)]
struct Msg<'a> {
    #[serde(borrow)]
    stream: Option<&'a str>,
    #[serde(borrow)]
    data: Option<Data<'a>>,
}

#[derive(Deserialize)]
#[allow(non_snake_case)]
struct Data<'a> {
    b: Option<&'a str>,
    a: Option<&'a str>,
    B: Option<&'a str>,
    A: Option<&'a str>,
    u: Option<u64>,
    T: Option<f64>,
    p: Option<&'a str>,
    q: Option<&'a str>,
    m: Option<bool>,
    t: Option<u64>,
}

/// Dedupe key: bookTicker update id or trade id.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum Key {
    U(u64),
    T(u64),
}

fn f(s: Option<&str>) -> Option<f64> {
    s.and_then(|x| x.parse::<f64>().ok())
}

/// (event, dedupe key) of one message; None if not ours. `t` = receipt time (s).
pub fn parse(t: f64, raw: &str, perp: bool) -> Option<(Ev, Key)> {
    let j: Msg = serde_json::from_str(raw).ok()?;
    let d = j.data?;
    let stream = j.stream.unwrap_or("");
    if stream.ends_with("@trade") {
        let tr = Trade { t, tt: d.T? / 1e3, px: f(d.p)?, q: f(d.q)? as f32 as f64,
            m: if d.m? { 1.0 } else { 0.0 }, id: d.t? };
        let key = Key::T(tr.id);
        return Some((if perp { Ev::Pt(tr) } else { Ev::St(tr) }, key));
    }
    if d.b.is_some() && d.a.is_some() {
        let tt = if perp { d.T.map(|x| x / 1e3).unwrap_or(f64::NAN) } else { f64::NAN };
        let bk = Book { t, tt, b: f(d.b)?, a: f(d.a)?, bq: f(d.B)? as f32 as f64, aq: f(d.A)? as f32 as f64, u: d.u? };
        let key = Key::U(bk.u);
        return Some((if perp { Ev::Pb(bk) } else { Ev::Sb(bk) }, key));
    }
    None
}
