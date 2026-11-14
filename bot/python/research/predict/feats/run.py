"""Build the per-market decision tables (feats/build.py) for every usable 5m market with
the perp feed: data/cache/predict/tab/<i>.npz.

    nice -n 10 python3 -m research.predict.feats.run [--workers 2] [--seg train,select]"""
from __future__ import annotations

import argparse
import time
from multiprocessing import Pool

import numpy as np

from .. import CACHE, segment
from ...strategy.eval.prep import usable
from ...strategy.ingest.load import Store
from ...strategy.sim.grid import Book
from .build import table

TAB = CACHE / "tab"
_st = None


def perp_trades(lo: float, hi: float) -> dict | None:
    parts = []
    for h in range(int(lo) // 3600, int(hi) // 3600 + 1):
        p = CACHE / f"ftr-{h}.npz"
        if p.exists():
            with np.load(p) as z:
                parts.append({k: z[k] for k in z.files})
    if not parts:
        return None
    d = {k: np.concatenate([p[k] for p in parts]) for k in parts[0]}
    w = (d["t"] > lo) & (d["t"] < hi)
    o = np.argsort(d["t"][w], kind="stable")
    return {k: v[w][o] for k, v in d.items()}


def one(i: int) -> str:
    global _st
    out = TAB / f"{i}.npz"
    if out.exists():
        return f"{i} cached"
    _st = _st or Store()
    t0 = time.time()
    m = _st.market(i)
    if m is None:
        return f"{i} empty"
    meta = m["meta"]
    book = Book(m["ev"], meta["start"] - 2, meta["end"] + 12, m["gaps"])
    ftr = perp_trades(meta["start"] - 420, meta["end"] + 35)
    d = table(m, book, ftr)
    if d is None:
        return f"{i} skipped"
    tmp = TAB / f"{i}.tmp.npz"
    np.savez(tmp, **d)
    tmp.rename(out)
    return f"{i} rows={len(d['t'])} {time.time() - t0:.1f}s"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--seg", default="train,select")
    ap.add_argument("--only", type=int, default=None)
    a = ap.parse_args()
    TAB.mkdir(parents=True, exist_ok=True)
    st = Store()
    segs = set(a.seg.split(","))
    ids = [i for i in usable(st) if segment(st.mk.start[i]) in segs]
    if a.only is not None:
        ids = [a.only]
    print("markets", len(ids), flush=True)
    with Pool(a.workers) as pool:
        for msg in pool.imap(one, ids, chunksize=6):
            print(msg, flush=True)


if __name__ == "__main__":
    main()
