//! Book snapshots (top 5 levels of the bought token, our feed's view) for the order log.
use serde_json::{json, Value};

use btl_signal::engine::World;

pub fn snapshot(w: &World, mkt: i64, up: bool, limit: f64) -> Option<Value> {
    let m = w.mkts.iter().find(|m| m.meta.start == mkt)?;
    let bk = &m.book;
    let (bids, asks) = bk.levels(up, 5);
    let mid_up = bk.mid();
    let mid = if mid_up.is_nan() { None } else { Some(if up { mid_up } else { 1.0 - mid_up }) };
    let (bb, ba) = if up { (bk.bb as f64 / 100.0, bk.ba as f64 / 100.0) } else { (1.0 - bk.ba as f64 / 100.0, 1.0 - bk.bb as f64 / 100.0) };
    Some(json!({"slug": m.meta.slug, "t": btl_venue::wall_ns() as f64 / 1e9, "top_t": bk.top_t, "up": up, "bids": bids, "asks": asks, "bb": bb, "ba": ba,
        "mid": mid, "depth_le_limit": bk.depth_le(up, limit), "vts": if bk.last_ts.is_nan() { None } else { Some(bk.last_ts) }}))
}
