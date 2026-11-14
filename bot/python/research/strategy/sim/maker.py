"""Resting (maker) quotes against the replayed venue, with counterfactual fills.

A quote is a resting buy of Up at b (Up bid) or of Down at 1 - a (an Up ask at a, mirrored),
live at the venue from t_on = decision + L until its replacement's decision + L. Cancels and
non-marketable (post-only) orders are not held; marketable orders are held `hold` (150 ms)
before matching. Post-only: a quote that would cross the venue book at t_on is rejected.
Because the recording never contained our order, fills are inferred:

1. Book crossing: while our bid b is live, a venue ask posted at <= b would have been a
   marketable order against us: it is held `xhold` and then fills us (depth at those prices)
   if our bid is still live. xhold = hold is the real rule; xhold = 0 is a pessimistic bound.
2. Takers through our price: a recorded taker sale of Up exposure below b swept every bid
   at >= that price, ours included (fill = trade size).
3. Queue at our price: trades exactly at b first eat the depth that was resting at b when
   we joined; the excess fills us.
The Up ask side is symmetric. We pay no fee (maker rebates ignored)."""
from __future__ import annotations

import numpy as np


def _flow(tr: dict):
    """Recorded taker trades in the Up frame: venue time, +1 = taker bought Up exposure,
    Up-frame price, size."""
    o = np.argsort(tr["ts"], kind="stable")
    up = tr["up"][o].astype(bool)
    d = np.where(up, 1, -1) * tr["side"][o]
    p = np.where(up, tr["px"][o], 1 - tr["px"][o]).astype(float)
    return tr["ts"][o], d, np.round(p, 4), tr["size"][o].astype(float)


def _segment_fill(book, flow, s: int, k: int, t_on: float, t_off: float, size: float,
                  xhold: float):
    """Fill events (venue time, shares) of one quote. s = +1 Up bid at tick k, -1 Up ask."""
    g0, g1 = int(book.g_ceil(t_on)), int(book.g_floor(t_off))
    if g1 < g0:
        return []
    if (s > 0 and book.ba[g0] <= k) or (s < 0 and book.bb[g0] >= k):
        return []  # post-only reject
    ev = []
    if s > 0:
        cross = np.flatnonzero(book.ba[g0:g1 + 1] <= k)
        if len(cross) and book.t0 + (g0 + cross[0]) * 0.005 + xhold <= t_off:
            g = g0 + cross[0]
            ev.append((book.t0 + g * 0.005 + xhold, float(book.size[g, 101:101 + k].sum())))
        ahead = float(book.size[g0, k]) if book.bb[g0] >= k else 0.0
    else:
        cross = np.flatnonzero(book.bb[g0:g1 + 1] >= k)
        if len(cross) and book.t0 + (g0 + cross[0]) * 0.005 + xhold <= t_off:
            g = g0 + cross[0]
            ev.append((book.t0 + g * 0.005 + xhold, float(book.size[g, k:100].sum())))
        ahead = float(book.size[g0, 100 + k]) if book.ba[g0] <= k else 0.0
    ts, d, p, sz = flow
    a, b = np.searchsorted(ts, [t_on, t_off])
    px = k / 100
    for j in range(a, b):
        if d[j] == -s:  # bid: hit by sellers of Up exposure; ask: lifted by buyers
            if (s > 0 and p[j] < px - 1e-9) or (s < 0 and p[j] > px + 1e-9):
                ev.append((ts[j], sz[j]))
            elif abs(p[j] - px) < 1e-9:
                eat = min(ahead, sz[j])
                ahead -= eat
                if sz[j] - eat > 0:
                    ev.append((ts[j], sz[j] - eat))
    ev.sort()
    out, left = [], size
    for t, x in ev:
        if left <= 1e-9:
            break
        f = min(x, left)
        out.append((t, f))
        left -= f
    return out


def run(book, tr: dict, t, bid, ask, L: float, size: float = 60.0, max_open: float = 300.0,
        xhold: float = 0.150):
    """t: decision times (sorted); bid / ask: target Up-frame ticks per decision (0 = none).
    Returns fills: (venue time, side +1 Up / -1 Down, shares, price paid)."""
    flow = _flow(tr)
    fills, pos = [], {1: 0.0, -1: 0.0}
    for s, tgt in ((1, bid), (-1, ask)):
        chg = np.flatnonzero(np.r_[True, tgt[1:] != tgt[:-1]])
        for n, i in enumerate(chg):
            k = int(tgt[i])
            if k <= 0 or k >= 100:
                continue
            t_on = t[i] + L
            t_off = t[chg[n + 1]] + L if n + 1 < len(chg) else book.t0 + (book.n - 1) * 0.005
            if book.bad[book.g_ceil(t_on):book.g_floor(t_off) + 1].any():
                continue
            for tf, x in _segment_fill(book, flow, s, k, t_on, t_off, size, xhold):
                pay = k / 100 if s > 0 else 1 - k / 100
                fills.append((tf, s, x, pay))
    fills.sort()
    out = []
    for tf, s, x, pay in fills:  # inventory cap on the unpaired side, in time order
        net = pos[s] - pos[-s]
        x = min(x, max(0.0, max_open - net))
        if x > 0:
            pos[s] += x
            out.append((tf, s, x, pay))
    return out
