"""Replay one token's CLOB book from the flat clob table (load._clob).

Polymarket books are mirrored (an Up bid at p is a Down ask at 1 - p), so the
Up token's book carries both sides of the trade: buying Down = hitting Up bids."""
from __future__ import annotations

import numpy as np
import pandas as pd


def replay(rows: pd.DataFrame, asset: str, queries: np.ndarray):
    """Return (top, snaps). top: DataFrame t, ts, bb, ba after every top change.
    snaps[i]: (bids, asks) dicts price -> size as seen at receipt time queries[i]
    (all messages with t <= queries[i] applied)."""
    r = rows[(rows["asset"] == asset) & (rows["kind"] < 2)]
    t, ts = r["t"].to_numpy(), r["ts"].to_numpy()
    side, px, sz = r["side"].to_numpy(), r["price"].to_numpy(), r["size"].to_numpy()
    q = np.sort(np.asarray(queries, dtype=float))
    bids: dict[float, float] = {}
    asks: dict[float, float] = {}
    tops, snaps, qi, last = [], [], 0, (np.nan, np.nan)
    n = len(t)
    for i in range(n):
        while qi < len(q) and q[qi] < t[i]:
            snaps.append((dict(bids), dict(asks)))
            qi += 1
        s = side[i]
        if s == 0:  # snapshot marker
            bids.clear()
            asks.clear()
        else:
            book = bids if s > 0 else asks
            p = round(px[i], 4)
            if sz[i] > 0:
                book[p] = sz[i]
            else:
                book.pop(p, None)
        if i + 1 < n and t[i + 1] == t[i]:
            continue  # apply the whole message before reading the top
        top = (max(bids) if bids else np.nan, min(asks) if asks else np.nan)
        if top != last:
            tops.append((t[i], ts[i], *top))
            last = top
    while qi < len(q):
        snaps.append((dict(bids), dict(asks)))
        qi += 1
    return pd.DataFrame(tops, columns=["t", "ts", "bb", "ba"]), snaps


def top_at(top: pd.DataFrame, when: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Best bid / ask in effect at each receipt time."""
    i = np.searchsorted(top["t"].to_numpy(), when, side="right") - 1
    ok = i >= 0
    bb = np.where(ok, top["bb"].to_numpy()[np.clip(i, 0, None)], np.nan)
    ba = np.where(ok, top["ba"].to_numpy()[np.clip(i, 0, None)], np.nan)
    return bb, ba
