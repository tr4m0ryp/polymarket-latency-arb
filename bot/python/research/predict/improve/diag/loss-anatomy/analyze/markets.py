"""Market-level anatomy: per-market 10 s markout of each arm, the tails (worst / best markets),
whether the bad markets are shared across arms (regime) or arm-specific, and which market
regime separates losing markets (AUC for "market sum < 0")."""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

from .. import ARMS, LS, SHORT
from .stats import auc

FILL_MEANS = ["rv60", "rows10", "pred", "abs_mid", "secs_left", "pm_spr", "v_top", "pm_chg10",
              "burst_pos", "trigger"]
REGIME = ["m_rv", "m_rows", "m_pmchg", "m_lam", "m_sigma", "m_spr", "m_absmid", "m_range_c"]


def per_market(f: pd.DataFrame, ms: pd.DataFrame) -> pd.DataFrame:
    g = f.groupby(["arm", "L", "window", "m"])
    a = g.agg(n=("mk10v", "size"), usd=("mk10v", "sum"), cost=("cost", "sum"),
              **{f"f_{c}": (c, "mean") for c in FILL_MEANS}).reset_index()
    a["c_usd"] = 100 * a["usd"] / a["cost"]
    return a.merge(ms.drop(columns=["window"]), on="m", how="left")


def tails(pm: pd.DataFrame, k: int = 5) -> pd.DataFrame:
    rows = []
    for (arm, L), g in pm.groupby(["arm", "L"]):
        tot = g["usd"].sum()
        s = g.sort_values("usd")
        rows.append({"arm": SHORT[arm], "L": L, "markets": len(g), "usd_total": tot,
                     "bottom5_usd": s["usd"].head(k).sum(), "top5_usd": s["usd"].tail(k).sum(),
                     "losing_mkts": float((g["usd"] < 0).mean()),
                     "bottom5_fills": s["n"].head(k).sum(), "all_fills": g["n"].sum()})
    return pd.DataFrame(rows)


def worst(pm: pd.DataFrame, arm: str, L: int, k: int = 8) -> pd.DataFrame:
    g = pm[(pm["arm"] == arm) & (pm["L"] == L)].sort_values("usd").head(k)
    g = g.assign(hour=((g["start"] % 86400) // 3600).astype(int))
    cols = ["window", "m", "hour", "n", "usd", "c_usd", "f_rv60", "f_rows10", "f_pred", "f_abs_mid",
            "f_secs_left", "f_burst_pos", "m_rv", "m_pmchg", "m_range_c"]
    return g[cols]


def shared(pm: pd.DataFrame) -> pd.DataFrame:
    """Spearman of per-market markout between arms (same L, markets both traded)."""
    rows = []
    for L in LS:
        w = pm[pm["L"] == L].pivot_table(index="m", columns="arm", values="usd")
        for i, a in enumerate(ARMS):
            for b in ARMS[i + 1:]:
                x = w[[a, b]].dropna()
                if len(x) > 10:
                    rows.append({"L": L, "a": SHORT[a], "b": SHORT[b], "mkts": len(x),
                                 "spearman": spearmanr(x[a], x[b]).statistic})
    return pd.DataFrame(rows)


def regime_auc(pm: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for v in REGIME + [f"f_{c}" for c in FILL_MEANS] + ["n"]:
        r = {"var": v}
        for arm in ARMS:
            for L in LS:
                g = pm[(pm["arm"] == arm) & (pm["L"] == L)]
                y = (g["usd"] < 0).to_numpy(float)
                r[f"{SHORT[arm]}_L{L}"] = auc(g[v].to_numpy(float), y)
                r[f"{SHORT[arm]}_L{L}_rho_usd"] = spearmanr(g[v], g["usd"], nan_policy="omit").statistic
        rows.append(r)
    return pd.DataFrame(rows)


def regime_terciles(pm: pd.DataFrame, ms: pd.DataFrame, var: str = "m_rv") -> pd.DataFrame:
    """Markout c/$ and $ per market by tercile of a whole-market regime variable (edges from all
    allowed markets, traded or not)."""
    q = np.nanpercentile(ms[var], [33.3, 66.7])
    out = []
    for (arm, L), g in pm.groupby(["arm", "L"]):
        b = np.digitize(g[var], q)
        for k in range(3):
            x = g[b == k]
            n_all = int((np.digitize(ms[var], q) == k).sum())
            out.append({"arm": SHORT[arm], "L": L, "tercile": k + 1, "mkts_traded": len(x),
                        "mkts_all": n_all, "fills": int(x["n"].sum()),
                        "c_usd": 100 * x["usd"].sum() / max(x["cost"].sum(), 1e-9),
                        "usd_per_mkt": x["usd"].sum() / max(n_all, 1)})
    return pd.DataFrame(out)
