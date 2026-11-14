"""Value model: predict the per-share 10 s taker value of buying a side at the match time
(t + L + 150 ms), from side-oriented features. GBDT regressor, train = run 2 first 12 h,
scored on run 2 last 12 h. Reports realized value by decile of the prediction, against the
leaders' trigger and the micf fair filter on the same rows.

    nice -n 10 python3 -m research.predict.model.value [--L 0] [--k 10] [--frac 0.5]"""
from __future__ import annotations

import argparse

import numpy as np
import pandas as pd

from .. import OUT
from ..report.md import md
from .data import load
from .learners import clean, gbdt_reg
from .stack import stacked


def fit(tr: pd.DataFrame, vf: list[str], target: str, seed: int = 0, **kw):
    ok = np.isfinite(tr[target].to_numpy())
    y = np.clip(tr.loc[ok, target].to_numpy(float), -0.3, 0.3)
    return gbdt_reg(seed=seed, **kw).fit(clean(tr.loc[ok, vf].to_numpy()), y)


def deciles(pred: np.ndarray, real: np.ndarray, price: np.ndarray, q=10) -> pd.DataFrame:
    ok = np.isfinite(real)
    b = pd.qcut(pred[ok], q, labels=False, duplicates="drop")
    d = pd.DataFrame({"b": b, "pred_c": 100 * pred[ok], "real_c": 100 * real[ok], "px": price[ok]})
    g = d.groupby("b").agg(n=("real_c", "size"), pred_c=("pred_c", "mean"), real_c=("real_c", "mean"),
                           px=("px", "mean"))
    g["real_c_per_usd"] = g["real_c"] / g["px"]
    return g.reset_index()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--L", type=int, default=0)
    ap.add_argument("--k", type=int, default=10)
    ap.add_argument("--frac", type=float, default=0.5)
    a = ap.parse_args()
    tr, vf = stacked(load("train", frac=a.frac, seed=1))
    te, _ = stacked(load("select", frac=a.frac, seed=2))
    tgt = f"v{a.k}_{a.L}"
    tr = tr[tr[f"bad{a.L}"] == 0]
    te = te[te[f"bad{a.L}"] == 0]
    m = fit(tr, vf, tgt)
    p = m.predict(clean(te[vf].to_numpy()))
    real, px = te[f"v10_{a.L}"].to_numpy(float), te["seen"].to_numpy(float)
    out = deciles(p, real, px, 20)
    print("rows", len(tr), len(te), "features", len(vf))
    print(md(out, 2))
    for thr in (0.0, 0.005, 0.01, 0.02, 0.03):
        w = p >= thr
        print(f"pred >= {thr:.3f}: rows {w.sum()} ({w.mean():.4f}) real10 {100*np.nanmean(real[w]):.2f} c/sh "
              f"{100*np.nanmean(real[w])/np.nanmean(px[w]):.2f} c/$")
    trig = (np.abs(te["p_dmic0.1"]) >= 0.002) & (te["p_dmic0.1"] + te["s_dmic0.1"] > 0)
    for name, w in (("leaders' trigger", trig), ("micf (trigger + fair edge >= 1 c)", trig & (te["fair_edge_up"] >= 0.01))):
        w = w.to_numpy()
        print(f"{name}: rows {w.sum()} real10 {100*np.nanmean(real[w]):.2f} c/sh pred {100*np.mean(p[w]):.2f}")
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"value_deciles_L{a.L}_k{a.k}.md").write_text(md(out, 2))


if __name__ == "__main__":
    main()
