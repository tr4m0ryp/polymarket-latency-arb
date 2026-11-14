"""Venues with engines in London or the US: Deribit, Bitstamp, Kraken spot/futures, LMAX, Bullish."""
from __future__ import annotations

from .common import _iso_us, _us


def deribit(m: dict, out: list, st: dict) -> None:
    p = m.get("params") or {}
    ch, d = p.get("channel", ""), p.get("data")
    if ch.startswith("quote."):
        out.append((1, -1, -1, (d["best_bid_price"] + d["best_ask_price"]) / 2,
                    _us(d["timestamp"]), -1))
    elif ch.startswith("trades."):
        for x in d:
            out.append((0, x.get("trade_seq", -1), -1, float(x["price"]), _us(x["timestamp"]), -1))


def bitstamp(m: dict, out: list, st: dict) -> None:
    d, ch = m.get("data") or {}, m.get("channel", "")
    if m.get("event") == "trade":
        out.append((0, d["id"], -1, float(d["price"]), int(d["microtimestamp"]), -1))
    elif m.get("event") == "data" and ch.startswith("order_book") and d.get("bids") and d.get("asks"):
        mid = (float(d["bids"][0][0]) + float(d["asks"][0][0])) / 2
        out.append((1, -1, -1, mid, int(d["microtimestamp"]), -1))


def kraken_spot(m: dict, out: list, st: dict) -> None:
    ch = m.get("channel")
    for x in m.get("data", ()) if ch in ("ticker", "trade") else ():
        if ch == "ticker" and x.get("bid") and x.get("ask"):
            ts = _iso_us(x["timestamp"]) if x.get("timestamp") else -1
            out.append((1, -1, -1, (x["bid"] + x["ask"]) / 2, ts, -1))
        elif ch == "trade":
            out.append((0, x.get("trade_id", -1), -1, float(x["price"]), _iso_us(x["timestamp"]), -1))


def kraken_fut(m: dict, out: list, st: dict) -> None:
    if m.get("product_id") != "PF_XBTUSD":
        return
    f = m.get("feed")
    if f == "ticker" and m.get("bid") and m.get("ask"):
        out.append((1, m.get("seq", -1), -1, (m["bid"] + m["ask"]) / 2, _us(m.get("time")), -1))
    elif f == "trade":
        out.append((0, m.get("seq", -1), -1, float(m["price"]), _us(m.get("time")), -1))


def lmax(m: dict, out: list, st: dict) -> None:
    if m.get("type") == "ORDER_BOOK" and m.get("bids") and m.get("asks"):
        mid = (float(m["bids"][0]["price"]) + float(m["asks"][0]["price"])) / 2
        out.append((1, -1, -1, mid, _iso_us(m["timestamp"]), -1))


def bullish(m: dict, out: list, st: dict) -> None:
    d = m.get("data")
    if m.get("dataType") == "V1TALevel1" and d and d.get("bid") and d.get("ask"):
        mid = (float(d["bid"][0]) + float(d["ask"][0])) / 2
        out.append((1, int(d.get("sequenceNumber", -1)), -1, mid,
                    _us(d.get("publishedAtTimestamp")), _us(d.get("timestamp"))))
