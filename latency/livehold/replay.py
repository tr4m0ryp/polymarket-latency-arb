"""Per-token event streams on the venue clock and book replay at chosen instants.

The paper box receives the CLOB websocket with a lag of 80 ms median and > 1 s p90 behind the
venue `timestamp`, so every replay orders and cuts events by the venue timestamp (ms), never
by receipt time. A `book` message resets one side-pair; `price_change` sets the new total size
at a level (side BUY = bid, SELL = ask); `last_trade_price` is a match, side = taker side."""
from __future__ import annotations

import gzip
import json
from collections import defaultdict

from . import TAPE


def streams(tokens: set[str]) -> dict[str, list]:
    """token -> time-sorted [(venue_s, kind, payload)]; kind in book, pc, trade."""
    out = defaultdict(list)
    with gzip.open(TAPE / "ours.tsv.gz", "rt") as fh:
        for line in fh:
            d = json.loads(line.split("\t", 1)[1])
            for e in (d if isinstance(d, list) else [d]):
                k, ts = e.get("event_type"), e.get("timestamp")
                if ts is None:
                    continue
                t = int(ts) / 1000
                if k == "book" and e["asset_id"] in tokens:
                    out[e["asset_id"]].append((t, "book", (
                        {float(x["price"]): float(x["size"]) for x in e["bids"]},
                        {float(x["price"]): float(x["size"]) for x in e["asks"]})))
                elif k == "price_change":
                    for c in e["price_changes"]:
                        if c["asset_id"] in tokens:
                            out[c["asset_id"]].append((t, "pc", (c["side"], float(c["price"]), float(c["size"]))))
                elif k == "last_trade_price" and e["asset_id"] in tokens:
                    out[e["asset_id"]].append((t, "trade", (e["side"], float(e["price"]), float(e["size"]))))
    for v in out.values():
        v.sort(key=lambda x: x[0])
    return out


class Replay:
    """Walk one token's stream forward; `at(t)` returns (bids, asks) as of venue time t."""

    def __init__(self, ev: list):
        self.ev, self.i = ev, 0
        self.bids: dict[float, float] = {}
        self.asks: dict[float, float] = {}
        self.ok = False                       # a snapshot has been seen

    def at(self, t: float):
        ev = self.ev
        while self.i < len(ev) and ev[self.i][0] <= t:
            _, k, p = ev[self.i]
            if k == "book":
                self.bids, self.asks, self.ok = dict(p[0]), dict(p[1]), True
            elif k == "pc":
                side, px, sz = p
                book = self.bids if side == "BUY" else self.asks
                if sz <= 0:
                    book.pop(px, None)
                else:
                    book[px] = sz
            self.i += 1
        return self.bids, self.asks


def best(bids, asks):
    bb = max((p for p, s in bids.items() if s > 0), default=None)
    ba = min((p for p, s in asks.items() if s > 0), default=None)
    return bb, ba


def sweep(asks, limit: float, shares: float):
    """FAK BUY of `shares` up to `limit` against `asks`: (filled shares, vwap) or (0, None)."""
    got = cost = 0.0
    for p in sorted(a for a in asks if a <= limit + 1e-9):
        take = min(asks[p], shares - got)
        got, cost = got + take, cost + take * p
        if got >= shares - 1e-9:
            break
    return (got, cost / got) if got > 0 else (0.0, None)
