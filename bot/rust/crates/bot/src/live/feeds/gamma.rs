//! Gamma: market discovery by slug (btclat/live/markets.py) and the closed-market outcome
//! (research/strategy/ingest/markets.py `_gamma_outcome`).
use anyhow::{Context, Result};
use serde_json::Value;

use btl_signal::MarketMeta;

pub const GAMMA: &str = "https://gamma-api.polymarket.com";

/// Starts of the 5m markets open now or opening within `lead_s` (90 s: the pre-open strike window).
pub fn wanted(now: f64, lead_s: f64) -> Vec<i64> {
    let cur = (now as i64) / 300 * 300;
    let mut out = vec![cur];
    if (cur + 300) as f64 - now <= lead_s {
        out.push(cur + 300);
    }
    out
}

fn strs(v: &Value) -> Option<Vec<String>> {
    serde_json::from_str(v.as_str()?).ok()
}

pub async fn fetch(http: &reqwest::Client, start: i64) -> Result<Option<MarketMeta>> {
    let slug = format!("btc-updown-5m-{start}");
    let rows: Value = http.get(format!("{GAMMA}/markets?slug={slug}")).send().await?.json().await?;
    let Some(m) = rows.as_array().and_then(|a| a.first()) else { return Ok(None) };
    let outs = strs(&m["outcomes"]).context("outcomes")?;
    let toks = strs(&m["clobTokenIds"]).context("clobTokenIds")?;
    let iu = outs.iter().position(|o| o == "Up").context("no Up")?;
    let idn = outs.iter().position(|o| o == "Down").context("no Down")?;
    let tick = m["orderPriceMinTickSize"].as_f64().or_else(|| m["orderPriceMinTickSize"].as_str().and_then(|s| s.parse().ok()));
    Ok(Some(MarketMeta { fam: "5m".into(), slug, start, end: start + 300,
        condition_id: m["conditionId"].as_str().unwrap_or("").into(), up: toks[iu].clone(), down: toks[idn].clone(),
        tick: tick.unwrap_or(0.01) }))
}

/// 1.0 Up won, 0.0 Down won, None while not resolved.
pub async fn outcome(http: &reqwest::Client, slug: &str) -> Result<Option<f64>> {
    let rows: Value = http.get(format!("{GAMMA}/markets?slug={slug}&closed=true")).send().await?.json().await?;
    let Some(m) = rows.as_array().and_then(|a| a.first()) else { return Ok(None) };
    let (Some(outs), Some(px)) = (strs(&m["outcomes"]), strs(&m["outcomePrices"])) else { return Ok(None) };
    let px: Vec<f64> = px.iter().filter_map(|s| s.parse().ok()).collect();
    if px.len() != outs.len() || px.iter().cloned().fold(f64::MIN, f64::max) < 0.99 {
        return Ok(None);
    }
    let iu = outs.iter().position(|o| o == "Up").context("no Up")?;
    Ok(Some(if px[iu] > 0.5 { 1.0 } else { 0.0 }))
}
