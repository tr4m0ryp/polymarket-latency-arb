"""Offline pieces for the maker tests: a clock, ops whose acks the test releases by hand, a
market with a real Polymarket book (btclat.paper.state.pm), and a manager wired to a real
risk book and log. No network."""
from __future__ import annotations

import json
from types import SimpleNamespace

from btclat.paper.state.pm import PMBook
from btclat.trade.maker.log import MakerLog
from btclat.trade.maker.orders.manager import OrderManager
from btclat.trade.maker.orders.risk import MakerLimits, MakerRisk
from btclat.trade.risk.book import RiskBook
from btclat.trade.risk.limits import Limits

from ..fakes import ListSink

START = 1_791_800_100.0


class Clock:
    def __init__(self, t=START + 60.0):
        self.t = t

    def now(self):
        return self.t

    def now_ns(self):
        return int(self.t * 1e9)


class FakeOps:
    """Records every op; `ack(kind)` releases the oldest pending one with a result."""

    def __init__(self, clock):
        self.clock = clock
        self.pending: list = []
        self.calls: list = []

    def server_now(self):
        return self.clock.now()

    def _q(self, kind, o, cb):
        self.calls.append((kind, o.cid, o.tick, o.side))
        self.pending.append((kind, o, cb))

    def insert(self, o, cb):
        self._q("insert", o, cb)

    def cancel(self, o, cb):
        self._q("cancel", o, cb)

    def lookup(self, o, cb):
        self._q("lookup", o, cb)

    def n(self, kind):
        return sum(1 for c in self.calls if c[0] == kind)

    def ack(self, kind, **res):
        i = next(i for i, p in enumerate(self.pending) if p[0] == kind)
        _, o, cb = self.pending.pop(i)
        t = self.clock.now()
        base = {"insert": {"ok": True, "order_id": f"0x{o.cid}", "status": "live", "fill_sh": 0.0, "t_venue": t},
                "cancel": {"confirmed": True, "t_venue": t},
                "lookup": {"status": "LIVE", "fill_sh": o.matched, "unknown": False, "t_ack": t}}[kind]
        cb({**base, **res})
        return o


def book(bb=45, ba=55, size=100.0):
    b = PMBook()
    b.apply(START, START, True, [(1, bb, size), (-1, ba, size)])
    return b


def market(start=START, bb=45, ba=55, tick=0.01):
    meta = {"slug": f"btc-updown-5m-{int(start)}", "up": "UP", "down": "DN", "start": start, "end": start + 300,
            "tick": tick}
    return SimpleNamespace(meta=meta, start=start, end=start + 300, book=book(bb, ba))


def q(t, bid=47, ask=53, pull_bid=False, pull_ask=False, **kw):
    d = {"t": t, "bid": bid, "ask": ask, "pull_bid": pull_bid, "pull_ask": pull_ask, "pu": -0.05, "pdn": -0.05,
         "fair": 0.5, "bb": 45.0, "ba": 55.0, "mid": 0.5, "secs_left": 200.0}
    d.update(kw)
    return d


def manager(tmp_path, clock=None, limits=None, balance=73.0):
    clock = clock or Clock()
    ops = FakeOps(clock)
    rb = RiskBook(Limits(), tmp_path / "state", now=clock.now())
    rb.balance = balance
    sinks = {n: ListSink() for n in ("quotes", "ops", "fills", "infer")}
    m = market()
    log = MakerLog(sinks, clock.now_ns, lambda slug: m.book if slug == m.meta["slug"] else None)
    mgr = OrderManager(ops, MakerRisk(rb, limits or MakerLimits()), log, clock.now)
    log.pulled = mgr.pulled
    return SimpleNamespace(mgr=mgr, ops=ops, clock=clock, risk=rb, log=log, sinks=sinks, m=m)


def lines(sink) -> list[dict]:
    return [json.loads(r) for _, r in sink.lines]


def live_per_slot(mgr) -> dict:
    """Working orders per (slug, side): must never exceed 1."""
    out: dict = {}
    for o in mgr.working():
        out[(o.slug, o.side)] = out.get((o.slug, o.side), 0) + 1
    return out
