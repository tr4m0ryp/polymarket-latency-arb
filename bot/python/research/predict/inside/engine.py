"""Maker replay with live-probe latency and the rival-improver haircut.

The fill rules are research/strategy/sim/maker.py `_segment_fill` (book crossing after the
hold, takers through our price, queue at our price behind the depth there), with a source tag
(0 cross, 1 through, 2 queue), as in the fill-improve study's mk engine. Additions:

- Latency: insert and cancel delays are the min of `k` draws (hedged copies) from the warm
  Dublin probe quantiles (dublin-probe-20261013, p50 ~50 ms), shifted by L - 50 ms, so L = 50
  is the measured venue and L = 100 / 150 are slower ones. The cancel waits for the insert
  ack (the live manager's rule) unless ackwait=False.
- Haircut (rival improvers): a level at our price that shows in the book between our decision
  and one insert latency after our order went live (rivals sent before us whose acks / feed
  updates land later) is ahead of us. Its largest size is the queue ahead, and it is eaten by
  crossing orders as well as by prints at our price. Prints through our price still fill us
  (they cleared our whole level)."""
from __future__ import annotations

import numpy as np

QP = np.array([0, 10, 50, 90, 99, 100])
INS = np.array([30, 41.5, 56.4, 118.0, 577.3, 670.4]) / 1000
CAN = np.array([25, 35.8, 49.9, 113.4, 356.5, 475.8]) / 1000
DT = 0.005  # book grid step (research/strategy/sim/grid.py)


def draw(rng, q, k: int, shift: float) -> float:
    return float(np.interp(rng.uniform(0, 100, k), QP, q).min()) + shift


def _ahead(book, s: int, k: int, g0: int, g1: int) -> float:
    """Largest depth at our price over grid rows g0..g1 (bid k: level exists if bb >= k)."""
    g1 = max(g0, min(g1, book.n - 1))
    if s > 0:
        sz = np.where(book.bb[g0:g1 + 1] >= k, book.size[g0:g1 + 1, k], 0.0)
    else:
        sz = np.where(book.ba[g0:g1 + 1] <= k, book.size[g0:g1 + 1, 100 + k], 0.0)
    return float(sz.max()) if len(sz) else 0.0


def seg_fill(book, flow, s, k, t_on, t_off, size, xhold, hc_until=None, t_dec=None):
    """Fill events [(t, shares, src)] of one quote and whether post-only rejected it."""
    g0, g1 = int(book.g_ceil(t_on)), int(book.g_floor(t_off))
    if g1 < g0:
        return [], False
    if (s > 0 and book.ba[g0] <= k) or (s < 0 and book.bb[g0] >= k):
        return [], True
    ev = []
    lvl = book.ba[g0:g1 + 1] <= k if s > 0 else book.bb[g0:g1 + 1] >= k
    cross = np.flatnonzero(lvl)
    if len(cross) and book.t0 + (g0 + cross[0]) * DT + xhold <= t_off:
        g = g0 + cross[0]
        depth = book.size[g, 101:101 + k].sum() if s > 0 else book.size[g, k:100].sum()
        ev.append((book.t0 + g * DT + xhold, float(depth), 0))
    if hc_until is None:
        ahead = _ahead(book, s, k, g0, g0)
    else:
        ahead = _ahead(book, s, k, int(book.g_ceil(t_dec)), int(book.g_floor(hc_until)))
    ts, d, p, sz = flow
    a, b = np.searchsorted(ts, [t_on, t_off])
    px = k / 100
    for j in range(a, b):
        if d[j] == -s:
            if (s > 0 and p[j] < px - 1e-9) or (s < 0 and p[j] > px + 1e-9):
                ev.append((ts[j], sz[j], 1))
            elif abs(p[j] - px) < 1e-9:
                ev.append((ts[j], sz[j], 2))
    ev.sort()
    out, left = [], size
    for t, x, src in ev:
        if src == 2 or (src == 0 and hc_until is not None):
            eat = min(ahead, x)
            ahead -= eat
            x -= eat
        if left <= 1e-9:
            break
        if x <= 1e-9:
            continue
        f = min(x, left)
        out.append((t, f, src))
        left -= f
    return out, False


def run(book, flow, t, bid, ask, L=0.05, k=2, size=60.0, max_open=300.0, xhold=0.27, seed=0,
        haircut=False, ackwait=True):
    """Fills [(tf, side, shares, pay, src, t_on)] and {ins, rej} of target ticks per decision."""
    rng = np.random.default_rng(seed)
    shift = L - 0.05
    fills, ins, rej = [], 0, 0
    t_end = book.t0 + (book.n - 1) * DT
    for s, tgt in ((1, bid), (-1, ask)):
        chg = np.flatnonzero(np.r_[True, tgt[1:] != tgt[:-1]])
        for n, i in enumerate(chg):
            q = int(tgt[i])
            if q <= 0 or q >= 100:
                continue
            a = draw(rng, INS, k, shift)
            t_on = t[i] + a
            if n + 1 < len(chg):
                c = draw(rng, CAN, k, shift)
                t_off = (max(t[chg[n + 1]], t_on) if ackwait else t[chg[n + 1]]) + c
            else:
                t_off = t_end
            if book.bad[book.g_ceil(t_on):book.g_floor(t_off) + 1].any():
                continue
            ins += 1
            ev, r = seg_fill(book, flow, s, q, t_on, t_off, size, xhold,
                             t_on + a if haircut else None, t[i])
            rej += r
            for tf, x, src in ev:
                fills.append((tf, s, x, q / 100 if s > 0 else 1 - q / 100, src, t_on))
    fills.sort()
    pos, out = {1: 0.0, -1: 0.0}, []
    for tf, s, x, pay, src, ton in fills:
        x = min(x, max(0.0, max_open - (pos[s] - pos[-s])))
        if x > 0:
            pos[s] += x
            out.append((tf, s, x, pay, src, ton))
    return out, {"ins": ins, "rej": rej}
