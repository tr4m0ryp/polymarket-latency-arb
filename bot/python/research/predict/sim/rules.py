"""Decision rules driven by the value model (model/value.py) on one market's table.

pred_up / pred_dn = predicted per-share 10 s value of buying Up / Down at the match time.

- vtaker: buy the side with the higher prediction when it is >= margin; optional `require`
  = "trigger" (the leaders' perp microprice trigger toward that side) or "micf" (trigger +
  fair edge >= 1 c): the model then acts as a veto on that rule. Limit = seen ask + slip.
- vmaker: post-only quotes (strategy rules.quotes: fair +/- half around the pzm fair value,
  or join the touch) pulled per side when the model says the opposite side is about to
  become valuable (pred of the side that would run us over >= pull)."""
from __future__ import annotations

import numpy as np
import pandas as pd

from ...strategy import fee
from ...strategy.signals.rules import _refractory


def _gates(d: pd.DataFrame, seen, band, tleft, fav_max):
    mid = d["pm_mid"].to_numpy(float)
    ok = (seen >= band[0]) & (seen <= band[1]) & (d["secs_left"].to_numpy() >= tleft)
    ok &= np.maximum(mid, 1 - mid) <= fav_max
    return ok & (d["pm_bb"].to_numpy() > 0) & (d["pm_ba"].to_numpy() < 100) & np.isfinite(mid)


def vtaker(d: pd.DataFrame, pu, pd_, margin=0.02, refr=0.2, shares=60.0, slip=0.02,
           band=(0.05, 0.95), tleft=20.0, fav_max=0.97, require=None, fair_margin=0.01,
           max_fills=None, burst=None):
    side = np.where(pu >= pd_, 1.0, -1.0)
    edge = np.maximum(pu, pd_)
    seen = np.where(side > 0, d["pm_ba"].to_numpy(float) / 100, 1 - d["pm_bb"].to_numpy(float) / 100)
    ok = (edge >= margin) & _gates(d, seen, band, tleft, fav_max)
    if require in ("trigger", "micf"):
        pm, sm = d["p_dmic0.1"].to_numpy(float), d["s_dmic0.1"].to_numpy(float)
        ok &= (np.abs(pm) >= 0.002) & (np.sign(pm + sm) == side)
        if require == "micf":
            fp = d["fair_p"].to_numpy(float)
            val = np.where(side > 0, fp, 1 - fp)
            ok &= val - seen - fee(seen) >= fair_margin
    i = _refractory(d["t"].to_numpy(), ok, refr)
    if burst is not None:  # at most burst[0] orders per burst[1] s window (tail-risk cap)
        t, keep = d["t"].to_numpy()[i], []
        for j, x in enumerate(t):
            if sum(1 for k in keep[-burst[0]:] if x - t[k] < burst[1]) < burst[0]:
                keep.append(j)
        i = i[np.array(keep, dtype=np.int64)] if keep else i[:0]
    if max_fills is not None:  # orders per market
        i = i[:max_fills]
    return {"t": d["t"].to_numpy()[i], "side": side[i], "shares": np.full(len(i), shares),
            "limit": np.minimum(seen[i] + slip, 0.99), "edge": edge[i]}


def vmaker(d: pd.DataFrame, pu, pd_, half=0.05, pull=-0.01, anchor="fair", band=(0.10, 0.90),
           tleft=30.0):
    bb, ba = d["pm_bb"].to_numpy(float), d["pm_ba"].to_numpy(float)
    mid = d["pm_mid"].to_numpy(float)
    fp = d["fair_p"].to_numpy(float)
    if anchor == "fair":
        b = np.minimum(np.floor((fp - half) * 100 + 1e-9), ba - 1)
        a = np.maximum(np.ceil((fp + half) * 100 - 1e-9), bb + 1)
    else:
        b, a = bb.copy(), ba.copy()
    ok = (mid >= band[0]) & (mid <= band[1]) & (d["secs_left"].to_numpy() >= tleft)
    ok &= np.isfinite(fp) & (bb > 0) & (ba < 100)
    b = np.where(ok & (b >= 1) & (pd_ < pull), b, 0).astype(int)   # Up bid is run over when Down gains
    a = np.where(ok & (a <= 99) & (pu < pull), a, 0).astype(int)   # Up ask is lifted when Up gains
    return d["t"].to_numpy(), b, a


def vinside(d: pd.DataFrame, pu, pd_, half=0.04, pull=-0.02, h=0.0, **gates):
    """Inside gate (reports/fill-improve.md idea 1, pre-registered in
    data/out/predict/inside-prereg.json): vmaker at fair -/+ half, kept only where the quote
    is the new best price strictly inside the spread (bb < bid < ba, bb < ask < ba). h > 0
    adds insert hysteresis: a side enters only at pred < pull - h and leaves at pred >= pull."""
    t, b, a = vmaker(d, pu, pd_, half=half, pull=pull, **gates)
    bb, ba = d["pm_bb"].to_numpy(float), d["pm_ba"].to_numpy(float)
    b = np.where((b > 0) & (b > bb), b, 0).astype(int)
    a = np.where((a > 0) & (a < ba), a, 0).astype(int)
    if h > 0:
        b, a = hysteresis(b, pd_, pull, h), hysteresis(a, pu, pull, h)
    return t, b, a


def hyst_step(on: bool, tick: int, p: float, pull: float, h: float) -> tuple[bool, int]:
    """One decision of the insert hysteresis: (side live?, tick to quote). A zero target
    resets the side; an idle side enters only when its pull prediction is below pull - h."""
    if tick <= 0:
        return False, 0
    if on or p < pull - h:
        return True, tick
    return False, 0


def hysteresis(q, p, pull: float, h: float):
    out, on = np.zeros(len(q), dtype=int), False
    for i in range(len(q)):
        on, out[i] = hyst_step(on, int(q[i]), float(p[i]), pull, h)
    return out
