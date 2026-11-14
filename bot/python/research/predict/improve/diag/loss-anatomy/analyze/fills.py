"""Fill-level tables: overview per arm x L x window, markout decomposition of winners vs losers,
AUC of every state variable for "fill loses", deciles, and markout by hour."""
from __future__ import annotations

import numpy as np
import pandas as pd

from .. import ARMS, LS, SHORT
from .stats import auc, auc_ci, days, deciles
from .vars import POST, all_vars, group_of


def overview(f: pd.DataFrame, nmk: dict) -> pd.DataFrame:
    rows = []
    for (arm, L, w), g in f.groupby(["arm", "L", "window"]):
        d = days(g, nmk)
        rows.append({"arm": SHORT[arm], "L": L, "window": w, "fills_day": len(g) / d,
                     "c_usd": 100 * g["mk10v"].sum() / g["cost"].sum(), "usd_day": g["mk10v"].sum() / d,
                     "lose": g["lose"].mean(), "mk_sh_c": 100 * g["mk_sh"].mean(),
                     "top10%_of_usd": _top_share(g)})
    return pd.DataFrame(rows)


def _top_share(g: pd.DataFrame) -> float:
    s = np.sort(g["mk10v"].to_numpy())[::-1]
    return float(s[: max(len(s) // 10, 1)].sum() / s.sum()) if s.sum() > 0 else np.nan


def decomposition(f: pd.DataFrame) -> pd.DataFrame:
    """Mean c per share of each markout part, losers vs winners (fills with a venue replay)."""
    parts = ["d_move", "d_half", "d_walk", "d_fee", "mk_sh", "d_hold"]
    g = f[np.isfinite(f["d_move"])]
    out = g.groupby(["arm", "L", "lose"])[parts].mean().mul(100).round(2).reset_index()
    out["n"] = g.groupby(["arm", "L", "lose"]).size().to_numpy()
    out["arm"] = out["arm"].map(SHORT)
    return out


def auc_table(f: pd.DataFrame, boot: int = 400) -> pd.DataFrame:
    rows = []
    for v in all_vars() + POST:
        r = {"var": v, "group": group_of(v)}
        for arm in ARMS:
            for L in LS:
                g = f[(f["arm"] == arm) & (f["L"] == L)]
                a, lo, hi = auc_ci(g, v, boot)
                k = f"{SHORT[arm]}_L{L}"
                r[k], r[k + "_lo"], r[k + "_hi"] = a, lo, hi
                ws = [auc(x[v].to_numpy(float), x["lose"].to_numpy(float)) for _, x in g.groupby("window")]
                r[k + "_win_same"] = int(sum((w - 0.5) * (a - 0.5) > 0 for w in ws if np.isfinite(w)))
        rows.append(r)
    return pd.DataFrame(rows)


def by_hour(f: pd.DataFrame, nmk_hour: pd.Series) -> pd.DataFrame:
    rows = []
    for (arm, L, w, h), g in f.groupby(["arm", "L", "window", "hour"]):
        d = nmk_hour.get((w, h), np.nan) / 288
        rows.append({"arm": SHORT[arm], "L": L, "window": w, "hour": h, "fills": len(g),
                     "c_usd": 100 * g["mk10v"].sum() / g["cost"].sum(), "usd_day": g["mk10v"].sum() / d,
                     "lose": g["lose"].mean(), "rv60": g["rv60"].median(), "delta_med": g["delta"].median(),
                     "share_delta<5": (g["delta"] < 5).mean()})
    return pd.DataFrame(rows)


def decile_tables(f: pd.DataFrame, vars_: list[str], nmk: dict) -> pd.DataFrame:
    out = []
    for arm in ARMS:
        for L in LS:
            g = f[(f["arm"] == arm) & (f["L"] == L)]
            for v in vars_:
                d = deciles(g, v, nmk, q=5 if len(g) < 600 else 10)
                d.insert(0, "var", v)
                d.insert(0, "L", L)
                d.insert(0, "arm", SHORT[arm])
                out.append(d)
    return pd.concat(out, ignore_index=True)
