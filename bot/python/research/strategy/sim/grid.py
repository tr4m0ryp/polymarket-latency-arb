"""Dense replay of one market's Up book on a 5 ms grid, on two clocks.

Venue view (fills): `Book.size[g, c]` = shares resting at the matching engine at time
t0 + g * DT, rebuilt from the venue's own message stamps (`ts`, ms), so recorder backlog
cannot show depth that was already gone. Columns 0..99 = Up bids at tick c (price c / 100),
100..199 = Up asks at tick c - 100. Buying Down at q = hitting Up bids at 1 - q (mirrored).
Our view (decisions): `Book.bb_r / ba_r` = best bid / ask as our recorder had received it
(receipt clock `t`, no look-ahead). Polymarket's stamps sit a median ~16 ms before our
receipt with a 5 ms floor (network), so the two clocks agree to a few ms.

`Book.bad[g]` flags the recorder's socket gaps (messages lost); fills there are skipped."""
from __future__ import annotations

import numpy as np

from .. import DT


def _replay(tm, side, tick, size, t0: float, n: int) -> np.ndarray:
    """size[g, col] after applying every message with time <= t0 + g * DT, in order."""
    g = np.clip(np.ceil((tm - t0) / DT - 1e-9).astype(np.int64), 0, n - 1)
    seq = np.arange(len(tm), dtype=np.int64)
    col = np.where(side > 0, tick, 100 + tick)
    snap = np.flatnonzero(side == 0)  # a snapshot clears the book at its position
    lv = side != 0
    G = np.concatenate([g[lv], np.repeat(g[snap], 200)])
    S = np.concatenate([seq[lv], np.repeat(seq[snap], 200)])
    C = np.concatenate([col[lv], np.tile(np.arange(200, dtype=np.int64), len(snap))])
    V = np.concatenate([size[lv].astype(np.float32), np.zeros(200 * len(snap), np.float32)])
    o = np.lexsort((S, G, C))
    G, C, V = G[o], C[o], V[o]
    last = np.r_[(G[1:] != G[:-1]) | (C[1:] != C[:-1]), True]
    G, C, V = G[last], C[last], V[last]
    idx = np.full((n, 200), -1, dtype=np.int32)
    idx[G, C] = np.arange(len(G), dtype=np.int32)
    np.maximum.accumulate(idx, axis=0, out=idx)
    out = np.where(idx >= 0, V[np.clip(idx, 0, None)], 0).astype(np.float32)
    out[:, 0] = out[:, 100] = 0
    return out


def _top(sz: np.ndarray):
    has_b, has_a = sz[:, 1:100] > 0, sz[:, 101:200] > 0
    bb = np.where(has_b.any(1), 99 - np.argmax(has_b[:, ::-1], axis=1), 0).astype(np.int16)
    ba = np.where(has_a.any(1), 1 + np.argmax(has_a, axis=1), 100).astype(np.int16)
    return bb, ba


class Book:
    def __init__(self, ev: dict, t0: float, t1: float, gaps=()):
        self.t0, self.n = t0, int(np.ceil((t1 - t0) / DT)) + 1
        t, ts = ev["t"], ev["ts"]
        side, tick, size = ev["side"], ev["tick"].astype(np.int64), ev["size"]
        lag = t - ts
        self.delay = float(np.nanmedian(lag)) if len(t) else np.nan
        ts = np.where(np.isfinite(ts), ts, t - self.delay)
        o = np.argsort(ts, kind="stable")
        self.size = _replay(ts[o], side[o], tick[o], size[o], t0, self.n)
        self.bb, self.ba = _top(self.size)
        self.bb_r, self.ba_r = _top(_replay(t, side, tick, size, t0, self.n))
        self.lag_p99 = float(np.nanpercentile(lag, 99)) if len(t) else np.nan
        self.bad = np.zeros(self.n, dtype=bool)
        for g0, g1 in gaps:
            a, b = self.g_floor(g0), self.g_floor(g1)
            self.bad[a:b + 1] = True

    def g_floor(self, t):
        """Row holding what was known by t (no look-ahead)."""
        return np.clip(np.floor((np.asarray(t) - self.t0) / DT + 1e-9).astype(np.int64), 0, self.n - 1)

    def g_ceil(self, t):
        """First row at or after t (conservative for fills: the book is at least as late)."""
        return np.clip(np.ceil((np.asarray(t) - self.t0) / DT - 1e-9).astype(np.int64), 0, self.n - 1)

    def mid(self, g, ours: bool = False):
        bb = (self.bb_r if ours else self.bb)[g].astype(float)
        ba = (self.ba_r if ours else self.ba)[g].astype(float)
        return np.where((bb > 0) & (ba < 100), (bb + ba) / 200, np.nan)
