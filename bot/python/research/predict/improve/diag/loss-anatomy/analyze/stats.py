"""Market-bootstrap statistics on fill tables: AUC of a state variable for "fill loses",
decile tables of 10 s markout, and cut gains (markout $ of fills a rule would drop)."""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import rankdata

DAY = 288


def auc(x: np.ndarray, y: np.ndarray) -> float:
    """P(x of a loser > x of a winner), ties 1/2. NaN rows dropped."""
    w = np.isfinite(x)
    x, y = x[w], y[w]
    n1 = y.sum()
    n0 = len(y) - n1
    if n1 < 5 or n0 < 5:
        return np.nan
    r = rankdata(x)
    return float((r[y > 0].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))


def _boot_idx(m: np.ndarray, boot: int, seed: int):
    """Row index arrays of `boot` market-bootstrap resamples (markets with replacement)."""
    u, inv = np.unique(m, return_inverse=True)
    rows = [np.flatnonzero(inv == k) for k in range(len(u))]
    rng = np.random.default_rng(seed)
    for _ in range(boot):
        pick = rng.integers(0, len(u), len(u))
        yield np.concatenate([rows[k] for k in pick])


def auc_ci(f: pd.DataFrame, col: str, boot: int = 400, seed: int = 7) -> tuple[float, float, float]:
    x, y, m = f[col].to_numpy(float), f["lose"].to_numpy(float), f["key"].to_numpy()
    a = auc(x, y)
    bs = [auc(x[k], y[k]) for k in _boot_idx(m, boot, seed)]
    bs = np.array([b for b in bs if np.isfinite(b)])
    return a, float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))


def days(f: pd.DataFrame, nmk: dict) -> float:
    return sum(nmk[w] for w in f["window"].unique()) / DAY


def deciles(f: pd.DataFrame, col: str, nmk: dict, q: int = 10) -> pd.DataFrame:
    x = f[col].to_numpy(float)
    ok = np.isfinite(x)
    g = f[ok].copy()
    g["bin"] = pd.qcut(g[col].rank(method="first"), q, labels=False) + 1
    d = days(f, nmk)
    out = g.groupby("bin").agg(lo=(col, "min"), hi=(col, "max"), n=("lose", "size"),
                               lose=("lose", "mean"), mk=("mk10v", "sum"), cost=("cost", "sum"))
    out["c_usd"] = 100 * out["mk"] / out["cost"]
    out["usd_day"] = out["mk"] / d
    return out.drop(columns=["mk", "cost"]).reset_index()


def cut_gain(f: pd.DataFrame, drop: np.ndarray, nmk: dict, boot: int = 2000, seed: int = 3) -> dict:
    """Markout $/day change from dropping the flagged fills (= minus their sum), market-bootstrap
    CI; c/$ before and after. Ignores knock-on effects on later orders (refractory, depth memory)."""
    d = days(f, nmk)
    v = np.where(drop, -f["mk10v"].to_numpy(float), 0.0)
    per = pd.Series(v).groupby(f["key"].to_numpy()).sum()
    # markets without fills contribute 0: pad to the full market count
    n_all = sum(nmk[w] for w in f["window"].unique())
    arr = np.r_[per.to_numpy(), np.zeros(max(n_all - len(per), 0))]
    k = np.random.default_rng(seed).integers(0, len(arr), size=(boot, len(arr)))
    s = arr[k].sum(1)
    keep = ~drop
    c0 = 100 * f["mk10v"].sum() / f["cost"].sum()
    c1 = 100 * f.loc[keep, "mk10v"].sum() / max(f.loc[keep, "cost"].sum(), 1e-9)
    return {"dropped": int(drop.sum()), "share": float(drop.mean()), "gain_day": arr.sum() / d,
            "lo": np.percentile(s, 2.5) / d, "hi": np.percentile(s, 97.5) / d,
            "p_le0": float((s <= 0).mean()), "c_before": c0, "c_after": c1,
            "usd_day_after": f.loc[keep, "mk10v"].sum() / d}
