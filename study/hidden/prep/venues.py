"""Parse one hour of the side recorder (study/hidden/venues.py) into compact tables.

Per venue: <v>_bk (t receipt, ts venue stamp, bid, ask, bid size, ask size) and <v>_tr (t, ts, px,
qty, sgn +1 taker buy). Venues: perp (Binance USD-M, raw trades + bookTicker), coinbase (BTC-USD;
top of book only from the ticker that follows each trade), okx (BTC-USDT-SWAP bbo-tbt and swap
trades), bybit (linear BTCUSDT orderbook.1 and trades)."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import pandas as pd

from clob import _lines

BK = ["t", "ts", "bid", "ask", "bq", "aq"]
TR = ["t", "ts", "px", "qty", "sgn"]


def _iso(s: str) -> float:
    return datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp()


def parse(v: str, p: Path) -> dict[str, pd.DataFrame]:
    bk, tr = [], []
    for t, raw in _lines(p):
        j = json.loads(raw)
        if v == "perp":
            d = j.get("data") or {}
            if j.get("stream", "").endswith("@trade"):
                tr.append((t, d["T"] / 1e3, float(d["p"]), float(d["q"]), -1 if d["m"] else 1))
            elif "b" in d:
                bk.append((t, d["T"] / 1e3, float(d["b"]), float(d["a"]), float(d["B"]), float(d["A"])))
        elif v == "coinbase":
            ty = j.get("type")
            if ty == "ticker" and j.get("best_bid"):
                bk.append((t, _iso(j["time"]), float(j["best_bid"]), float(j["best_ask"]),
                           float(j["best_bid_size"]), float(j["best_ask_size"])))
            elif ty == "match":  # side is the maker's side
                tr.append((t, _iso(j["time"]), float(j["price"]), float(j["size"]), -1 if j["side"] == "buy" else 1))
        elif v == "okx":
            ch = (j.get("arg") or {}).get("channel")
            inst = (j.get("arg") or {}).get("instId")
            for d in j.get("data") or []:
                if ch == "bbo-tbt" and d.get("bids") and d.get("asks"):
                    b, a = d["bids"][0], d["asks"][0]
                    bk.append((t, int(d["ts"]) / 1e3, float(b[0]), float(a[0]), float(b[1]), float(a[1])))
                elif ch == "trades" and inst == "BTC-USDT-SWAP":
                    tr.append((t, int(d["ts"]) / 1e3, float(d["px"]), float(d["sz"]), 1 if d["side"] == "buy" else -1))
        elif v == "bybit":
            topic = j.get("topic", "")
            d = j.get("data")
            if topic.startswith("orderbook") and d and d.get("b") and d.get("a"):
                b, a = d["b"][0], d["a"][0]
                if float(b[1]) > 0 and float(a[1]) > 0:
                    bk.append((t, j["ts"] / 1e3, float(b[0]), float(a[0]), float(b[1]), float(a[1])))
            elif topic.startswith("publicTrade"):
                for x in d or []:
                    tr.append((t, x["T"] / 1e3, float(x["p"]), float(x["v"]), 1 if x["S"] == "Buy" else -1))
    return {f"{v}_bk": pd.DataFrame(bk, columns=BK), f"{v}_tr": pd.DataFrame(tr, columns=TR)}
