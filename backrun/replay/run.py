"""Replay every recorded market and store one row per order (Parquet, zstd).

    python -m backrun.replay.run [--procs 6]"""
from __future__ import annotations

import argparse
from multiprocessing import Pool

import numpy as np
import pandas as pd

from .. import OUT

_store = None


def _work(idx: np.ndarray) -> list[dict]:
    global _store
    from research.strategy.ingest.load import Store

    from .market import run_market
    _store = _store or Store(keep=3)
    rows = []
    for i in idx:
        m = _store.market(int(i))
        if m is not None:
            rows += run_market(m)
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--procs", type=int, default=6)
    a = ap.parse_args()
    from research.strategy.ingest.load import Store
    mk = Store().mk
    idx = np.flatnonzero((mk["fam"] == "5m").to_numpy())
    chunks = np.array_split(idx, max(1, len(idx) // 12))   # consecutive markets share hour files
    with Pool(a.procs) as pool:
        rows = [r for part in pool.imap(_work, chunks) for r in part]
    df = pd.DataFrame(rows)
    OUT.mkdir(parents=True, exist_ok=True)
    df.to_parquet(OUT / "rows.parquet", compression="zstd", index=False)
    span = (mk["end"].max() - mk["start"].min()) / 3600
    pd.Series({"markets_listed": len(idx), "markets_with_orders": df["slug"].nunique(),
               "hours_span": span, "t_first": float(mk["start"].min()),
               "t_last": float(mk["end"].max())}).to_json(OUT / "window.json")
    print(df.groupby("arm").size().to_dict(), df["slug"].nunique(), "markets", f"{span:.1f} h")


if __name__ == "__main__":
    main()
