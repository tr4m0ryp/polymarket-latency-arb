"""Simulated fill fraction by order size (the paper-run check: realized fill fraction of orders
above 60 sh within 25% of the simulator), and 10 s markout per filled share by size bin.

Same simulator call as the harness worker (strategy/sim/taker.run, 150 ms hold), allowed
markets only. Fill fraction = filled / ordered shares over the decisions the simulator does
not skip (recorder gap or < 5 sh).

    nice -n 10 python3 -m research.predict.improve.cand.<c1 pkg>.fillfrac"""
from __future__ import annotations

import multiprocessing as mp

import numpy as np
import pandas as pd

from .... import OUT
from ....sim.fills import score
from .....strategy.sim import taker
from .....strategy.sim.grid import Book
from ...harness import windows as W
from ...harness.api import Market
from ...harness.guard import SEALED, assert_allowed
from ...harness.sim import worker
from .arms import taker_arm, veto_arm

ARMS = [taker_arm(2000, "pred"), taker_arm(2000, "vstar", cap=6), taker_arm(3000, "vstar", cap=6),
        veto_arm(4000, "vstar", cap=6), veto_arm(3000, "vstar")]
BINS = [0, 60.5, 100, 150, 200.5, 400.5]
VAR = {"base": (0.010, 1.0), "comp": (0.050, 0.5)}


def _one(i: int) -> list[dict]:
    m = worker._store().market(i)
    meta = m["meta"]
    book = Book(m["ev"], meta["start"] - 2, meta["end"] + 2, m["gaps"])
    mk = Market(i, meta)
    rows = []
    for a in ARMS:
        d = a.decide(mk, 0)
        if d is None or not len(d["t"]):
            continue
        t, sh = np.asarray(d["t"], float), np.asarray(d["shares"], float)
        q0 = book.g_ceil(t + 0.150)
        for v, (J, cap) in VAR.items():
            q1 = book.g_ceil(t + 0.150 + J)
            ok = np.array([not book.bad[int(a0):int(a1) + 1].any() for a0, a1 in zip(q0, q1)]) & (sh >= 5)
            fills, _ = taker.run(book, t, d["side"], sh, d["limit"], 0.0, J, cap, 0.150)
            f = pd.DataFrame(fills)
            got = np.zeros(len(t))
            mk10 = np.zeros(len(t))
            if len(f):
                f = score(f, book, float(m["outcome"]))
                got[f["i"].to_numpy()] = f["shares"].to_numpy()
                mk10[f["i"].to_numpy()] = f["mk10v"].to_numpy()
            for k in np.flatnonzero(ok):
                rows.append({"arm": a.name, "var": v, "m": i, "w": W.window_of(i), "ordered": sh[k],
                             "got": got[k], "mk10v": mk10[k]})
    return rows


def main() -> None:
    ids = W.all_eval_ids()
    assert_allowed(W._markets().start[ids], "fillfrac")
    assert W._markets().start[ids].max() < SEALED
    with mp.get_context("fork").Pool(2, initializer=worker.init_worker) as pool:
        rows = [r for rs in pool.imap(_one, ids, chunksize=4) for r in rs]
    o = pd.DataFrame(rows)
    o["bin"] = pd.cut(o["ordered"], BINS)
    o["busy"] = np.where(o["w"] == "ext", "ext", "other")
    g = o.groupby(["arm", "var", "busy", "bin"], observed=True).agg(
        orders=("got", "size"), ordered=("ordered", "sum"), got=("got", "sum"), mk10v=("mk10v", "sum"))
    g["fill_frac"] = g["got"] / g["ordered"]
    g["mk10_c_per_sh"] = 100 * g["mk10v"] / g["got"].where(g["got"] > 0)
    out = OUT / "improve" / "c1-size" / "fill_fraction.csv"
    g.reset_index().to_csv(out, index=False)
    print(g.round(3).to_string())


if __name__ == "__main__":
    main()
