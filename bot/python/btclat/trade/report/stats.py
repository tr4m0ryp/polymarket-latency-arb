"""Small statistics for the live-test report: percentiles, a market-cluster bootstrap of a
c/$ ratio (fills in one market are not independent), and the number of trades the 95% CI
needs to exclude 0 at a given mean."""
from __future__ import annotations

import math

import numpy as np
import pandas as pd

Z = 1.959964


def pct(x, scale: float = 1.0) -> dict:
    x = pd.to_numeric(pd.Series(x), errors="coerce").dropna().to_numpy() * scale
    if not len(x):
        return {"n": 0, "p10": np.nan, "p50": np.nan, "p90": np.nan, "p99": np.nan, "max": np.nan}
    q = np.percentile(x, [10, 50, 90, 99])
    return {"n": len(x), "p10": q[0], "p50": q[1], "p90": q[2], "p99": q[3], "max": float(x.max())}


def boot_cpd(num, den, groups, n: int = 4000, seed: int = 0) -> tuple[float, float, float]:
    """100 * sum(num) / sum(den) and its 95% bootstrap CI, resampling whole groups (markets)."""
    d = pd.DataFrame({"num": np.asarray(num, float), "den": np.asarray(den, float), "g": np.asarray(groups)})
    d = d.dropna()
    if not len(d) or d["den"].sum() <= 0:
        return np.nan, np.nan, np.nan
    s = d.groupby("g")[["num", "den"]].sum().to_numpy()
    point = 100 * s[:, 0].sum() / s[:, 1].sum()
    if len(s) < 2:
        return point, np.nan, np.nan
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(s), size=(n, len(s)))
    num_b, den_b = s[idx, 0].sum(axis=1), s[idx, 1].sum(axis=1)
    r = 100 * num_b[den_b > 0] / den_b[den_b > 0]
    lo, hi = np.percentile(r, [2.5, 97.5])
    return point, float(lo), float(hi)


def n_needed(sd: float, mean: float) -> float:
    """Trades for the normal 95% CI of the mean to exclude 0: (1.96 sd / mean)^2."""
    if not (sd == sd and mean == mean) or mean <= 0:
        return math.inf
    return math.ceil((Z * sd / mean) ** 2)
