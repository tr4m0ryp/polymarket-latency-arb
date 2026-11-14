"""Orders of one 5m market and their fills on the venue-clock book at every delay.

Decisions use our receipt-clock view of the top of book (`Book.bb_r / ba_r`) and Binance
data received by then (`Feeds.ret`). Fills read `Book.size` (venue stamps, 5 ms rows) at the
first row at or after decision + d. Side +1 buys Up (lifts Up asks, column 100 + tick);
side -1 buys Down at q = hits Up bids at 1 - q (column 100 - tick)."""
from __future__ import annotations

import numpy as np

from research.strategy.signals.features import candidates
from research.strategy.signals.feeds import Feeds
from research.strategy.signals.rules import _refractory
from research.strategy.sim.grid import Book

from .. import ARMS, CLIP, DELAYS, GATE

MK_H = 10.0   # markout horizon, s


def _orders(fd: Feeds, book: Book, t: np.ndarray, arm: tuple):
    src, win, thr, refr = arm
    r = fd.ret(src, t, 0, win)
    g = book.g_floor(t)
    bb, ba = book.bb_r[g].astype(float), book.ba_r[g].astype(float)
    side = np.sign(r)
    seen = np.where(side > 0, ba / 100, 1 - bb / 100)
    mid = (bb + ba) / 200
    ok = (np.abs(r) >= thr) & (side != 0) & (bb > 0) & (ba < 100)
    ok &= (seen >= GATE["band"][0]) & (seen <= GATE["band"][1]) & (fd.end - t >= GATE["tleft"])
    ok &= np.maximum(mid, 1 - mid) <= GATE["fav_max"]
    ok &= ~book.bad[g] & ~book.bad[book.g_ceil(t + max(DELAYS) / 1e3)]
    i = _refractory(t, ok, refr)
    return t[i], side[i].astype(int), np.round(seen[i], 2), r[i]


def _fill(book: Book, g: int, side: int, s_tick: int, want: float):
    """(shares, cost, depth at <= limit) of a FAK sweep up to the seen tick at grid row g."""
    ticks = np.arange(1, s_tick + 1)
    cols = 100 + ticks if side > 0 else 100 - ticks
    avail = book.size[g, cols].astype(float)
    take = np.clip(want - (np.cumsum(avail) - avail), 0, avail)
    return float(take.sum()), float((take * ticks / 100).sum()), float(avail.sum())


def _side_mid(book: Book, g: int, side: int) -> float:
    m = float(book.mid(g))
    return m if side > 0 else 1 - m


def run_market(m: dict) -> list[dict]:
    meta, out = m["meta"], []
    if m["outcome"] is None or not len(m["spot_tr"].get("t", [])):
        return out
    fd = Feeds(m)
    if np.isnan(fd.K):
        return out
    book = Book(m["ev"], meta["start"] - 2, meta["end"] + 2, m["gaps"])
    cand = candidates(fd, book)
    if not len(cand):
        return out
    for name, arm in ARMS.items():
        for t, side, seen, r in zip(*_orders(fd, book, cand, arm)):
            won = m["outcome"] if side > 0 else 1 - m["outcome"]
            s_tick, want = int(round(seen * 100)), CLIP / seen
            row = {"arm": name, "slug": meta["slug"], "hour": int(t // 3600), "t": float(t),
                   "side": int(side), "seen": float(seen), "move_bp": float(r), "won": float(won),
                   "want": want, "secs_left": float(fd.end - t)}
            for d in DELAYS:
                g = int(book.g_ceil(t + d / 1e3))
                sh, cost, depth = _fill(book, g, int(side), s_tick, want)
                gm = int(book.g_ceil(min(t + d / 1e3 + MK_H, fd.end + 2)))
                mk = _side_mid(book, gm, int(side))
                row.update({f"sh_{d}": sh, f"cost_{d}": cost, f"depth_{d}": depth,
                            f"mk10_{d}": mk if mk == mk else float(won)})
            out.append(row)
    return out
