"""In-process load at each send: raw feed messages the event loop handled in the second
before it (binance spot + futures + CLOB, from the run's --record files). The loop parses,
books and decides on every one of them while the sender threads need the GIL."""
from __future__ import annotations

import gzip
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

FEEDS = ("binance", "binance_fut", "clob_5m")


def per_second(root: Path, feeds=FEEDS) -> pd.Series:
    """Messages per wall-clock second (the recorded feeds named)."""
    n: Counter = Counter()
    for f in feeds:
        for p in sorted((root / "raw").glob(f"*/{f}-*.tsv.gz")):
            with gzip.open(p, "rb") as fh:
                for line in fh:
                    n[int(line[:10])] += 1
    return pd.Series(n, dtype=float).sort_index()


def attach(ops: pd.DataFrame, rate: pd.Series, col: str = "msgs_1s") -> pd.DataFrame:
    out = ops.copy()
    sec = (out["t_send_ns"] // 1_000_000_000).astype(int)
    out[col] = [rate.get(s - 1, np.nan) for s in sec]
    return out
