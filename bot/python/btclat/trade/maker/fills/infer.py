"""Inferred fills of our resting quotes: the simulator's maker fill rule (research/strategy/sim/
maker.py `_segment_fill`) on the live tape, per order, in venue time.

A quote rests from t_on to t_off (the manager's ack times). While it rests:
1. trade through: a tape trade selling Up exposure below our bid (buying it above our ask)
   swept our price: fill = trade size;
2. queue: trades exactly at our price first eat the depth that rested there when we joined
   (`ahead`), the excess fills us;
3. book crossing: our Up book showing an ask <= our bid (bid >= our ask) means an order that
   would have matched us: it fills us `xhold` s later (the venue's hold on marketable orders,
   0.27 s measured) with the depth at those prices, if we still rest then. First crossing only.
Fills stop at the quote's size. Dry runs trade on these fills; live runs log them next to the
real fills so the counterfactual rule itself gets checked."""
from __future__ import annotations

import math
from dataclasses import dataclass

INF = math.inf
GRACE = 0.10            # s: wait for a cancel ack before settling a crossing fill


@dataclass
class Seg:
    o: object
    s: int
    k: int
    t_on: float
    ahead: float
    left: float
    t_off: float = INF
    cross: tuple | None = None
    cross_done: bool = False


class Infer:
    def __init__(self, on_fill, book_of, xhold: float = 0.27):
        self.on_fill, self.book_of, self.xhold = on_fill, book_of, xhold
        self.segs: dict[str, list[Seg]] = {}
        self.n = {"segments": 0, "fills": 0, "trade": 0, "queue": 0, "cross": 0}

    def on_live(self, o) -> None:
        s = 1 if o.side == "bid" else -1
        bk = self.book_of(o.slug)
        ahead = float(bk.size[o.tick if s > 0 else 100 + o.tick]) if bk is not None else 0.0
        self.segs.setdefault(o.slug, []).append(Seg(o, s, o.tick, o.t_on, ahead, o.size - o.matched))
        self.n["segments"] += 1

    def on_off(self, o) -> None:
        for g in self.segs.get(o.slug, []):
            if g.o is o:
                g.t_off = o.t_off if math.isfinite(o.t_off) else g.t_off

    def on_trade(self, tr: dict) -> None:
        for g in self.segs.get(tr["slug"], []):
            ts = tr["ts"]
            if g.left <= 1e-9 or not g.t_on <= ts < g.t_off or tr["d"] != -g.s:
                continue
            px, p = g.k / 100, tr["p"]
            if (g.s > 0 and p < px - 1e-9) or (g.s < 0 and p > px + 1e-9):
                self._fill(g, tr["size"], ts, "trade")
            elif abs(p - px) < 1e-9:
                eat = min(g.ahead, tr["size"])
                g.ahead -= eat
                if tr["size"] - eat > 1e-9:
                    self._fill(g, tr["size"] - eat, ts, "queue")

    def on_book(self, m, t: float, ts: float) -> None:
        segs = self.segs.get(m.meta["slug"])
        if not segs:
            return
        bk = m.book
        tv = ts if ts == ts else t - bk.delay
        for g in segs:
            if g.cross is not None or g.left <= 1e-9 or not g.t_on <= tv < g.t_off:
                continue
            if g.s > 0 and bk.ba <= g.k:
                g.cross = (tv + self.xhold, sum(bk.size[100 + j] for j in range(1, g.k + 1)))
            elif g.s < 0 and bk.bb >= g.k:
                g.cross = (tv + self.xhold, sum(bk.size[j] for j in range(g.k, 100)))

    def on_tick(self, now: float) -> None:
        for slug, segs in list(self.segs.items()):
            for g in segs:
                if g.cross is not None and not g.cross_done and now >= g.cross[0] + GRACE:
                    g.cross_done = True
                    if g.cross[0] <= g.t_off and g.left > 1e-9:
                        self._fill(g, g.cross[1], g.cross[0], "cross")
            keep = [g for g in segs if g.left > 1e-9 and not g.t_off + 5 < now]
            if keep:
                self.segs[slug] = keep
            else:
                del self.segs[slug]

    def _fill(self, g: Seg, x: float, t: float, how: str) -> None:
        x = min(float(x), g.left)
        if x <= 1e-9:
            return
        g.left -= x
        self.n["fills"] += 1
        self.n[how] += 1
        self.on_fill(g.o, x, t, how)
