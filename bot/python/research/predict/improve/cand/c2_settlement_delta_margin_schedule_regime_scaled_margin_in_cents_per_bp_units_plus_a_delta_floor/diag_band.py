"""Row-level screen of the decision rows a delta schedule adds or removes (no simulator, best
level, no rivals): realized 1 s / 10 s per-share value of the side the 1 s model prefers at
L, by window and by a state variable (sigma, secs_left, delta), for rows in the band
`lo <= predicted value < hi` that pass the frozen vtaker gates. Diagnostic only.

    python3 -m research.predict.improve.cand.<c2>.diag_band --L 0 --lo 0.025 --hi 0.03 --dmin 25"""
from __future__ import annotations

import argparse

import numpy as np
import pandas as pd

from ....model.data import TAB
from ....model.derive import side_values
from ....sim.rules import _gates
from ...harness import windows as W
from ...harness.api import saved_pred
from .delta import assert_unsealed, delta

WINS = ("select", "dev3", "test3r1", "ext")


def rows(L: int, lo: float, hi: float, dmin: float, dmax: float) -> pd.DataFrame:
    parts = []
    for w in WINS:
        st = W.starts(w)
        assert_unsealed(list(st.values()), w)
        for i in W.ids(w):
            with np.load(TAB / f"{i}.npz") as z:
                d = pd.DataFrame({k: z[k] for k in z.files})
            pu, pdn = saved_pred(i, f"v1_L{L}", d.drop(columns=[c for c in d if c.startswith(("y_", "x_"))]))
            side = np.where(pu >= pdn, 1, -1)
            edge = np.maximum(pu, pdn)
            seen = np.where(side > 0, d["pm_ba"].to_numpy(float) / 100, 1 - d["pm_bb"].to_numpy(float) / 100)
            dl = delta(d)
            ok = _gates(d, seen, (0.05, 0.95), 20.0, 0.97) & (edge >= lo) & (edge < hi) & (dl >= dmin) & (dl < dmax)
            if not ok.any():
                continue
            out = {"m": i, "w": w, "edge": edge[ok], "delta": dl[ok], "sigma": d["sigma"].to_numpy(float)[ok],
                   "secs_left": d["secs_left"].to_numpy(float)[ok], "t": d["t"].to_numpy(float)[ok]}
            for k in (1, 10):
                up, dn = side_values(d, L, k)
                out[f"v{k}"] = np.where(side > 0, up, dn)[ok]
            parts.append(pd.DataFrame(out))
    f = pd.concat(parts, ignore_index=True)
    # thin to one row per market per 0.2 s (the refractory), as an order stream would be
    f = f.sort_values(["m", "t"])
    keep = np.r_[True, (np.diff(f["t"].to_numpy()) >= 0.2) | (np.diff(f["m"].to_numpy()) != 0)]
    return f[keep]


def table(f: pd.DataFrame, by: str, bins) -> pd.DataFrame:
    g = f.assign(b=pd.cut(f[by], bins)).groupby(["w", "b"], observed=True)
    return g.agg(rows=("v10", "size"), mkts=("m", "nunique"), pred_c=("edge", lambda x: 100 * x.mean()),
                 v1_c=("v1", lambda x: 100 * np.nanmean(x)), v10_c=("v10", lambda x: 100 * np.nanmean(x))).round(2)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--L", type=int, default=0)
    ap.add_argument("--lo", type=float, default=0.025)
    ap.add_argument("--hi", type=float, default=0.03)
    ap.add_argument("--dmin", type=float, default=25.0)
    ap.add_argument("--dmax", type=float, default=np.inf)
    a = ap.parse_args()
    f = rows(a.L, a.lo, a.hi, a.dmin, a.dmax)
    sq = np.nanquantile(f.loc[f["w"].isin(["select", "dev3"]), "sigma"], [0.5, 0.9])
    print(f"sigma median / p90 on select+dev3 band rows: {sq}")
    for by, bins in (("sigma", [0, *sq, np.inf]), ("secs_left", [0, 30, 60, 120, 300]),
                     ("delta", [0, 3, 8, 25, 40, 80, np.inf])):
        print(f"\n## by {by}\n" + table(f, by, bins).to_string())


if __name__ == "__main__":
    main()
