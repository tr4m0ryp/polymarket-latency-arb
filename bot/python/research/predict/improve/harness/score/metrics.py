"""Window metrics of one arm against the frozen references, on a fixed market set.

Same estimators and seeds as the report (research/strategy/eval/metrics.py): per-day numbers
scale by markets / 288, a market where the arm did not trade counts as 0, CIs are 2.5/97.5%
of a market bootstrap (summary: 1000 draws seed 1; paired: 2000 draws seed 2), so a frozen
arm on a frozen run's market list reproduces that run's table exactly."""
from __future__ import annotations

import numpy as np
import pandas as pd

from .....strategy.eval.metrics import DAY_MARKETS, paired, summary

REFS = ("vt_v1_m0.03_any", "micf")


def _per_market(a: pd.DataFrame, markets, col: str) -> np.ndarray:
    return a.groupby("m")[col].sum().reindex(markets).fillna(0).to_numpy(float)


def row(a: pd.DataFrame, refs: dict[str, pd.DataFrame], markets) -> dict:
    """a: aggregates of one arm x L x variant (columns of sim/fills.aggregate); refs: the
    frozen references' aggregates at the same L and variant; markets: the window's ids."""
    markets = np.asarray(sorted(markets))
    days = len(markets) / DAY_MARKETS
    s = summary(a, markets) if len(a) else {}
    mk = _per_market(a, markets, "mk10v") if len(a) else np.zeros(len(markets))
    usd = a["cost"].sum() if len(a) else 0.0
    k = np.random.default_rng(1).integers(0, len(markets), size=(1000, len(markets)))
    bm = mk[k].sum(1) / days
    out = {"mkts": len(markets), "fills_day": s.get("fills_day", 0.0), "usd_day": usd / days,
           "mk10_c": 100 * mk.sum() / usd if usd > 0 else np.nan, "mk10_day": mk.sum() / days,
           "mk10_lo": np.percentile(bm, 2.5), "mk10_hi": np.percentile(bm, 97.5),
           "net_day": s.get("net_day", 0.0), "net_c": s.get("c_per_usd", np.nan),
           "worst5": np.sort(mk)[:5].sum(), "best5": np.sort(mk)[-5:].sum(),
           "traded_mkts": int((_per_market(a, markets, "cost") > 0).sum()) if len(a) else 0}
    for name, b in refs.items():
        tag = "vt" if name == "vt_v1_m0.03_any" else name
        p = _paired_safe(a, b, markets)
        out.update({f"g_{tag}": p["diff_day"], f"g_{tag}_lo": p["lo"], f"g_{tag}_hi": p["hi"],
                    f"g_{tag}_p0": p["p_le0"]})
    return out


def _paired_safe(a, b, markets):
    if not len(a):
        a = pd.DataFrame({"m": [], "mk10v": []})
    if not len(b):
        b = pd.DataFrame({"m": [], "mk10v": []})
    return paired(a, b, markets, col="mk10v")


def table(arms: dict[str, pd.DataFrame], refs: dict[str, pd.DataFrame], sets: dict[str, list[int]],
          Ls=(0, -40), variants=("base", "comp")) -> pd.DataFrame:
    """Rows per market set x arm x L x variant. arms / refs: name -> aggregates over every
    market of every set (columns L, var, m, ...)."""
    rows = []
    for set_name, ids in sets.items():
        if not ids:
            continue
        ids_s = set(ids)
        for L in Ls:
            for var in variants:
                sel = lambda x: x[(x["L"] == L) & (x["var"] == var) & x["m"].isin(ids_s)]  # noqa: E731
                rf = {n: sel(r) for n, r in refs.items()}
                for name, a in arms.items():
                    rows.append({"set": set_name, "arm": name, "L": L, "var": var, **row(sel(a), rf, ids)})
    return pd.DataFrame(rows)
