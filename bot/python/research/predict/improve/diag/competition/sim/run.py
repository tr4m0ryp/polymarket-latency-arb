"""Run the competition diagnostic on allowed windows (one heavy job, 2 workers, 2 threads each).

    OMP_NUM_THREADS=2 nice -n 10 python3 -m research.predict.improve.diag.competition.sim.run \
        --win select,dev3,final,ext [--workers 2] [--limit N] [--kind main|sweep]

Writes data/cache/predict/improve/competition/orders-<win>[-sweep].pkl (one row per order)."""
from __future__ import annotations

import argparse
import os
import time
from multiprocessing import Pool

import pandas as pd

from .. import CACHE, SEALED
from ..data.safe import SafeStore, market_ids

_st = None


def _one(job):
    global _st
    _st = _st or SafeStore()
    i, win, kind = job
    from .market import one
    try:
        return one(_st, i, win, kind)
    except Exception as exc:  # report and continue: one bad market must not kill the run
        print(f"market {i} failed: {exc!r}", flush=True)
        return pd.DataFrame()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--win", default="dev3,final,ext")
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--kind", default="main", help="main (all measurements) or sweep (size sweep only)")
    a = ap.parse_args()
    os.environ.setdefault("OMP_NUM_THREADS", "2")
    wins = a.win.split(",")
    ids = market_ids(wins)
    st = SafeStore()
    starts = [float(st.mk.start[i]) for w in wins for i in ids[w]]
    assert max(starts) < SEALED, "sealed market requested"
    CACHE.mkdir(parents=True, exist_ok=True)
    for w in wins:
        jobs = [(i, w, a.kind) for i in ids[w]][: a.limit]
        t0, parts = time.time(), []
        with Pool(a.workers) as pool:
            for k, f in enumerate(pool.imap(_one, jobs, chunksize=2)):
                parts.append(f)
                if k % 20 == 0:
                    print(f"{w} {k}/{len(jobs)} {time.time() - t0:.0f}s", flush=True)
        out = pd.concat([p for p in parts if len(p)], ignore_index=True)
        assert out["m"].map(lambda i: st.mk.start[i]).max() < SEALED
        sfx = ("" if a.kind == "main" else f"-{a.kind}") + ("" if a.limit is None else f"-lim{a.limit}")
        out.to_pickle(CACHE / f"orders-{w}{sfx}.pkl")
        print(w, "markets", len(jobs), "orders", len(out), f"{time.time() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
