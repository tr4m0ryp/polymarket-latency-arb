"""Replay every paper order of the three arms through the hold scenarios.

    PYTHONPATH=. nice -n 10 python3 -m research.vetohold.replay.run [--workers 3] [--limit N]
    -> data/out/vetohold/rows.pkl (one row per order x scenario), hold.json"""
from __future__ import annotations

import argparse
import json
from multiprocessing import Pool

import numpy as np
import pandas as pd

from .. import OUT
from ..data.orders import live_hold, paper_orders
from .market import run_market, scenarios

_st = _hold = _ord = None


def _init(hold, orders):
    global _hold, _ord
    _hold, _ord = hold, orders


def _do(chunk: list[tuple[int, str]]) -> list[dict]:
    global _st
    from research.strategy.ingest.load import Store
    _st = _st or Store(keep=3)
    rows = []
    for i, slug in chunk:
        m = _st.market(i)
        if m is None or m["outcome"] is None:
            continue
        if _ord is None:    # trigger split from the simulator tables (data/trigger.py)
            from ..data.trigger import trigger_orders
            o = trigger_orders(i, m["meta"], float(m["outcome"]))
            o = o[~_in_gap(m, o["t"].to_numpy())] if len(o) else o
        else:
            o = _ord[_ord["slug"] == slug]
        if len(o):
            rows += run_market(m, o, _hold, seed=i)
    return rows


def _in_gap(m, t: np.ndarray) -> np.ndarray:
    """Orders inside a recorder gap window (already padded 30 s before, 5 s after)."""
    bad = np.zeros(len(t), bool)
    for g0, g1 in m["gaps"]:
        bad |= (t >= g0) & (t <= g1 + 0.2)
    return bad


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--trigger", action="store_true", help="kept vs vetoed trigger signals")
    a = ap.parse_args()
    from research.strategy.ingest.load import Store
    mk = Store().mk
    hold = live_hold()
    o = paper_orders()
    o = o[~o["gap"].astype(bool) & o["outcome"].notna()]
    ids = [(int(i), s) for i, s in zip(mk.index, mk["slug"]) if s in set(o["slug"])]
    if a.limit:
        ids = ids[:a.limit]
    n = max(1, len(ids) // (a.workers * 8))
    chunks = [ids[k:k + n] for k in range(0, len(ids), n)]
    with Pool(a.workers, _init, (hold, None if a.trigger else o)) as p:
        rows = [r for part in p.imap(_do, chunks) for r in part]
    df = pd.DataFrame(rows)
    OUT.mkdir(parents=True, exist_ok=True)
    name = ("rows-trigger" if a.trigger else "rows") + ("-test" if a.limit else "")
    df.to_pickle(OUT / f"{name}.pkl")
    (OUT / "hold.json").write_text(json.dumps({"n": len(hold), "ms": (hold * 1e3).round(1).tolist(),
                                              "scenarios": scenarios(hold)}))
    print(len(df), "rows,", df["slug"].nunique(), "markets")


if __name__ == "__main__":
    main()
