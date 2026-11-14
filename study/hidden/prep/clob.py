"""Stream-parse one hour of the 5m CLOB log into compact tables (low RAM).

prints: every last_trade_price (t receipt s, ts venue s, market, asset, side +1 BUY / -1 SELL,
        price, size, tx hash). Joined to Data API fills by tx hash in attrib.py.
levels: every level change of each market's Up-token book (t, ts, market, side +1 bid / -1 ask,
        price, new size; side 0 = snapshot marker). Books are mirrored, so Up carries both sides.
tops:   Up-token top of book after every message that changes it (bb, ba, bid/ask size at top)."""
from __future__ import annotations

import gzip
import json
import zlib
from pathlib import Path

import numpy as np
import pandas as pd


def _lines(p: Path):
    try:
        with gzip.open(p, "rt") as fh:
            for line in fh:
                t, _, raw = line.rstrip("\n").partition("\t")
                if raw:
                    yield int(t) / 1e9, raw
    except (EOFError, zlib.error, gzip.BadGzipFile):
        return


class _Book:
    __slots__ = ("bids", "asks", "last")

    def __init__(self) -> None:
        self.bids: dict[float, float] = {}
        self.asks: dict[float, float] = {}
        self.last = None

    def top(self):
        bb = max(self.bids) if self.bids else np.nan
        ba = min(self.asks) if self.asks else np.nan
        return (bb, ba, self.bids.get(bb, 0.0), self.asks.get(ba, 0.0))


def parse(p: Path, up_of: dict[str, str]) -> dict[str, pd.DataFrame]:
    """up_of: condition_id -> Up asset id (5m markets)."""
    ups = set(up_of.values())
    books: dict[str, _Book] = {}
    prints, levels, tops = [], [], []
    for t, raw in _lines(p):
        if '"last_trade_price"' not in raw and '"price_change' not in raw and '"book"' not in raw:
            continue
        j = json.loads(raw)
        touched = set()
        for x in (j if isinstance(j, list) else [j]):
            ev, mk = x.get("event_type"), x.get("market")
            ts = float(x.get("timestamp") or "nan") / 1e3
            if ev == "last_trade_price":
                prints.append((t, ts, mk, x["asset_id"], 1 if x["side"] == "BUY" else -1,
                               float(x["price"]), float(x["size"]), x.get("transaction_hash", "")))
            elif ev == "book" and x["asset_id"] in ups:
                b = books.setdefault(mk, _Book())
                b.bids = {round(float(l["price"]), 4): float(l["size"]) for l in x["bids"]}
                b.asks = {round(float(l["price"]), 4): float(l["size"]) for l in x["asks"]}
                levels.append((t, ts, mk, 0, np.nan, np.nan))
                touched.add(mk)
            elif ev == "price_change":
                for c in x["price_changes"]:
                    if c["asset_id"] not in ups:
                        continue
                    b = books.setdefault(mk, _Book())
                    s = 1 if c["side"] == "BUY" else -1
                    px, sz = round(float(c["price"]), 4), float(c["size"])
                    d = b.bids if s > 0 else b.asks
                    if sz > 0:
                        d[px] = sz
                    else:
                        d.pop(px, None)
                    levels.append((t, ts, mk, s, px, sz))
                    touched.add(mk)
        for mk in touched:
            b = books[mk]
            top = b.top()
            if top != b.last:
                tops.append((t, ts, mk, *top))
                b.last = top
    return {
        "prints": pd.DataFrame(prints, columns=["t", "ts", "market", "asset", "side", "price", "size", "tx"]),
        "levels": pd.DataFrame(levels, columns=["t", "ts", "market", "side", "price", "size"]),
        "tops": pd.DataFrame(tops, columns=["t", "ts", "market", "bb", "ba", "bbs", "bas"]),
    }
