"""Fill filters chosen on early windows, read on later ones: for each decision-time variable pick,
on the `fit` windows only (select; or select + dev3, the pre-freeze hours), the tail cut (drop x
above / below its 10-30% quantile there) that adds the most 10 s markout $, then apply the same
threshold to the `read` windows (unseen: dev3 + test3 run 1 + ext; or test3 run 1 + ext).

An approximation of a re-simulation: dropping an order frees the refractory window and the
remembered depth, so later orders could change. A screen for hypotheses, not a result."""
from __future__ import annotations

import numpy as np
import pandas as pd

from .. import ARMS, LS, SHORT, UNSEEN
from .stats import cut_gain
from .vars import GROUPS

QS = (0.1, 0.2, 0.3)


def _best_on_fit(s: pd.DataFrame, v: str):
    x = s[v].to_numpy(float)
    if np.isfinite(x).sum() < 50:
        return None
    best = None
    for q in QS:
        for hi in (True, False):
            thr = np.nanquantile(x, 1 - q if hi else q)
            drop = (x > thr) if hi else (x < thr)
            gain = -s.loc[drop, "mk10v"].sum()
            if best is None or gain > best[0]:
                best = (gain, thr, hi, q)
    return best


def screen(f: pd.DataFrame, nmk: dict, arms=ARMS, fit=("select",), read=UNSEEN,
           vars_=None) -> pd.DataFrame:
    rows = []
    vars_ = vars_ or [v for g, vs in GROUPS.items() for v in vs]
    fit_days = sum(nmk[w] for w in fit) / 288
    for arm in arms:
        for L in LS:
            g = f[(f["arm"] == arm) & (f["L"] == L)]
            s, u = g[g["window"].isin(fit)], g[g["window"].isin(read)]
            for v in vars_:
                b = _best_on_fit(s, v)
                if b is None:
                    continue
                gain_s, thr, hi, q = b
                xu = u[v].to_numpy(float)
                drop = (xu > thr) if hi else (xu < thr)
                r = cut_gain(u, drop, nmk)
                rows.append({"arm": SHORT[arm], "L": L, "var": v, "rule": f"drop {'>' if hi else '<'} {thr:.4g}",
                             "q_fit": q, "fit_gain_day": gain_s / fit_days,
                             **{f"read_{k}": val for k, val in r.items()}})
    return pd.DataFrame(rows)


def fixed_rules(f: pd.DataFrame, nmk: dict, rules: dict, arms=ARMS[:2]) -> pd.DataFrame:
    """Named rules (fill table -> drop mask) read on every window separately."""
    rows = []
    for arm in arms:
        for L in LS:
            g = f[(f["arm"] == arm) & (f["L"] == L)]
            for name, fn in rules.items():
                for w, x in g.groupby("window"):
                    r = cut_gain(x, fn(x, g).to_numpy(bool), nmk, boot=1000)
                    rows.append({"arm": SHORT[arm], "L": L, "rule": name, "window": w, **r})
    return pd.DataFrame(rows)


def grid_pick(f: pd.DataFrame, nmk: dict, var: str, grid, fit=("select", "dev3"),
              read=("test3r1", "ext"), arms=ARMS[:2]) -> pd.DataFrame:
    """Drop x < threshold: pick the threshold on `fit` (most markout $ added, ties -> lowest),
    report every grid point on `fit` and `read` so the pick is visible."""
    rows = []
    for arm in arms:
        for L in LS:
            g = f[(f["arm"] == arm) & (f["L"] == L)]
            s, u = g[g["window"].isin(fit)], g[g["window"].isin(read)]
            res = []
            for thr in grid:
                a = cut_gain(s, (s[var] < thr).to_numpy(), nmk, boot=500)
                b = cut_gain(u, (u[var] < thr).to_numpy(), nmk, boot=2000)
                res.append({"arm": SHORT[arm], "L": L, "thr": thr, "fit_gain_day": a["gain_day"],
                            "fit_dropped": a["dropped"], **{f"read_{k}": v for k, v in b.items()}})
            best = max(res, key=lambda r: (round(r["fit_gain_day"], 6), -r["thr"]))
            for r in res:
                r["picked"] = r is best
            rows += res
    return pd.DataFrame(rows)
