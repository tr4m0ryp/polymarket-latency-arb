"""Parse the live recorder's logs (recorder.live) into flat tables, cached as
pickle per hour file under data/cache/live/ (complete hours only).

Clock: `t` is the SNTP-corrected receipt time (s); `ts` is the venue's own
server stamp (s): Binance trade time T, Polymarket message timestamp,
Chainlink observation time."""
from __future__ import annotations

import gzip
import json
import sys
import time
import zlib
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
LIVE = ROOT / "data" / "live"
CACHE = ROOT / "data" / "cache" / "live"


def _lines(p: Path):
    try:
        with gzip.open(p, "rt") as fh:
            for line in fh:
                t, _, raw = line.rstrip("\n").partition("\t")
                if raw:
                    yield int(t) / 1e9, raw
    except (EOFError, zlib.error, gzip.BadGzipFile):
        return


def _binance(p: Path) -> pd.DataFrame:
    rows = []
    for t, raw in _lines(p):
        j = json.loads(raw)
        d = j["data"]
        if j["stream"].endswith("@trade"):
            rows.append((t, d["T"] / 1e3, float(d["p"]), float(d["q"]), 1))
        else:
            rows.append((t, np.nan, (float(d["b"]) + float(d["a"])) / 2, 0.0, 0))
    return pd.DataFrame(rows, columns=["t", "ts", "px", "qty", "is_trade"])


def _chainlink(p: Path) -> pd.DataFrame:
    rows = []
    for t, raw in _lines(p):
        j = json.loads(raw)
        pl = j.get("payload") or {}
        if j.get("type") == "update" and "value" in pl:
            rows.append((t, pl["timestamp"] / 1e3, j["timestamp"] / 1e3, float(pl["value"])))
    return pd.DataFrame(rows, columns=["t", "obs", "ts", "px"])


# kind: 0 snapshot level, 1 level change, 2 trade; side: +1 bid / taker buy, -1 ask / taker sell
def _clob(p: Path) -> pd.DataFrame:
    rows = []
    for t, raw in _lines(p):
        j = json.loads(raw)
        for x in (j if isinstance(j, list) else [j]):
            ev, mk = x.get("event_type"), x.get("market")
            ts = float(x.get("timestamp") or "nan") / 1e3
            if ev == "book":
                a = x["asset_id"]
                rows.append((t, ts, mk, a, 0, 0, np.nan, np.nan))  # snapshot marker: clear book
                rows += [(t, ts, mk, a, 0, 1, float(l["price"]), float(l["size"])) for l in x["bids"]]
                rows += [(t, ts, mk, a, 0, -1, float(l["price"]), float(l["size"])) for l in x["asks"]]
            elif ev == "price_change":
                for c in x["price_changes"]:
                    rows.append((t, ts, mk, c["asset_id"], 1, 1 if c["side"] == "BUY" else -1,
                                 float(c["price"]), float(c["size"])))
            elif ev == "last_trade_price":
                rows.append((t, ts, mk, x["asset_id"], 2, 1 if x["side"] == "BUY" else -1,
                             float(x["price"]), float(x["size"])))
    return pd.DataFrame(rows, columns=["t", "ts", "market", "asset", "kind", "side", "price", "size"])


PARSERS = {"binance": _binance, "chainlink": _chainlink, "clob_5m": _clob, "clob_15m": _clob}


def table(stream: str) -> pd.DataFrame:
    parts = []
    for p in sorted(LIVE.glob(f"*/{stream}-*.tsv.gz")):
        hour = int(p.name.split("-")[-1].split(".")[0])
        c = CACHE / f"{stream}-{hour}.pkl"
        if c.exists():
            parts.append(pd.read_pickle(c))
            continue
        df = PARSERS[stream](p)
        if (hour + 1) * 3600 < time.time() + 8.3 - 120 and len(df):  # complete hour
            CACHE.mkdir(parents=True, exist_ok=True)
            df.to_pickle(c)
        parts.append(df)
    df = pd.concat(parts, ignore_index=True) if parts else pd.DataFrame()
    return df.sort_values("t", kind="stable").reset_index(drop=True) if len(df) else df


def _lines_all(stream: str):
    for p in sorted(LIVE.glob(f"*/{stream}-*.tsv.gz")):
        yield from _lines(p)


def markets() -> pd.DataFrame:
    rows = [json.loads(raw) for p in sorted(LIVE.glob("*/markets-*.tsv.gz")) for _, raw in _lines(p)]
    return pd.DataFrame(rows).drop_duplicates("slug")
