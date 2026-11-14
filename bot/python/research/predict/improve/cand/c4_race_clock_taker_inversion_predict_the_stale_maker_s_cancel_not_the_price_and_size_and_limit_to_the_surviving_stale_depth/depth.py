"""Receipt-clock Polymarket depth per decision row and the stale-level events of one market.

Replays the market's level messages on OUR receipt clock (`t`, never the venue stamp), the
same `_replay` the simulator uses for its decision view, so a row at time t sees only what
had arrived by t. Per tab row (Up frame, columns 0-99 bids, 100-199 asks):
  qa  size at the seen Up ask (pm_ba),  qa2 size one tick worse (pm_ba + 1)
  qb  size at the seen Up bid (pm_bb),  qb2 size one tick worse (pm_bb - 1)
Events: tab rows where the strategy fair value moved >= 1 c within 0.1 s, >= 1 s apart. The
stale level is the Up ask after a rise (Up buyers lift it), the Up bid after a fall. alive =
its receipt-clock size stayed >= half its size at t_e over our L = 0 match window (MATCH);
egap = how far the stale level sits inside the new fair value ($, > 0 = worth taking).
y_alive_a / y_alive_b: per-row label, the seen ask / bid kept >= half its size over the match
window (future data: used to fit the row-level model only, never read by a decision).
Cached per market (npz) under CACHE/depth/."""
from __future__ import annotations

import os

import numpy as np

from .....strategy import DT
from .....strategy.sim.grid import _replay
from ....model.data import TAB
from . import CACHE, MATCH, assert_open

DIR = CACHE / "depth"
COLS = ("t", "fair_p", "pm_ba", "pm_bb")
JUMP, GAP, LOOK = 0.01, 1.0, 0.1
_ST = None


def _store():
    global _ST
    if _ST is None:
        from ...harness.guard import SafeStore
        _ST = SafeStore()
    return _ST


def _events(t, fp, ba, bb):
    j = np.searchsorted(t, t - LOOK, "right") - 1
    ok = j >= 0
    d = np.where(ok, fp - fp[np.clip(j, 0, None)], 0.0)
    cand = np.flatnonzero(ok & np.isfinite(d) & (np.abs(d) >= JUMP) & (bb > 0) & (ba < 100))
    out, last = [], -np.inf
    for k in cand:
        if t[k] - last >= GAP:
            out.append(k)
            last = t[k]
    k = np.asarray(out, dtype=np.int64)
    return k, np.sign(d[k]).astype(np.int8)


def build(i: int) -> dict:
    st = _store()
    meta = st.mk.iloc[i]
    start, end = float(meta["start"]), float(meta["end"])
    assert_open(start)
    with np.load(TAB / f"{i}.npz") as z:
        d = {c: z[c] for c in COLS}
    m = st.market(i)
    ev = m["ev"]
    t0 = start - 2
    n = int(np.ceil((end + 2 - t0) / DT)) + 1
    sz = _replay(ev["t"], ev["side"], ev["tick"].astype(np.int64), ev["size"], t0, n)
    t = d["t"].astype(float)
    g = np.clip(np.floor((t - t0) / DT + 1e-9).astype(np.int64), 0, n - 1)
    ba = d["pm_ba"].astype(np.int64)
    bb = d["pm_bb"].astype(np.int64)
    ca, cb = np.clip(100 + ba, 101, 199), np.clip(bb, 1, 99)
    out = {"qa": sz[g, ca], "qa2": sz[g, np.clip(ca + 1, 101, 199)] * (ca < 199),
           "qb": sz[g, cb], "qb2": sz[g, np.clip(cb - 1, 1, 99)] * (cb > 1)}
    for k in ("qa", "qb"):
        out[k] = np.where((ba < 100) & (bb > 0), out[k], 0).astype(np.float32)
    r0 = np.clip(np.ceil((t + MATCH[0] - t0) / DT - 1e-9).astype(np.int64), 0, n - 1)
    r1 = np.clip(np.floor((t + MATCH[1] - t0) / DT + 1e-9).astype(np.int64), 0, n - 1)
    for k, c in (("a", ca), ("b", cb)):     # LABELS (future): fitting only, never read by a decision
        smin = np.min([sz[np.minimum(r0 + j, r1), c] for j in range(int(round((MATCH[1] - MATCH[0]) / DT)) + 1)], 0)
        out[f"y_alive_{k}"] = ((smin >= 0.5 * out[f"q{k}"]) & (out[f"q{k}"] > 0)).astype(np.int8)
    k, sgn = _events(t, d["fair_p"].astype(float), ba, bb)
    col = np.where(sgn > 0, ca[k], cb[k])
    size0 = sz[g[k], col]
    g0 = np.clip(np.ceil((t[k] + MATCH[0] - t0) / DT - 1e-9).astype(np.int64), 0, n - 1)
    g1 = np.clip(np.floor((t[k] + MATCH[1] - t0) / DT + 1e-9).astype(np.int64), 0, n - 1)
    smin = np.array([sz[a:b + 1, c].min() if b >= a else sz[a, c] for a, b, c in zip(g0, g1, col)],
                    dtype=np.float32)
    fp = d["fair_p"].astype(float)[k]
    egap = np.where(sgn > 0, fp - ba[k] / 100, bb[k] / 100 - fp)      # stale level inside fair, $
    out.update(ek=k, edir=sgn, esize=size0.astype(np.float32), egap=egap.astype(np.float32),
               ealive=((smin >= 0.5 * size0) & (size0 > 0)).astype(np.int8),
               start=np.float64(start), n=np.int64(len(t)))
    return out


def load(i: int) -> dict:
    """Cached depth of market i (built on first use)."""
    p = DIR / f"{i}.npz"
    if p.exists():
        with np.load(p) as z:
            out = {k: z[k] for k in z.files}
        assert_open(out["start"])
        return out
    out = build(i)
    DIR.mkdir(parents=True, exist_ok=True)
    tmp = p.with_name(f"{i}.{os.getpid()}.tmp.npz")
    np.savez(tmp, **out)
    os.replace(tmp, p)
    return out
