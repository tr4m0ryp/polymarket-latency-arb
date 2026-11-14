"""Time split and per-market feature tables (cached under data/cache/strategy/feat/).

    nice -n 10 python3 -m research.strategy.eval.prep [--workers 2] [--micro]

Split (fixed before any tuning): train = every 5m market that opens before 2026-10-10 10:00
UTC (run 1 + the first 12 h of run 2), test = every later complete market. Run 1 has no perp
feed, so perp-based rules train on run 2 only. --micro writes the v2 tables (microprice
candidates and features, signals/features.py) to data/cache/strategy/feat2/."""
from __future__ import annotations

import argparse
from multiprocessing import Pool

import pandas as pd

from .. import CACHE
from ..ingest.load import Store
from ..sim.grid import Book
from ..signals.features import table

SPLIT = 1791626400  # 2026-10-10 10:00 UTC
RUN2 = 1791583200   # 2026-10-09 22:00 UTC
FEAT = CACHE / "feat"
FEAT2 = CACHE / "feat2"


def split(mk: pd.DataFrame) -> pd.Series:
    return pd.Series(["train" if s < SPLIT else "test" for s in mk["start"]], index=mk.index)


def usable(st: Store) -> list[int]:
    hrs = st.have
    ok = []
    for i, m in st.mk.iterrows():
        need = range(int(m["start"] - 420) // 3600, int(m["end"] + 35) // 3600 + 1)
        if m["slug"] in st.outcome and all(h in hrs for h in need):
            ok.append(i)
    return ok


_st, _micro = None, False


def _one(i: int) -> str:
    global _st
    p = (FEAT2 if _micro else FEAT) / f"{i}.pkl"
    if p.exists():
        return f"{i} cached"
    _st = _st or Store()
    m = _st.market(i)
    if m is None:
        return f"{i} empty"
    meta = m["meta"]
    book = Book(m["ev"], meta["start"] - 2, meta["end"] + 2, m["gaps"])
    df = table(m, book, _micro)
    df.to_pickle(p)
    return f"{i} rows={len(df)}"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--micro", action="store_true")
    a = ap.parse_args()
    global _micro
    _micro = a.micro
    (FEAT2 if a.micro else FEAT).mkdir(parents=True, exist_ok=True)
    ids = usable(Store())
    print("usable markets", len(ids), flush=True)
    # contiguous chunks per worker keep the hour cache warm
    with Pool(a.workers) as pool:
        for msg in pool.imap(_one, ids, chunksize=12):
            print(msg, flush=True)


if __name__ == "__main__":
    main()
