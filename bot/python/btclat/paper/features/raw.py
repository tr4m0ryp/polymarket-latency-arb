"""One decision row at time q, column for column the offline table of
research/predict/feats/build.py (Binance perp + spot book features, spot trade flow, basis
and microprice deviations, Polymarket view and settlement features, the pzm fair value).

`Ctx` bundles the shared Binance state; `MarketCtx` the per-market part (book, K, last-minute
TWAP cache). Perp trade features (ft_*) are not built: the v1 models do not read them."""
from __future__ import annotations

import math
from dataclasses import dataclass, field

from ..state.book import BookState
from ..state.pm import PMBook
from ..state.spot import LockedTwap, Settle, TradeFlow, p_model
from .fair import PZM, zq

TICK_PERP = 0.1


@dataclass
class Ctx:
    perp: BookState = field(default_factory=lambda: BookState(TICK_PERP))
    spot: BookState = field(default_factory=lambda: BookState(0.01))
    flow: TradeFlow = field(default_factory=TradeFlow)
    settle: Settle = field(default_factory=Settle)
    fair: PZM = field(default_factory=PZM)


@dataclass
class MarketCtx:
    meta: dict
    book: PMBook = field(default_factory=PMBook)
    K: float = float("nan")
    lock: LockedTwap | None = None

    def __post_init__(self):
        self.start, self.end = float(self.meta["start"]), float(self.meta["end"])
        self.lock = LockedTwap(self.end)

    def strike(self, st: Settle) -> float:
        """K = 60 s TWAP before the start (trade clock); fixed once computed after start."""
        if self.K != self.K:
            self.K = st.twap(self.start - 60, self.start)
        return self.K


def row(q: float, c: Ctx, m: MarketCtx) -> dict:
    f: dict = {"t": q}
    c.perp.features(q, "p", f)
    c.spot.features(q, "s", f)
    sdep = max(c.spot.depth if c.spot.t is not None else 1.0, 1e-6)
    c.flow.features(q, sdep, f)
    pm, sm = c.perp, c.spot
    f["basis_dev"] = 1e4 * (pm.lmid(q) - sm.lmid(q)) - 1e4 * (pm.lmid(q - 30) - sm.lmid(q - 30))
    f["mic_dev"] = 1e4 * ((pm.lmic(q) - pm.lmic(q - 2)) - (sm.lmic(q) - sm.lmic(q - 2)))
    pm_feats(q, c, m, f)
    zs = f["zs"]
    f["fair_dz"] = c.fair.dz(q, c.perp, c.spot, zs)
    f["fair_p"] = PZM.p(f["pm_mid"], f["fair_dz"])
    return f


def pm_feats(q: float, c: Ctx, m: MarketCtx, f: dict) -> None:
    """research/predict/feats/pm.py pm_features at one instant."""
    bk = m.book
    zscale = c.settle.zscale(q, m.end)
    zs = zscale * 1e-4
    mid = bk.mid()
    f.update({"pm_bb": float(bk.bb), "pm_ba": float(bk.ba), "pm_mid": mid,
              "pm_spr": float(bk.ba - bk.bb), "secs_left": m.end - q, "lzs": math.log(zs),
              "sigma": c.settle.sigma(q)})
    # offline: top changes on the book grid from start - 2 on, else q - 5 (feats/pm.py)
    last = bk.top_t if bk.top_t is not None and bk.top_t > m.start - 2 else q - 5.0
    f["pm_tsc"] = math.log(max(q - last, 1e-3))
    f["pm_stale"] = 1e4 * (c.perp.lmic(q) - c.perp.lmic(last)) * zs
    zm = zq(mid)
    for k, (a, b) in enumerate(((0, .2), (.2, 1), (1, 3))):
        f[f"bk{k}"] = zq(bk.mid_at(q - a)) - zq(bk.mid_at(q - b))
    K = m.strike(c.settle)
    g = zq(p_model(c.settle, q, m.start, m.end, K, m.lock)) - zm
    f["gap"] = min(max(g, -2.0), 2.0) if g == g else g
    f["zs"] = zscale


def micro_view(q: float, c: Ctx, m: MarketCtx, with_fair: bool) -> dict:
    """The few columns the strategy micro rules read (research/strategy/signals/features.py
    v2 table): our view of the book, time left, perp / spot microprice moves over 0.1 s, and
    the pzm fair value (micf)."""
    bk = m.book
    d = {"t": q, "secs_left": m.end - q, "bb": float(bk.bb), "ba": float(bk.ba), "mid": bk.mid(),
         "pmic_r0.1": 1e4 * (c.perp.lmic(q) - c.perp.lmic(q - 0.1)),
         "smic_r0.1": 1e4 * (c.spot.lmic(q) - c.spot.lmic(q - 0.1))}
    if with_fair:
        zs = c.settle.zscale(q, m.end)
        d["p_fair"] = PZM.p(d["mid"], c.fair.dz(q, c.perp, c.spot, zs))
    return d
