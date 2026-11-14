"""One order's price ladder in its own side frame, its limits, and FAK sweeps on it.

Side +1 buys Up: lifts Up asks (book column 100 + tick). Side -1 buys Down at q: hits Up
bids at 1 - q (column 100 - tick in Down ticks), the research grid's mirrored layout. The
ladder runs from 1 c to seen + SPAN c (capped at 99 c), best price first.

Limits (LIMS): k<i> = seen + i c; pv<j> = the model's value price (seen + predicted 10 s
value + fee, i.e. the break-even price) minus j c, floored to the tick; fp<j> = the
settlement fair value fair_p minus j c."""
from __future__ import annotations

import numpy as np

from .. import FP, KS, LIMS, PV, SIZES, SPAN

FEE = 0.07


def fee(p):
    return FEE * p * (1 - p)


def ladder(side: int, seen: float) -> tuple[np.ndarray, np.ndarray, int]:
    """(cols, prices in the side frame, index of the seen tick)."""
    s_tick = int(round(seen * 100))
    ticks = np.arange(1, min(s_tick + SPAN, 99) + 1)
    cols = 100 + ticks if side > 0 else 100 - ticks
    return cols, ticks / 100.0, s_tick - 1


def limit_idx(o, n: int, s_idx: int) -> np.ndarray:
    """Ladder index of every limit in LIMS (-1 = below 1 c: never fills)."""
    pv = o.seen + o.edge + fee(o.seen)
    fp = o.fair_p if o.side > 0 else 1 - o.fair_p
    t = [s_idx + i for i in KS]
    t += [int(np.floor(pv * 100 + 1e-6)) - j - 1 for j in PV]
    t += [int(np.floor(fp * 100 + 1e-6)) - j - 1 if fp == fp else -1 for j in FP]
    assert len(t) == len(LIMS)
    return np.clip(np.array(t), -1, n - 1)


def sweep(avail: np.ndarray, px: np.ndarray, lim: np.ndarray):
    """Fill shares / cost / fee for every (limit, size): arrays (len(LIMS), len(SIZES))."""
    nl, ns = len(lim), len(SIZES)
    sh, cost, fe = np.zeros((nl, ns)), np.zeros((nl, ns)), np.zeros((nl, ns))
    a = np.maximum(avail, 0.0)
    cum = np.cumsum(a)
    prev = cum - a
    for li, hi in enumerate(lim):
        if hi < 0 or cum[hi] <= 0:
            continue
        aa, pp, pv = a[:hi + 1], px[:hi + 1], prev[:hi + 1]
        for si, q in enumerate(SIZES):
            take = np.clip(q - pv, 0, aa)
            got = take.sum()
            if got > 0:
                sh[li, si], cost[li, si], fe[li, si] = got, (take * pp).sum(), (take * fee(pp)).sum()
    return sh, cost, fe


def istar(avail: np.ndarray, s_idx: int, q: float = 60.0) -> tuple[float, float]:
    """Needed offset in cents at the match instant: (first price with depth, price where
    cumulative depth reaches q shares) minus seen; NaN when the ladder has none."""
    nz = np.flatnonzero(avail > 0)
    full = np.flatnonzero(np.cumsum(np.maximum(avail, 0)) >= q - 1e-9)
    return (float(nz[0] - s_idx) if len(nz) else np.nan, float(full[0] - s_idx) if len(full) else np.nan)


def takes(avail: np.ndarray, cols: np.ndarray, hi: int, q: float) -> list:
    """(col, shares) consumed by a size-q sweep to ladder index hi (3 s own-take memory)."""
    out, left = [], q
    for c, a in zip(cols[:hi + 1], avail[:hi + 1]):
        if left <= 1e-9:
            break
        if a > 0:
            x = min(float(a), left)
            out.append((int(c), x))
            left -= x
    return out
