"""Instrumented copy of research/strategy/sim/taker.py: the same fill rule (match at
t + L + hold, depth must survive [match, match + J], at most `cap` of a level, our own takes
remembered MEMORY s), plus a match-time shift `e` (s) and the per-level fills of every order.

e > 0 = we match e later than the simulator assumes (every rival inside that gap beats us);
e < 0 = we match earlier. With e = 0, J = 0.01, cap = 1 it reproduces the simulator's fills
(checked against data/out/predict/fills-<tag>.pkl in check.py)."""
from __future__ import annotations

import numpy as np

from ......strategy import fee
from ......strategy.sim.taker import MEMORY


def cols_for(side: int, limit: float) -> np.ndarray:
    """Book columns an order may take, best first (Up asks up to limit, or Up bids down to
    1 - limit for a Down buy)."""
    if side > 0:
        hi = int(np.floor(limit * 100 + 1e-6))
        return np.arange(101, 101 + min(hi, 99)) if hi >= 1 else np.arange(0)
    lo = int(np.ceil(100 - limit * 100 - 1e-6))
    return np.arange(99, max(lo, 1) - 1, -1) if lo <= 99 else np.arange(0)


def price(c: int, side: int) -> float:
    return (c - 100) / 100 if side > 0 else 1 - c / 100


def run(book, t, side, shares, limit, L: float, J: float = 0.010, cap: float = 1.0,
        hold: float = 0.150, e: float = 0.0):
    """Returns one dict per decision: i, tf, got, cost, fee, lv [(col, shares)], skip."""
    out, taken = [], []
    for i in range(len(t)):
        tf = t[i] + L + hold + e
        rec = {"i": i, "tf": tf, "got": 0.0, "cost": 0.0, "fee": 0.0, "lv": [], "skip": False}
        out.append(rec)
        q0, q1 = int(book.g_ceil(tf)), int(book.g_ceil(tf + J))
        if book.bad[q0:q1 + 1].any() or shares[i] < 5:
            rec["skip"] = True
            continue
        cols = cols_for(int(side[i]), float(limit[i]))
        if not len(cols):
            continue
        avail = book.size[q0:q1 + 1, cols].min(axis=0) * cap
        if not avail.any():
            continue
        taken = [x for x in taken if x[0] > t[i] - MEMORY]
        for tt, c, s in taken:
            k = np.flatnonzero(cols == c)
            if len(k):
                avail[k[0]] = max(0.0, avail[k[0]] - s)
        left = float(shares[i])
        for c, a in zip(cols, avail):
            if left <= 1e-9:
                break
            if a <= 0:
                continue
            x = min(a, left)
            p = price(int(c), int(side[i]))
            rec["got"] += x
            rec["cost"] += x * p
            rec["fee"] += x * fee(p)
            rec["lv"].append((int(c), x))
            left -= x
            taken.append((t[i], c, x))
    return out
