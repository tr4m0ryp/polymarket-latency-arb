//! What must hold before the bot may touch the venue (btclat/trade/gate/preflight.py). Live:
//! --i-approve, no kill file, the UTC day not locked, credentials file safe, a pinned model,
//! then online: not geoblocked (IE / JP / NL / KR are API-allowed), CLOB exchange version 2,
//! enough pUSD and a non-zero allowance. Dry: kill file only; an ephemeral key signs.
use anyhow::{bail, Context, Result};
use serde_json::{json, Value};
use std::path::Path;

use btl_venue::{load_creds, parse, ApiCreds, Clob, Creds, Signer};

use super::exec::Venue;

pub const API_ALLOWED: [&str; 4] = ["IE", "JP", "NL", "KR"];
pub const MIN_BALANCE: f64 = 5.0;
pub const EXCHANGE_VERSION: i64 = 2;
/// market windows and the refractory run on the host clock (GET /time has 1 s resolution)
pub const MAX_CLOCK_OFFSET_S: f64 = 2.0;

pub fn dry_signer() -> Result<(Signer, String)> {
    let pk: [u8; 32] = rand::random();
    let c = Creds::new(&format!("0x{}", hex_of(&pk)), "0x0000000000000000000000000000000000000001", 0, None)?;
    Ok((Signer::new(&c)?, "dry-run-owner".into()))
}

fn hex_of(b: &[u8]) -> String {
    b.iter().map(|x| format!("{x:02x}")).collect()
}

pub async fn live(config: &Path, host: &str, k: usize) -> Result<(Venue, Signer, String, Value)> {
    let creds = load_creds(&config.join("polymarket.env")).map_err(|e| anyhow::anyhow!("refusing: {e:#}"))?;
    let clob = Clob::new(host, k)?;
    let pings = clob.connect().await;
    if clob.offset_s().abs() > MAX_CLOCK_OFFSET_S {
        bail!("refusing: host clock is {:.1} s off the CLOB server clock (> {MAX_CLOCK_OFFSET_S} s); fix chrony first",
            -clob.offset_s());
    }
    let signer = Signer::new(&creds)?;
    let (api, derived): (ApiCreds, bool) = match creds.api() {
        Some(a) => (a.clone(), false),
        None => match clob.derive_api_key(&signer).await {
            Ok(a) => (a, true),
            Err(_) => (clob.create_api_key(&signer).await.context("refusing: could not derive or create L2 API creds")?, true),
        },
    };
    let g = clob.geoblock().await;
    let blocked = g.body.get("blocked").and_then(|v| v.as_bool());
    let country = g.body.get("country").and_then(|v| v.as_str()).unwrap_or("");
    if !(blocked == Some(false) || (blocked == Some(true) && API_ALLOWED.contains(&country))) {
        bail!("refusing: geoblock says {} (orders from this IP are rejected or close-only)", g.body);
    }
    let v = btl_venue::http::endpoints::version_num(&clob.version().await);
    if v != EXCHANGE_VERSION {
        bail!("refusing: CLOB exchange version {v}, this code signs version {EXCHANGE_VERSION}");
    }
    let addr = signer.address().to_string();
    let b = parse::balance(&clob.balance(&api, &addr, creds.sig_type()).await);
    if b.balance < MIN_BALANCE {
        bail!("refusing: pUSD balance ${:.2} < ${MIN_BALANCE} (HTTP {})", b.balance, b.code);
    }
    if !b.allowance_ok {
        bail!("refusing: pUSD allowance to the exchange is zero (run the trading approvals)");
    }
    let info = json!({"address": addr, "funder": creds.funder(), "sig_type": creds.sig_type(), "l2_derived": derived,
        "server_offset_s": clob.offset_s(), "geoblock": g.body, "version": v, "balance": b.balance,
        "warm_ms": pings.iter().map(|r| r.ms()).collect::<Vec<_>>(), "pops": pings.iter().map(|r| r.pop.clone()).collect::<Vec<_>>()});
    let owner = api.key.clone();
    let venue = Venue { clob, api, addr, sig_type: creds.sig_type() };
    Ok((venue, signer, owner, info))
}
