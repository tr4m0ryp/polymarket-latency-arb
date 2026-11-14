"""Everything the bot knows, updated per event: shared Binance state (`Ctx`) plus one
`MarketCtx` per subscribed 5m market. `apply` returns what changed, which the decision
layer turns into candidates."""
from __future__ import annotations

from ..features.raw import Ctx, MarketCtx


class World:
    def __init__(self):
        self.ctx = Ctx()
        self.mkts: dict[str, MarketCtx] = {}
        self.n_ev = 0

    def add_market(self, meta: dict) -> MarketCtx:
        if meta["slug"] not in self.mkts:
            self.mkts[meta["slug"]] = MarketCtx(meta)
        return self.mkts[meta["slug"]]

    def drop_old(self, now: float, after_end: float = 120.0) -> None:
        for s in [s for s, m in self.mkts.items() if m.end + after_end < now]:
            del self.mkts[s]

    def active(self, t: float) -> MarketCtx | None:
        """The market whose decision window (start + 3, end - 5) contains t."""
        for m in self.mkts.values():
            if m.start + 3 < t < m.end - 5:
                return m
        return None

    def apply(self, ev: tuple):
        """Update state. Returns (kind, market or None, flag): flag = mid changed for Binance
        books, top changed for a Polymarket book, price changed for a spot trade."""
        k = ev[0]
        self.n_ev += 1
        c = self.ctx
        if k == "pb":
            c.perp.update(ev[1], ev[3], ev[4], ev[5], ev[6])
            return k, None, c.perp.mid_changed
        if k == "sb":
            c.spot.update(ev[1], ev[3], ev[4], ev[5], ev[6])
            return k, None, c.spot.mid_changed
        if k == "st":
            c.flow.update(ev[1], ev[4], ev[5])
            c.settle.update(ev[1], ev[2], ev[3])
            s = c.settle
            return k, None, s.prev_lpx == s.prev_lpx and s.prev_lpx != s.last_lpx
        if k == "pm":
            m = self.mkts.get(ev[3])
            if m is None:
                return k, None, False
            return k, m, m.book.apply(ev[1], ev[2], ev[4], ev[5])
        if k == "mk":
            return k, self.add_market(ev[2]), False
        return k, None, False
