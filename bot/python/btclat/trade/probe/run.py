"""Probe mode: zero fill risk. Every `every` s (floor 5 s, cap 120 per hour) on the current
BTC 5m market's Up token: read the book (separate public session), post a post-only GTC BUY
of 5 shares at 0.01, cancel it at once. Never marketable: the price must sit at least 5 ticks
under the best bid (`passive_price`), asserted again right before sending, and post-only makes
the venue reject rather than take if the book moved.

Cycles alternate warm (1 GET /time per s for `warm_n` s before the order) and idle (the order
session silent for the whole period), to measure the keep-alive effect on the POST round trip.
Logged per cycle: sign time, POST ack and cancel round trips (ns clock), HTTP status, error
kind, Cloudflare POP, rate-limit headers, idle time of the connection. A probe order that
reports any fill, a failed cancel or a region / auth rejection stops the run (cancel-all)."""
from __future__ import annotations

import json
import time
from collections import deque

from recorder.live import markets as lm

from ..risk.limits import VENUE_MIN_SHARES, Limits
from ..risk.session import Stop
from ..venue import parse

PRICE, GAP_TICKS = 0.01, 5
FATAL = ("geoblock", "closed_only", "banned", "auth", "forbidden")


class Marketable(AssertionError):
    pass


def passive_price(bb: float, price: float = PRICE, gap_ticks: int = GAP_TICKS) -> float | None:
    """`price` if it is at least gap_ticks under the best bid, else None (skip the cycle)."""
    if not (bb == bb) or bb <= 0:
        return None
    return price if round(price * 100) <= round(bb * 100) - gap_ticks else None


def assert_passive(price: float, bb: float) -> None:
    if passive_price(bb, price) != price:
        raise Marketable(f"probe price {price} not <= best bid {bb} - {GAP_TICKS} ticks")


class Markets:
    def __init__(self, fetch=lm.fetch):
        self.fetch, self.cache = fetch, {}

    def current(self, now: float, margin: float = 20.0) -> dict | None:
        start = int(now) // 300 * 300
        if now > start + 300 - margin:
            return None
        if start not in self.cache:
            self.cache[start] = self.fetch("5m", start)
        return self.cache[start]


def run(venue, session, log, a, limits: Limits, now=time.time, sleep=time.sleep, markets=None) -> dict:
    markets = markets or Markets()
    every = max(float(a.every), limits.min_probe_every)
    sends: deque = deque()
    n = {"cycles": 0, "sent": 0, "skipped": 0, "cancelled": 0, "rejected": 0}
    t_end = now() + a.hours * 3600 if a.hours else float("inf")
    while (a.n is None or n["cycles"] < a.n) and now() < t_end:
        session.check()
        t0 = now()
        warm = a.warm == "warm" or (a.warm == "both" and n["cycles"] % 2 == 0)
        rec = {"cycle": n["cycles"], "warm": warm}
        while sends and sends[0] <= t0 - 3600:
            sends.popleft()
        m = markets.current(t0)
        if len(sends) >= limits.max_probe_hour:
            rec["decision"] = "skip:max_probe_hour"
        elif m is None:
            rec["decision"] = "skip:no_market"
        else:
            if warm:
                rec["ping_ms"] = []
                for _ in range(a.warm_n):
                    rec["ping_ms"].append(round(venue.ping().ms, 3))
                    sleep(1.0)
            session.check()
            _cycle(venue, m, rec, sends, now)
        n["cycles"] += 1
        d = rec["decision"]
        n["sent" if d == "sent" else "skipped"] += 1
        n["cancelled"] += bool(rec.get("cancelled"))
        n["rejected"] += bool(rec.get("err_kind"))
        log(rec)
        if rec.get("err_kind") in FATAL:
            raise Stop(f"probe rejected: {rec['err_kind']}: {rec.get('err')}")
        if rec.get("stop"):
            raise Stop(rec["stop"])
        wait = every - (now() - t0)
        if rec.get("err_kind") == "rate_limited":
            wait = max(wait, float(rec["post"]["hdr"].get("retry-after", 60)))
        if wait > 0 and (a.n is None or n["cycles"] < a.n):
            sleep(wait)
    return n


def _cycle(venue, m: dict, rec: dict, sends: deque, now) -> None:
    token = m["up"]
    bk = venue.book(token)
    rec.update(slug=m["slug"], token=token, bb=bk["bb"], ba=bk["ba"], book_ms=round(bk["resp"].ms, 3))
    price = passive_price(bk["bb"])
    if price is None:
        rec["decision"] = "skip:book_too_low"
        return
    assert_passive(price, bk["bb"])
    s = venue.sign(token, price, VENUE_MIN_SHARES, "BUY", "GTC", post_only=True)
    if not (s.post_only and s.order_type == "GTC" and s.price == price):   # not an assert: survives -O
        raise Marketable(f"probe order not post-only GTC at {price}: {s.order_type} {s.post_only} {s.price}")
    r = venue.post(s)
    sends.append(now())
    o = parse.order(r)
    rec.update(decision="sent", price=price, size=VENUE_MIN_SHARES, sign_us=round(s.sign_us, 1),
               t_send_ns=r.t_send_ns, t_ack_ns=r.t_ack_ns, post=r.brief(), **o)
    if o["fill_sh"] > 0 or o["status"] == "matched":
        rec["stop"] = "probe order reported a fill: stopping (should be impossible)"
    if o["order_id"]:
        c = venue.cancel(o["order_id"])
        rec["cancel"] = c.brief()
        rec["cancelled"] = parse.cancelled(c, o["order_id"])
        if not rec["cancelled"]:
            rec["stop"] = f"cancel of {o['order_id']} not confirmed: stopping (cancel-all on exit)"


def logger(sink, clock_ns=time.time_ns):
    def log(rec: dict) -> None:
        sink.write(clock_ns(), json.dumps(rec, default=str))
    return log
