"""Value-model variants on run 2 (train -> select): target horizon k, tree regularisation,
and a candidate prefilter. Each variant is compared with micf at matched budgets: the top-N
rows by prediction, N = 0.5x / 1x / 2x micf's row count on the same select rows, realized
10 s value per share and per $.

    nice -n 10 python3 -m research.predict.model.value_sweep [--L 0] [--frac 0.4]"""
from __future__ import annotations

import argparse
from itertools import product

import numpy as np
import pandas as pd

from .. import OUT
from ..report.md import md
from .data import load
from .learners import clean, gbdt_reg
from .stack import stacked


def prefilter(d: pd.DataFrame) -> np.ndarray:
    """Rows where something is happening toward this side: the leaders' trigger, an extreme
    queue, a stale book or a fair edge within 2 c of paying."""
    return ((np.abs(d["p_dmic0.1"]) >= 0.001) | (d["p_imb"] > 0.8) | (np.abs(d["pm_stale"]) > 0.02)
            | (d["fair_edge_up"] > -0.02)).to_numpy()


def micf_rows(d: pd.DataFrame) -> np.ndarray:
    trig = (np.abs(d["p_dmic0.1"]) >= 0.002) & (d["p_dmic0.1"] + d["s_dmic0.1"] > 0)
    return (trig & (d["fair_edge_up"] >= 0.01)).to_numpy()


def budget(pred, real, px, n) -> tuple[float, float]:
    top = np.argsort(-pred)[:n]
    return 100 * np.nanmean(real[top]), 100 * np.nansum(real[top]) / np.nansum(px[top])


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--L", type=int, default=0)
    ap.add_argument("--frac", type=float, default=0.4)
    a = ap.parse_args()
    L = a.L
    tr, vf = stacked(load("train", frac=a.frac, seed=1))
    te, _ = stacked(load("select", frac=a.frac, seed=2))
    tr, te = tr[tr[f"bad{L}"] == 0], te[te[f"bad{L}"] == 0]
    real, px = te[f"v10_{L}"].to_numpy(float), te["seen"].to_numpy(float)
    mc = micf_rows(te)
    n0 = int(mc.sum())
    rows = [{"variant": "micf (reference)", "n": n0, "c_sh_1x": 100 * np.nanmean(real[mc]),
             "c_usd_1x": 100 * np.nansum(real[mc]) / np.nansum(px[mc])}]
    Xte = clean(te[vf].to_numpy())
    pf_te = prefilter(te)
    for k, leaf, pf in product((1, 3, 10), (200, 3000), (False, True)):
        tgt = f"v{k}_{L}" if k > 1 else f"v1_{L}"
        w = np.isfinite(tr[tgt].to_numpy()) & (prefilter(tr) if pf else True)
        m = gbdt_reg(max_iter=200, leaves=15, lr=0.05, min_leaf=leaf).fit(
            clean(tr.loc[w, vf].to_numpy()), np.clip(tr.loc[w, tgt].to_numpy(float), -0.3, 0.3))
        p = m.predict(Xte)
        if pf:
            p = np.where(pf_te, p, -1.0)
        r = {"variant": f"k={k} leaf={leaf} prefilter={pf}", "n": n0}
        for mult in (0.5, 1, 2):
            r[f"c_sh_{mult:g}x"], r[f"c_usd_{mult:g}x"] = budget(p, real, px, int(mult * n0))
        r["overlap_micf_1x"] = float(mc[np.argsort(-p)[:n0]].mean())
        print(r, flush=True)
        rows.append(r)
    out = pd.DataFrame(rows)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"value_sweep_L{L}.md").write_text(md(out, 2))
    print(md(out, 2))


if __name__ == "__main__":
    main()
