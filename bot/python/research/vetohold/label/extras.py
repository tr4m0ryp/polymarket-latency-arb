"""Book-survival features for the label rows, on the receipt clock (what the bot had):
depth at the seen tick and within +2 / +5 c, its change over 0.25 s and 1 s, the seen
level's age (time since its size last changed or a snapshot), and the feed lag (receipt
minus venue stamp) averaged over the last 50 book messages."""
from __future__ import annotations

import numpy as np

from research.strategy import DT


def _ladder(rsz_rows, side, s_tick, k):
    up = rsz_rows[:, 101:200]
    dn = rsz_rows[:, 99:0:-1]
    a = np.where((side > 0)[:, None], up, dn)
    j = np.arange(99)[None, :]
    return np.where(j < np.minimum(s_tick + k, 99)[:, None], a, 0).sum(1)


def extras(m: dict, rsz: np.ndarray, book, t, side, s_tick) -> dict:
    t0 = m["meta"]["start"] - 2
    g = lambda x: np.clip(np.floor((x - t0) / DT + 1e-9).astype(np.int64), 0, len(rsz) - 1)  # noqa: E731
    now = rsz[g(t)]
    out = {"dep0": now[np.arange(len(t)), np.where(side > 0, 100 + s_tick, 100 - s_tick)],
           "dep2": _ladder(now, side, s_tick, 2), "dep5": _ladder(now, side, s_tick, 5)}
    for w in (0.25, 1.0):
        out[f"ddep{w}"] = out["dep2"] - _ladder(rsz[g(t - w)], side, s_tick, 2)
    ev = m["ev"]
    es, ek = ev["side"].astype(int), ev["tick"].astype(int)
    col = np.where(es > 0, ek, 100 + ek)
    et = ev["t"]
    snap = np.sort(et[es == 0])
    age = np.full(len(t), 60.0)
    mycol = np.where(side > 0, 100 + s_tick, 100 - s_tick)
    for c in np.unique(mycol):
        ct = np.sort(et[(col == c) & (es != 0)])
        k = np.flatnonzero(mycol == c)
        i = np.searchsorted(ct, t[k], "right") - 1
        j = np.searchsorted(snap, t[k], "right") - 1
        last = np.maximum(np.where(i >= 0, ct[np.maximum(i, 0)], -np.inf), np.where(j >= 0, snap[np.maximum(j, 0)], -np.inf))
        age[k] = np.minimum(t[k] - last, 60.0)
    out["age"] = age
    o = np.argsort(et, kind="stable")
    lag = (et - ev["ts"])[o]
    lag = np.where(np.isfinite(lag), lag, 0.0)
    cs = np.r_[0, np.cumsum(lag)]
    e = np.searchsorted(et[o], t, "right")
    s = np.maximum(e - 50, 0)
    out["rlag"] = (cs[e] - cs[s]) / np.maximum(e - s, 1)
    return {k: np.asarray(v, np.float32) for k, v in out.items()}
