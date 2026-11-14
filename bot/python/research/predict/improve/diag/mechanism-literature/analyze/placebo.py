"""Events vs matched quiet instants (placebo, same market, ~6 s earlier, same side): how much
of the stale-quote turnover and of the trade terminations is caused by the Binance move
rather than by background activity (the VPIN lesson of Andersen-Bondarenko: activity alone
mechanically raises any trade-based toxicity measure)."""
from __future__ import annotations

import numpy as np
import pandas as pd

from .stats import boot_median, boot_ratio, fmt


def _r(g: pd.DataFrame) -> dict:
    lq = boot_median(g, "lag_q")
    sn = boot_ratio(g, "snipe")
    return {"n": len(g), "touch life ms": fmt(lq[0], lq[1], lq[2], 0, 1000).replace("+", ""),
            "P(<300ms)": f"{(g['lag_q'].fillna(99) < 0.3).mean():.2f}",
            "ended by trade": fmt(sn[0], sn[1], sn[2], 2).replace("+", ""),
            "prints toward s 0.1-0.5s": f"{(g['n_s0.1'] + g['n_s0.2'] + g['n_s0.3']).mean():.2f}"}


def placebo_table(raw: pd.DataFrame, col: str = "cvol30", q: int = 5) -> pd.DataFrame:
    d = raw[(raw["bb0"] > 0) & (raw["ba0"] < 100) & (raw["pm_silence"] < 2.0) & (raw["lag_pmfeed"] < 0.5)].copy()
    ev = d[d["placebo"] == 0]
    cuts = np.unique(np.quantile(ev[col].dropna(), np.linspace(0, 1, q + 1)))
    cuts[0], cuts[-1] = -np.inf, np.inf
    d["b"] = pd.cut(d[col], cuts, labels=False)
    rows = []
    for b, g in d.groupby("b"):
        e, p = g[g["placebo"] == 0], g[g["placebo"] == 1]
        r = {col: f"Q{int(b) + 1}"}
        for tag, x in (("event", e), ("placebo", p)):
            r.update({f"{tag} {k}": v for k, v in _r(x).items()})
        both = g.groupby("placebo")["snipe"].mean()
        r["excess ended-by-trade"] = f"{both.get(0, np.nan) - both.get(1, np.nan):+.2f}"
        rows.append(r)
    return pd.DataFrame(rows)
