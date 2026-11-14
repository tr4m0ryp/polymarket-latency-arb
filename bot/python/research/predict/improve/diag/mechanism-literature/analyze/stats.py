"""Market-bootstrap helpers (events of one market share its book, so markets are the unit)."""
from __future__ import annotations

import numpy as np
import pandas as pd


def boot_ratio(df: pd.DataFrame, num: str, den: str | None = None, B: int = 1000, seed: int = 7):
    """sum(num) / sum(den) (or mean of num) over events, CI from resampling markets."""
    d = df[[c for c in ("m", num, den) if c]].dropna()
    if not len(d):
        return np.nan, np.nan, np.nan
    g = d.groupby("m").agg(s=(num, "sum"), n=(num if den is None else den, "count" if den is None else "sum"))
    s, n = g["s"].to_numpy(float), g["n"].to_numpy(float)
    k = np.random.default_rng(seed).integers(0, len(g), size=(B, len(g)))
    bs, bn = s[k].sum(1), n[k].sum(1)
    r = bs / np.where(bn == 0, np.nan, bn)
    return s.sum() / n.sum(), np.nanpercentile(r, 2.5), np.nanpercentile(r, 97.5)


def boot_median(df: pd.DataFrame, col: str, B: int = 400, seed: int = 7):
    d = df[["m", col]].dropna()
    if not len(d):
        return np.nan, np.nan, np.nan
    groups = [g[col].to_numpy(float) for _, g in d.groupby("m")]
    rng = np.random.default_rng(seed)
    meds = [np.median(np.concatenate([groups[j] for j in rng.integers(0, len(groups), len(groups))]))
            for _ in range(B)]
    return float(np.median(d[col])), np.percentile(meds, 2.5), np.percentile(meds, 97.5)


def fmt(x, lo=None, hi=None, nd=1, scale=1.0):
    if x is None or not np.isfinite(x):
        return "n/a"
    s = f"{x * scale:+.{nd}f}" if lo is not None else f"{x * scale:.{nd}f}"
    if lo is not None and np.isfinite(lo):
        s += f" [{lo * scale:+.{nd}f}, {hi * scale:+.{nd}f}]"
    return s


def deciles(x: pd.Series, q: int = 10) -> pd.Series:
    return pd.qcut(x.rank(method="first"), q, labels=False)
