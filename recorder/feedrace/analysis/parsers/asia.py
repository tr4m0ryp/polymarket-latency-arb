"""Coinbase, Bybit and OKX (the original side venues)."""
from __future__ import annotations

from .common import _iso_us, _us


def coinbase(m: dict, out: list, st: dict) -> None:
    t = m.get("type")
    if t == "ticker" and m.get("best_bid") and m.get("best_ask"):
        mid = (float(m["best_bid"]) + float(m["best_ask"])) / 2
        out.append((1, m["sequence"], -1, mid, _iso_us(m["time"]), -1))
    elif t == "match":
        out.append((0, m["trade_id"], -1, float(m["price"]), _iso_us(m["time"]), -1))


def bybit(m: dict, out: list, st: dict) -> None:
    top = m.get("topic", "")
    if top.startswith("publicTrade"):
        for x in m["data"]:
            out.append((0, -1, -1, float(x["p"]), _us(m.get("ts")), _us(x.get("T"))))
    elif top.startswith("orderbook"):
        d = m["data"]
        if d.get("b"):
            st["b"] = float(d["b"][0][0])
        if d.get("a"):
            st["a"] = float(d["a"][0][0])
        if "a" in st and "b" in st:
            out.append((1, d.get("u", -1), -1, (st["a"] + st["b"]) / 2, _us(m.get("ts")),
                        _us(m.get("cts"))))


def okx(m: dict, out: list, st: dict) -> None:
    ch = m.get("arg", {}).get("channel")
    for x in m.get("data", ()):
        if ch == "trades":
            out.append((0, int(x["tradeId"]), -1, float(x["px"]), _us(x["ts"]), -1))
        elif ch == "bbo-tbt" and x.get("bids") and x.get("asks"):
            mid = (float(x["bids"][0][0]) + float(x["asks"][0][0])) / 2
            out.append((1, int(x.get("seqId", -1)), -1, mid, _us(x["ts"]), -1))
