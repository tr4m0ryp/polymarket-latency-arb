"""One working order and one quote slot (market x side).

A slot holds the rule's target tick and AT MOST ONE working order; the order manager frees
the slot only when the venue has confirmed the order gone (cancel confirmed, rejected, fully
filled, or looked up as no longer resting). Order states: inserting -> live -> cancelling ->
done. Times: `t_dec` decision (s, SNTP clock), `t_on` / `t_off` when the order was resting at
the venue (dry: exact; live: send + RTT / 2 of the first ack).

`settled`: the order's final matched size is known. A live order leaves the book (cancel
confirmed or "gone", expiry) before its fills are known for sure (the venue's order lookup
lags; fills/settle.py), so until it settles its unfilled notional still counts as exposure
(`at_risk`), exactly as if it were resting."""
from __future__ import annotations

import math
from collections import deque
from dataclasses import dataclass, field

from ...risk.book import Intent
from ..arm import price as quote_price

NAN = math.nan


@dataclass
class Working:
    cid: str
    slug: str
    side: str                 # "bid": BUY Up at tick; "ask": BUY Down at 1 - tick
    token: str
    up: bool
    tick: int
    price: float
    size: float
    end: float
    otype: str = "GTD"
    expiration: int = 0
    state: str = "inserting"
    oid: str | None = None
    t_dec: float = NAN
    t_on: float = NAN
    t_off: float = NAN
    t_cancel: float = NAN
    matched: float = 0.0
    cancel_tries: int = 0
    settled: bool = False
    quote: dict = field(default_factory=dict)

    @property
    def resting(self) -> float:
        """$ this order can still be filled for."""
        return 0.0 if self.state == "done" else self.price * max(self.size - self.matched, 0.0)

    @property
    def at_risk(self) -> float:
        """$ that may still turn out filled: resting, or gone from the book but not settled."""
        if self.state == "done" and self.settled:
            return 0.0
        return self.price * max(self.size - self.matched, 0.0)

    def intent(self) -> Intent:
        return Intent("maker", self.slug, self.token, self.up, self.price, self.size, self.end)

    def brief(self) -> dict:
        return {"cid": self.cid, "oid": self.oid, "slug": self.slug, "side": self.side, "tick": self.tick,
                "price": self.price, "size": self.size, "token": self.token, "otype": self.otype,
                "expiration": self.expiration, "state": self.state, "matched": self.matched,
                "settled": self.settled}


@dataclass
class Slot:
    slug: str
    side: str
    token: str
    up: bool
    end: float
    target: int = 0
    t_target: float = -math.inf
    cause: str = "init"
    last_dec: float = -math.inf
    order: Working | None = None
    backoff: float = 0.0
    skip: str | None = None
    ctx: dict = field(default_factory=dict)
    pulls: deque = field(default_factory=deque)    # (t, pulled) at each change of the pull flag

    @classmethod
    def of(cls, meta: dict, side: str) -> "Slot":
        up = side == "bid"
        return cls(meta["slug"], side, meta["up"] if up else meta["down"], up, float(meta["end"]))

    def price(self, tick: int) -> float:
        return quote_price(self.side, tick)

    def note_pull(self, t: float, pulled: bool, keep: float = 60.0) -> None:
        if not self.pulls or self.pulls[-1][1] != pulled:
            self.pulls.append((t, pulled))
        while len(self.pulls) > 1 and self.pulls[1][0] < t - keep:
            self.pulls.popleft()

    def pulled_within(self, a: float, b: float) -> bool | None:
        """Was the pull condition on at a, or switched on in (a, b]? None if unknown at a."""
        state = None
        for t, p in self.pulls:
            if t <= a:
                state = p
            elif t <= b and p:
                return True
        return state
