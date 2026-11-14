"""Activity-regime columns at each decision time, causal (data at or before t only).

- bn10 / bn60: Binance perp bookTicker messages per second over the last 10 / 60 s
- sp10: Binance spot bookTicker messages per second over the last 10 s
- rv1 / rv10 / rv60: perp mid realised volatility over the last 1 / 10 / 60 s, bp per sqrt(s)
  (square root of the summed squared log-mid changes, divided by sqrt(window))
- pm10: Polymarket book messages of this market per second over the last 10 s
- pmtop10: changes of our view of the Up book's top per second over the last 10 s
- pmtr60: Polymarket trades (all takers, rivals included) in this market per second, 60 s
- jump10: |perp mid move| over the last 10 s in bp (a level-shift detector)"""
from __future__ import annotations

import numpy as np


def _count(t: np.ndarray, q: np.ndarray, w: float) -> np.ndarray:
    return (np.searchsorted(t, q, side="right") - np.searchsorted(t, q - w, side="right")) / w


def _rv(t: np.ndarray, cs: np.ndarray, q: np.ndarray, w: float) -> np.ndarray:
    hi = np.searchsorted(t, q, side="right")
    lo = np.searchsorted(t, q - w, side="right")
    return 1e4 * np.sqrt(np.maximum(cs[hi] - cs[lo], 0.0) / w)


def regime(m: dict, tab: dict) -> dict:
    q = np.asarray(tab["t"], float)
    out = {}
    perp = m["perp"]
    pt = np.asarray(perp["t"], float)
    lmid = np.log((perp["b"] + perp["a"]) / 2)
    r2 = np.r_[0.0, np.diff(lmid) ** 2]
    cs = np.r_[0.0, np.cumsum(r2)]
    out["bn10"], out["bn60"] = _count(pt, q, 10.0), _count(pt, q, 60.0)
    out["sp10"] = _count(np.asarray(m["spot_bk"]["t"], float), q, 10.0)
    for w in (1.0, 10.0, 60.0):
        out[f"rv{w:g}"] = _rv(pt, cs, q, w)
    i1, i0 = np.searchsorted(pt, q, side="right") - 1, np.searchsorted(pt, q - 10, side="right") - 1
    out["jump10"] = 1e4 * np.abs(lmid[np.clip(i1, 0, None)] - lmid[np.clip(i0, 0, None)])
    ev_t = np.sort(np.asarray(m["ev"]["t"], float))
    out["pm10"] = _count(ev_t, q, 10.0)
    tr_t = np.sort(np.asarray(m["tr"]["t"], float)) if len(m["tr"].get("t", [])) else np.zeros(0)
    out["pmtr60"] = _count(tr_t, q, 60.0)
    bb, ba = np.asarray(tab["pm_bb"], float), np.asarray(tab["pm_ba"], float)
    chg = np.r_[False, (np.diff(bb) != 0) | (np.diff(ba) != 0)]
    out["pmtop10"] = _count(q[chg], q, 10.0)
    return {k: v.astype(np.float32) for k, v in out.items()}
