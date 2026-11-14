"""Recalibrated value-taker arms through the unchanged strategy replay simulator (150 ms
hold, venue depth, survival-window competition), on allowed windows only.

    OMP_NUM_THREADS=1 nice -n 10 python3 -m research.predict.improve.diag.calibration.recal.sim
        --win select,dev3,final,ext [--L=0,-40] [--workers 2] [--J 0.01] [--cap 1.0] [--tag recal]

Arms (recal/arms.py): the frozen vt_v1_m0.03_any rebuilt here as vt_v1_m3 (reproduction
check against the frozen agg files), and the same rule (60 sh, limit seen ask + 2 c, 0.2 s
refractory) on recalibrated predictions or margins; the veto likewise. micf is taken from the frozen agg files of the same windows.
Writes OUT/sim/agg-<tag>-<win>.pkl and fills-<tag>-<win>.pkl."""
from __future__ import annotations

import argparse
import time
from multiprocessing import Pool

import numpy as np
import pandas as pd

from .. import OUT
from ..safe import SafeStore, check, market_ids, start_of
from ..rows.regime import regime
from .....model.store import load_model, predict_sides
from .....sim import rules
from .....sim.fills import aggregate, score
from ......strategy.sim import taker
from ......strategy.sim.grid import Book
from .arms import adjust, prepare

_st, _cfg, _mdl = None, None, {}


def _one(i: int):
    global _st
    _st = _st or SafeStore()
    m = _st.market(i)
    meta = m["meta"]
    book = Book(m["ev"], meta["start"] - 2, meta["end"] + 2, m["gaps"])
    with np.load(_cfg["tab"] / f"{i}.npz") as z:
        tab = pd.DataFrame({k: z[k] for k in z.files})
    rg = regime(m, tab)
    out, keep, preds = [], [], {}
    for L in _cfg["L"]:
        key = f"v1_L{L}"
        if key not in _mdl:
            _mdl[key] = load_model(key)
        if key not in preds:
            preds[key] = predict_sides(tab, _mdl[key])
        for arm in _cfg["arms"]:
            su, sd, margin = adjust(arm, preds[key], tab, rg, L, _cfg["fit"])
            d = rules.vtaker(tab, su, sd, margin=margin, **arm["params"])
            if not len(d["t"]):
                continue
            fl, _ = taker.run(book, d["t"], d["side"], d["shares"], d["limit"], L / 1000, _cfg["J"], _cfg["cap"], 0.150)
            if not fl:
                continue
            f = pd.DataFrame(fl)
            f["arm"], f["L"], f["m"], f["end"] = arm["name"], L, i, meta["end"]
            f["edge"] = d["edge"][f["i"].to_numpy()]
            f = score(f, book, float(m["outcome"]))
            out.append(aggregate(f))
            keep.append(f[["arm", "L", "m", "t", "tf", "side", "shares", "cost", "fee", "px", "won", "pnl",
                           "mk3v", "mk10v", "edge"]])
    cat = lambda x: pd.concat(x, ignore_index=True) if x else pd.DataFrame()  # noqa: E731
    return cat(out), cat(keep)


def _init(cfg):
    global _cfg
    _cfg = cfg


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--win", default="select,dev3,final,ext")
    ap.add_argument("--L", default="0,-40")
    ap.add_argument("--J", type=float, default=0.010)
    ap.add_argument("--cap", type=float, default=1.0)
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--tag", default="recal")
    ap.add_argument("--arms", default=None, help="comma list of arm names (default: all)")
    a = ap.parse_args()
    from ...... import predict
    arms, fit = prepare(a.arms)
    cfg = {"arms": arms, "fit": fit, "L": [int(x) for x in a.L.split(",")], "J": a.J, "cap": a.cap,
           "tab": predict.CACHE / "tab"}
    (OUT / "sim").mkdir(parents=True, exist_ok=True)
    for w in a.win.split(","):
        ids = market_ids(w)
        check(start_of(ids))
        t0, aggs, fills = time.time(), [], []
        with Pool(a.workers, initializer=_init, initargs=(cfg,)) as pool:
            for j, (ag, fl) in enumerate(pool.imap(_one, ids, chunksize=2)):
                aggs.append(ag)
                fills.append(fl)
                if j % 20 == 0:
                    print(w, j, len(ids), f"{time.time() - t0:.0f}s", flush=True)
        for name, parts in (("agg", aggs), ("fills", fills)):
            parts = [p for p in parts if len(p)]
            pd.concat(parts, ignore_index=True).to_pickle(OUT / "sim" / f"{name}-{a.tag}-{w}.pkl")
        print(w, "done", f"{time.time() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
