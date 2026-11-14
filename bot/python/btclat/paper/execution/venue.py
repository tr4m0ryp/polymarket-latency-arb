"""The venue book of one market at past venue times, rebuilt from the logged level changes
(state/pm.py), on the research simulator's 5 ms grid (research/strategy/sim/grid.py):
row g holds every change with ceil((ts - t0) / DT - 1e-9) <= g, t0 = start - 2.

`fill` runs the research taker simulator (research/strategy/sim/taker.py `run`) unchanged
on a window of those rows: the order matches at t + L + hold against depth that survives
the race window J, walking levels best first up to its limit, taker fee 0.07 p (1 - p)."""
from __future__ import annotations

import math

import numpy as np

from research.strategy.sim import taker

from ..state.pm import top_of

DT = 0.005
MEMORY = taker.MEMORY


def g_ceil(x: float, t0: float) -> int:
    return math.ceil((x - t0) / DT - 1e-9)


def rows_at(book, t0: float, g_lo: int, g_hi: int, slack: float = 2.0) -> np.ndarray:
    """Sizes (rows g_lo..g_hi, 200 cols). Changes older than the window by > slack s are
    taken as applied (arrival order is venue order to within that)."""
    x_lo = t0 + g_lo * DT
    suffix = []
    for e in reversed(book.log):
        if e[0] < x_lo - slack:
            break
        suffix.append(e)
    suffix.reverse()
    sz = list(book.size)
    for ts, c, old, new in reversed(suffix):
        sz[c] = old
    rows = [g_ceil(e[0], t0) for e in suffix]
    out = np.zeros((g_hi - g_lo + 1, 200), np.float32)
    for g in range(g_lo, g_hi + 1):
        for j, e in enumerate(suffix):
            if rows[j] == g or (g == g_lo and rows[j] < g_lo):
                sz[e[1]] = e[3]
        out[g - g_lo] = sz
    return out


def mid_at(book, t0: float, x: float) -> float:
    g = g_ceil(x, t0)
    bb, ba = top_of(rows_at(book, t0, g, g)[0])
    return (bb + ba) / 200 if bb > 0 and ba < 100 else math.nan


class _Window:
    """Duck-typed research Book over rows g_lo..g_hi (what taker.run reads)."""

    def __init__(self, t0: float, g_lo: int, size: np.ndarray):
        self.t0, self.g_lo, self.size = t0, g_lo, size
        self.n = len(size)
        self.bad = np.zeros(self.n, bool)

    def g_ceil(self, t):
        g = np.ceil((np.asarray(t) - self.t0) / DT - 1e-9).astype(np.int64) - self.g_lo
        return np.clip(g, 0, self.n - 1)


def _cols(side: int, limit: float) -> np.ndarray:
    if side > 0:
        hi = int(np.floor(limit * 100 + 1e-6))
        return np.arange(101, 101 + min(hi, 99)) if hi >= 1 else np.arange(0)
    lo = int(np.ceil(100 - limit * 100 - 1e-6))
    return np.arange(99, max(lo, 1) - 1, -1) if lo <= 99 else np.arange(0)


def fill(book, t0: float, t: float, side: int, shares: float, limit: float, L: float,
         J: float, hold: float, taken: list) -> tuple[dict | None, list, list]:
    """Paper fill of one order decided at receipt time t. taken: this arm's earlier takes
    (t, col, shares), subtracted for MEMORY s as the simulator does. Returns (fill or None,
    new takes, visible levels [(price, avail)] up to the limit)."""
    tm = t + L + hold
    g_lo, g_hi = g_ceil(tm, t0), g_ceil(tm + J, t0)
    size = rows_at(book, t0, g_lo, g_hi)
    for tt, c, x in taken:
        if tt > t - MEMORY:
            size[:, c] = np.maximum(size[:, c] - x, 0)
    win = _Window(t0, g_lo, size)
    fills, _ = taker.run(win, np.array([t]), np.array([side]), np.array([shares]), np.array([limit]),
                         L, J, 1.0, hold)
    cols = _cols(side, limit)
    avail = size[:, cols].min(axis=0) if len(cols) else np.zeros(0)
    px = [((c - 100) / 100 if side > 0 else 1 - c / 100) for c in cols]
    levels = [(round(p, 2), float(a)) for p, a in zip(px, avail) if a > 0][:10]
    new, left = [], float(shares)
    for c, a in zip(cols, avail):
        if left <= 1e-9:
            break
        if a > 0:
            x = min(float(a), left)
            new.append((t, int(c), x))
            left -= x
    return (fills[0] if fills else None), new, levels
