//! Polymarket CLOB market channel messages -> Up-token book events (parse.py `clob`): only
//! price_change and book events, only the Up token of a known market, levels off the 0.01 grid
//! dropped, sizes float32-rounded. One event per (message, market), markets in first-seen order.
use serde::Deserialize;
use std::collections::HashMap;

use crate::feed::event::{Ev, Pm};
use crate::state::pm::Chg;

#[derive(Deserialize)]
struct Lvl<'a> {
    price: &'a str,
    size: &'a str,
}

#[derive(Deserialize)]
struct Change<'a> {
    asset_id: &'a str,
    price: &'a str,
    size: &'a str,
    side: &'a str,
}

#[derive(Deserialize)]
struct Item<'a> {
    event_type: Option<&'a str>,
    asset_id: Option<&'a str>,
    timestamp: Option<&'a str>,
    #[serde(borrow, default)]
    price_changes: Vec<Change<'a>>,
    #[serde(borrow, default)]
    bids: Vec<Lvl<'a>>,
    #[serde(borrow, default)]
    asks: Vec<Lvl<'a>>,
}

#[derive(Deserialize)]
#[serde(untagged)]
enum Frame<'a> {
    #[serde(borrow)]
    Many(Vec<Item<'a>>),
    #[serde(borrow)]
    One(Item<'a>),
}

/// Tick 1..99 of a price on the 0.01 grid, else None (Python round = half-even).
pub fn tick(price: &str) -> Option<u8> {
    let x = price.parse::<f64>().ok()? * 100.0;
    let k = x.round_ties_even();
    if (x - k).abs() < 1e-6 && (1.0..=99.0).contains(&k) { Some(k as u8) } else { None }
}

fn ts_of(s: Option<&str>) -> f64 {
    s.and_then(|x| x.parse::<f64>().ok()).unwrap_or(f64::NAN) / 1e3
}

fn size(s: &str) -> f64 {
    s.parse::<f64>().map(|x| x as f32 as f64).unwrap_or(f64::NAN)
}

/// `ups`: Up token id -> market key (its start). Receipt time t (s).
pub fn parse(t: f64, raw: &str, ups: &HashMap<String, i64>) -> Vec<Ev> {
    if raw.contains("\"best_bid_ask\"") && !raw.contains("\"price_changes\"") && !raw.contains("\"book\"") {
        return vec![];
    }
    let items = match serde_json::from_str::<Frame>(raw) {
        Ok(Frame::Many(v)) => v,
        Ok(Frame::One(x)) => vec![x],
        Err(_) => return vec![],
    };
    let mut out = Vec::new();
    for x in items {
        match x.event_type {
            Some("price_change") => {
                let ts = ts_of(x.timestamp);
                let mut per: Vec<(i64, Vec<Chg>)> = Vec::new();
                for c in &x.price_changes {
                    let Some(&mk) = ups.get(c.asset_id) else { continue };
                    let Some(k) = tick(c.price) else { continue };
                    let e = (if c.side == "BUY" { 1 } else { -1 }, k, size(c.size));
                    match per.iter_mut().find(|p| p.0 == mk) {
                        Some(p) => p.1.push(e),
                        None => per.push((mk, vec![e])),
                    }
                }
                out.extend(per.into_iter().map(|(mkt, chg)| Ev::Pm(Pm { t, ts, mkt, snap: false, chg })));
            }
            Some("book") => {
                let Some(&mkt) = x.asset_id.and_then(|a| ups.get(a)) else { continue };
                let ts = ts_of(x.timestamp);
                let mut chg: Vec<Chg> = Vec::new();
                for (s, lv) in [(1i8, &x.bids), (-1i8, &x.asks)] {
                    chg.extend(lv.iter().filter_map(|l| tick(l.price).map(|k| (s, k, size(l.size)))));
                }
                out.push(Ev::Pm(Pm { t, ts, mkt, snap: true, chg }));
            }
            _ => {}
        }
    }
    out
}
