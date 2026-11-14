"""Each order's i = 0 ladder (limit = seen) at decision + hold, per stored hold draw.

For order j and draw k the venue-clock book row at t + h_jk gives the side-frame asks at
ticks 1..seen (Down asks = Up bids at 1 - q). Only levels with depth are kept, best price
first, as flat arrays (book column, price, shares) indexed by off[j, k] .. off[j, k] + n[j, k].
Own takes are not subtracted here (the bankroll kernel does it with the sizes it sends)."""
from __future__ import annotations

import numpy as np

from research.strategy.sim.grid import Book

from .. import K


def market_ladders(m: dict, o, H: dict, rng) -> dict:
    """o: this market's orders (t, side, seen). H: scenario -> hold sample. Returns per
    scenario: h (n, K), and per draw lists of (col, px, sh) arrays."""
    meta = m["meta"]
    book = Book(m["ev"], meta["start"] - 2, meta["end"] + 2, m["gaps"])
    t, side = o["t"].to_numpy(float), o["side"].to_numpy(int)
    s_tick = np.rint(o["seen"].to_numpy(float) * 100).astype(int)
    out = {}
    for sc, hs in H.items():
        h = np.tile(hs, (len(t), K))[:, :K] if len(hs) == 1 else rng.choice(hs, (len(t), K))
        lad = []
        for j in range(len(t)):
            ticks = np.arange(1, s_tick[j] + 1)
            cols = 100 + ticks if side[j] > 0 else 100 - ticks
            g = book.g_ceil(t[j] + h[j])
            a = book.size[g][:, cols]                          # (K, ticks)
            row = []
            for k in range(K):
                nz = np.flatnonzero(a[k] > 0)
                row.append((cols[nz].astype(np.int16), ticks[nz].astype(np.int16), a[k, nz].astype(np.float32)))
            lad.append(row)
        out[sc] = (h.astype(np.float32), lad)
    return out
