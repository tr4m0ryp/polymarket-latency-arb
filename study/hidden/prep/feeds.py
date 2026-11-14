"""Parse one hour of the price feeds into compact tables.

spot   Binance BTCUSDT: trades (t, ts = trade time, px, qty, buyer_maker) and bookTicker (t, bid, ask,
       bid_qty, ask_qty; spot bookTicker carries no venue stamp).
perp   Binance USD-M BTCUSDT bookTicker (t, ts, bid, ask, sizes) and, when present, raw trades.
chain  Chainlink BTC/USD via Polymarket RTDS (t, obs, ts, px)."""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from clob import _lines


def binance(p: Path, ts_key: str | None) -> dict[str, pd.DataFrame]:
    """ts_key: venue stamp of bookTicker ('T' on the perp, None on spot)."""
    tr, bk = [], []
    for t, raw in _lines(p):
        j = json.loads(raw)
        d = j.get("data") or {}
        s = j.get("stream", "")
        if s.endswith("@trade") or s.endswith("@aggTrade"):
            tr.append((t, d["T"] / 1e3, float(d["p"]), float(d["q"]), int(bool(d["m"]))))
        elif "b" in d and "a" in d:
            ts = d[ts_key] / 1e3 if ts_key else float("nan")
            bk.append((t, ts, float(d["b"]), float(d["a"]), float(d["B"]), float(d["A"])))
    return {"trades": pd.DataFrame(tr, columns=["t", "ts", "px", "qty", "bm"]),
            "book": pd.DataFrame(bk, columns=["t", "ts", "bid", "ask", "bq", "aq"])}


def chainlink(p: Path) -> pd.DataFrame:
    rows = []
    for t, raw in _lines(p):
        j = json.loads(raw)
        pl = j.get("payload") or {}
        if j.get("type") == "update" and "value" in pl:
            rows.append((t, pl["timestamp"] / 1e3, j["timestamp"] / 1e3, float(pl["value"])))
    return pd.DataFrame(rows, columns=["t", "obs", "ts", "px"])
