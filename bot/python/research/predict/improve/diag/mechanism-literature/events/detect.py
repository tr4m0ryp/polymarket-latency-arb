"""Binance perp events: the first perp update at which the mid has moved, within LOOK s on our
receipt clock, by enough to shift the Polymarket fair value by >= THR_C cents.

Cents per bp = delta = 100 * phi(Phi^-1(venue mid)) * zscale (model/derive.py), read from the
market's decision table row at or before the update (our view, no look-ahead). `detect`
returns the events and one matched quiet placebo instant per event (`placebo`)."""
from __future__ import annotations

import numpy as np
from scipy.special import ndtri

from .. import BAND, LOOK, REFR, THR_C, TLEFT


def perp_logmid(perp: dict) -> np.ndarray:
    return 1e4 * np.log((perp["b"] + perp["a"]) / 2)


def delta_at(tab: dict, q: np.ndarray):
    """(cents per bp, venue mid of our view, secs_left, row age) at query times q."""
    j = np.searchsorted(tab["t"], q, side="right") - 1
    jj = np.clip(j, 0, None)
    mid = np.where(j >= 0, tab["pm_mid"][jj], np.nan)
    zq = ndtri(np.clip(mid, 0.02, 0.98))
    d = 100 * np.exp(-zq ** 2 / 2) / np.sqrt(2 * np.pi) * tab["zs"][jj] * 1e-4
    age = np.where(j >= 0, q - tab["t"][jj], np.inf)
    return np.where(j >= 0, d, np.nan), mid, np.where(j >= 0, tab["secs_left"][jj], np.nan), age


def detect(perp: dict, tab: dict, start: float, end: float) -> dict:
    t, lm = perp["t"], perp_logmid(perp)
    w = (t >= start + 5) & (t <= end - TLEFT)
    idx = np.flatnonzero(w)
    if not len(idx):
        return {}, {}
    base = np.searchsorted(t, t[idx] - LOOK, side="right") - 1
    ok = base >= 0
    idx, base = idx[ok], base[ok]
    dm = lm[idx] - lm[base]
    d, mid, left, age = delta_at(tab, t[idx])
    c = dm * d
    cand = (np.abs(c) >= THR_C) & (mid >= BAND[0]) & (mid <= BAND[1]) & (age < 1.0) & (left >= TLEFT)
    keep, last = [], -np.inf
    for k in np.flatnonzero(cand):
        if t[idx[k]] - last >= REFR:
            keep.append(k)
            last = t[idx[k]]
    k = np.array(keep, dtype=np.int64)
    ev = {"k": idx[k], "base": base[k], "c0": c[k], "dm0": dm[k], "delta": d[k], "mid_view": mid[k],
          "secs_left": left[k], "side": np.sign(c[k])}
    return ev, placebo(t, idx, base, c, dm, d, mid, left, age, ev)


def placebo(t, idx, base, c, dm, d, mid, left, age, ev, quiet=0.25, gap=2.0, back=6.0) -> dict:
    """One matched quiet instant per event: the perp update nearest t0 - back with < `quiet` c
    of implied move over LOOK, same gates, >= gap s from every event; it inherits the event's
    side, so its response is the book's background turnover in the same activity state."""
    te = t[ev["k"]]
    ok = (np.abs(c) < quiet) & (mid >= BAND[0]) & (mid <= BAND[1]) & (age < 1.0) & (left >= TLEFT)
    if len(te):
        near = np.abs(t[idx][:, None] - te[None, :]).min(1) < gap
        ok &= ~near
    cand = np.flatnonzero(ok)
    pick = []
    for x in te:
        if not len(cand):
            pick.append(-1)
            continue
        j = cand[np.argmin(np.abs(t[idx[cand]] - (x - back)))]
        pick.append(j if abs(t[idx[j]] - (x - back)) < back else -1)
    p = np.array(pick, dtype=np.int64)
    w = p >= 0
    p = p[w]
    return {"k": idx[p], "base": base[p], "c0": c[p], "dm0": dm[p], "delta": d[p], "mid_view": mid[p],
            "secs_left": left[p], "side": ev["side"][w]}
