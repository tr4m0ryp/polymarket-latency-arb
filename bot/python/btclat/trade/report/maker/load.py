"""A maker run's logs as frames (btclat/trade/maker/log.py streams): fills scored like the
simulator's fills (research/predict/sim/fills.py, maker: no fee): 10 s value from our book's
mid at t + 10 s (a missing mid valued at the outcome) and hold-to-resolution value; orders,
quotes, inferred fills, and the loop notes (`feed`, or raw/events when the run recorded)."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from recorder.live.sink import read_stream
from btclat.paper.report.load import outcomes

from ..load import rows


def notes(root: Path) -> list[dict]:
    out = []
    for d, name in ((root, "feed"), (root / "raw", "events")):
        out += [dict(json.loads(raw), t_ns=t) for t, raw in read_stream(name, root=d)]
    return sorted(out, key=lambda r: r["t_ns"])


def hours(ns: list[dict], fills: pd.DataFrame, quotes: pd.DataFrame) -> float:
    """Run length: trade_start to trade_stop (else to the last logged line), in hours."""
    st = [r["t_ns"] for r in ns if r.get("kind") == "trade_start"]
    en = [r["t_ns"] for r in ns if r.get("kind") == "trade_stop"]
    if st:
        last = en[-1] if en else max([r["t_ns"] for r in ns] + [0])
        return max(last - st[0], 0) / 3.6e12
    ts = pd.concat([fills.get("t_fill", pd.Series(dtype=float)), quotes.get("t", pd.Series(dtype=float))])
    return float(ts.max() - ts.min()) / 3600 if len(ts) > 1 else float("nan")


def fills(root: Path, gamma: bool = True) -> pd.DataFrame:
    df = pd.DataFrame(rows(root, "fills"))
    if not len(df):
        return df
    oc = outcomes(root, df["slug"].unique()) if gamma else {r["slug"]: r["outcome"] for r in rows(root, "settle")}
    df["outcome"] = df["slug"].map(oc).astype(float)
    df["won"] = np.where(df["up"].astype(bool), df["outcome"], 1 - df["outcome"])
    for c in ("shares", "cost", "mk10", "t_fill"):
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df["v10"] = df["shares"] * df["mk10"].fillna(df["won"]) - df["cost"]
    df["vres"] = df["shares"] * df["won"] - df["cost"]
    df["pull"] = df["pull_1s"].map({True: "pull <= 1 s", False: "no pull"}).fillna("unknown")
    return df


def frame(root: Path, name: str) -> pd.DataFrame:
    return pd.DataFrame(rows(root, name))


def copies(ns: list[dict]) -> pd.DataFrame:
    """One row per copy of a hedged insert / cancel."""
    out = [{"what": r["what"], "cid": r["cid"], "i": i, **c} for r in ns if r.get("kind") == "copies"
           for i, c in enumerate(r.get("copies") or [])]
    return pd.DataFrame(out)
