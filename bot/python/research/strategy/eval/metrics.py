"""Scoring of simulated arms from per-market aggregates (eval/sim.py agg-<tag>.pkl).

Hold to resolution at our 0% rebate tier: pnl = shares * (bought side won) - cost - taker
fee. Per-day numbers scale by market time covered (n markets * 5 min / 24 h); every arm is
divided by the same market count, so a market where it did not trade counts as 0. Max
drawdown runs over cumulative PnL in resolution order. CI = 2.5/97.5% of a bootstrap over
markets (all fills of a market share one outcome). mk3_c = net c per $ if each fill were
valued at the venue mid 3 s later (low-variance edge estimate)."""
from __future__ import annotations

import numpy as np
import pandas as pd

DAY_MARKETS = 288


def summary(a: pd.DataFrame, markets: np.ndarray, boot: int = 1000, seed: int = 1) -> dict:
    """a: aggregate rows of one arm and L; markets: every market id in the evaluated set."""
    days = len(markets) / DAY_MARKETS
    a = a.set_index("m").reindex(markets)
    pnl, cost = a["pnl"].fillna(0).to_numpy(), a["cost"].fillna(0).to_numpy()
    n, usd, net = a["n"].fillna(0).sum(), cost.sum(), pnl.sum()
    order = np.argsort(a["end"].fillna(0).to_numpy(), kind="stable")
    cum = np.r_[0, np.cumsum(pnl[order])]
    dd = float(np.max(np.maximum.accumulate(cum) - cum))
    k = np.random.default_rng(seed).integers(0, len(markets), size=(boot, len(markets)))
    bn, bc = pnl[k].sum(1), cost[k].sum(1)
    c = lambda x: 100 * x / usd if usd > 0 else np.nan  # noqa: E731
    return {"fills_day": n / days, "usd_day": usd / days, "net_day": net / days,
            "c_per_usd": c(net), "win": a["won_n"].sum() / n if n else np.nan,
            "max_dd": dd, "mk3_c": c(a["mk3v"].sum()),
            "mk10_c": c(a["mk10v"].sum()) if "mk10v" in a else np.nan,
            "net_lo": np.percentile(bn, 2.5) / days, "net_hi": np.percentile(bn, 97.5) / days,
            "c_lo": 100 * np.percentile(bn / np.maximum(bc, 1e-9), 2.5) if usd > 0 else np.nan,
            "c_hi": 100 * np.percentile(bn / np.maximum(bc, 1e-9), 97.5) if usd > 0 else np.nan,
            "mkts": int((cost > 0).sum()), "net_total": net}


def table(agg: pd.DataFrame, markets: np.ndarray, keys=("arm", "L")) -> pd.DataFrame:
    rows = []
    for k, g in agg.groupby(list(keys), sort=False):
        rows.append({**dict(zip(keys, k if isinstance(k, tuple) else (k,))), **summary(g, markets)})
    return pd.DataFrame(rows)


def paired(a: pd.DataFrame, b: pd.DataFrame, markets: np.ndarray, boot: int = 2000,
           seed: int = 2, col: str = "pnl") -> dict:
    """Net $ difference a - b on the same markets, with a market bootstrap CI (col = pnl for
    resolution, mk10v for the 10 s markout)."""
    pa = a.set_index("m")[col].reindex(markets).fillna(0).to_numpy()
    pb = b.set_index("m")[col].reindex(markets).fillna(0).to_numpy()
    d = pa - pb
    k = np.random.default_rng(seed).integers(0, len(d), size=(boot, len(d)))
    s = d[k].sum(1)
    days = len(markets) / DAY_MARKETS
    return {"diff_day": d.sum() / days, "lo": np.percentile(s, 2.5) / days,
            "hi": np.percentile(s, 97.5) / days, "p_le0": float((s <= 0).mean())}
