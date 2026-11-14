"""Taker fills against the replayed venue book, with an explicit competition model.

A decision made at our receipt time t reaches the matching engine at t + L. Polymarket holds
every marketable order on crypto up/down markets for `hold` (150 ms since 2026-09-04, `itode`)
before it matches against the book as it is then; it cannot be cancelled meanwhile. So the
order fills against the venue book at t + L + hold. It buys up to
`shares` of one side (+1 Up: lift Up asks; -1 Down: hit Up bids, paying 1 - bid), walking
price levels best first up to its limit, tick 0.01, minimum order 5 shares.

Competition (documented in reports/strategy-search.md): the recording already contains every
rival. Depth at a level counts only if it is still resting at the venue for the whole window
[t + L + hold, t + L + hold + J] (J = jitter / race margin): if anyone took or cancelled it inside that
window we assume they beat us. Of what survives we take at most `cap` (share of the level).
Our own takes are remembered for `MEMORY` s: the recording does not know we took that depth, so
it is subtracted from what later decisions see. Decisions whose window touches a recorder
gap are skipped (counted)."""
from __future__ import annotations

import numpy as np

from .. import fee

MEMORY = 3.0


def run(book, t, side, shares, limit, L: float, J: float = 0.010, cap: float = 1.0,
        hold: float = 0.150):
    """Arrays per decision (sorted by t). Returns list of fills (dicts) and skipped count."""
    fills, skipped, taken = [], 0, []  # taken: (t, col, shares)
    for i in range(len(t)):
        q0, q1 = int(book.g_ceil(t[i] + L + hold)), int(book.g_ceil(t[i] + L + hold + J))
        if book.bad[q0:q1 + 1].any() or shares[i] < 5:
            skipped += 1
            continue
        if side[i] > 0:
            hi = int(np.floor(limit[i] * 100 + 1e-6))
            if hi < 1:
                continue
            cols = np.arange(101, 101 + min(hi, 99))
        else:
            lo = int(np.ceil(100 - limit[i] * 100 - 1e-6))
            if lo > 99:
                continue
            cols = np.arange(99, max(lo, 1) - 1, -1)  # best (highest) Up bid first
        avail = book.size[q0:q1 + 1, cols].min(axis=0) * cap
        if not avail.any():
            continue
        taken = [x for x in taken if x[0] > t[i] - MEMORY]
        for tt, c, s in taken:
            k = np.flatnonzero(cols == c)
            if len(k):
                avail[k[0]] = max(0.0, avail[k[0]] - s)
        left, got, cost, fees = float(shares[i]), 0.0, 0.0, 0.0
        for c, a in zip(cols, avail):
            if left <= 1e-9:
                break
            if a <= 0:
                continue
            x = min(a, left)
            p = (c - 100) / 100 if side[i] > 0 else 1 - c / 100
            got, cost, fees, left = got + x, cost + x * p, fees + x * fee(p), left - x
            taken.append((t[i], c, x))
        if got > 0:
            fills.append({"i": i, "t": t[i], "tf": t[i] + L + hold, "side": int(side[i]), "shares": got,
                          "cost": cost, "fee": fees, "px": cost / got})
    return fills, skipped
