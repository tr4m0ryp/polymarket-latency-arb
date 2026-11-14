"""Fit and save value models for every L (model/store.py), one config per name.

    nice -n 10 python3 -m research.predict.model.train --name v1 [--k 1] [--leaf 200]
        [--prefilter] [--seg train] [--frac 0.5] [--perp-trades] [--L=-40,0,50]

Target: per-share value of buying a side at the match time t + L + 150 ms, marked at the
venue mid k s later (k = 1 by default: least noise, selected on run 2 select hours)."""
from __future__ import annotations

import argparse
import time

import numpy as np

from .data import load
from .learners import clean, gbdt_reg
from .stack import stacked
from .store import save
from .value_sweep import prefilter


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", required=True)
    ap.add_argument("--k", type=int, default=1)
    ap.add_argument("--leaf", type=int, default=200)
    ap.add_argument("--leaves", type=int, default=15)
    ap.add_argument("--iters", type=int, default=200)
    ap.add_argument("--prefilter", action="store_true")
    ap.add_argument("--perp-trades", action="store_true")
    ap.add_argument("--seg", default="train")
    ap.add_argument("--frac", type=float, default=0.5)
    ap.add_argument("--L", default="-40,0,50")
    a = ap.parse_args()
    tr, vf = stacked(load(a.seg, frac=a.frac, seed=1), a.perp_trades)
    for L in (int(x) for x in a.L.split(",")):
        t0 = time.time()
        tgt = f"v{a.k}_{L}"
        w = np.isfinite(tr[tgt].to_numpy()) & (tr[f"bad{L}"] == 0).to_numpy()
        if a.prefilter:
            w &= prefilter(tr)
        m = gbdt_reg(max_iter=a.iters, leaves=a.leaves, lr=0.05, min_leaf=a.leaf).fit(
            clean(tr.loc[w, vf].to_numpy()), np.clip(tr.loc[w, tgt].to_numpy(float), -0.3, 0.3))
        save(f"{a.name}_L{L}", m, vf, vars(a) | {"L": L, "rows": int(w.sum())})
        print(a.name, L, int(w.sum()), f"{time.time() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
