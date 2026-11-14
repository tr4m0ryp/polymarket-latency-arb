//! One decision row at time q, column for column btclat/paper/features/raw.py `row`.
use crate::engine::market::{Ctx, MarketCtx};
use crate::features::names::*;
use crate::num::cephes::{ndtr, zq};
use crate::num::{pymax, pymin};
use crate::state::p_model;

pub fn row(q: f64, c: &mut Ctx, m: &mut MarketCtx) -> Row {
    let mut f: Row = [f64::NAN; N];
    f[T] = q;
    c.perp.features(q, &mut f, PERP);
    c.spot.features(q, &mut f, SPOT);
    let sdep = pymax(if c.spot.t.is_some() { c.spot.depth } else { 1.0 }, 1e-6);
    c.flow.features(q, sdep, &mut f);
    let (pm, sm) = (&c.perp, &c.spot);
    f[BASIS_DEV] = 1e4 * (pm.lmid(q) - sm.lmid(q)) - 1e4 * (pm.lmid(q - 30.0) - sm.lmid(q - 30.0));
    f[MIC_DEV] = 1e4 * ((pm.lmic(q) - pm.lmic(q - 2.0)) - (sm.lmic(q) - sm.lmic(q - 2.0)));
    pm_feats(q, c, m, &mut f);
    f[FAIR_DZ] = c.fair.dz(q, &c.perp, &c.spot, f[ZS]);
    f[FAIR_P] = ndtr(zq(f[PM_MID]) + f[FAIR_DZ]);
    f
}

fn pm_feats(q: f64, c: &mut Ctx, m: &mut MarketCtx, f: &mut Row) {
    let zscale = c.settle.zscale(q, m.end);
    let zs = zscale * 1e-4;
    let bk = &m.book;
    let mid = bk.mid();
    f[PM_BB] = bk.bb as f64;
    f[PM_BA] = bk.ba as f64;
    f[PM_MID] = mid;
    f[PM_SPR] = (bk.ba - bk.bb) as f64;
    f[SECS_LEFT] = m.end - q;
    f[LZS] = zs.ln();
    f[SIGMA] = c.settle.sigma(q);
    let last = match bk.top_t {
        Some(tt) if tt > m.start - 2.0 => tt,
        _ => q - 5.0,
    };
    f[PM_TSC] = pymax(q - last, 1e-3).ln();
    f[PM_STALE] = 1e4 * (c.perp.lmic(q) - c.perp.lmic(last)) * zs;
    let zm = zq(mid);
    for (k, (a, b)) in [(0.0, 0.2), (0.2, 1.0), (1.0, 3.0)].into_iter().enumerate() {
        f[BK0 + k] = zq(bk.mid_at(q - a)) - zq(bk.mid_at(q - b));
    }
    let k = m.strike(&c.settle);
    let g = zq(p_model(&mut c.settle, q, m.end, k, &mut m.lock)) - zm;
    f[GAP] = if g.is_nan() { g } else { pymin(pymax(g, -2.0), 2.0) };
    f[ZS] = zscale;
}
