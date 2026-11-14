"""Cluster bootstrap over markets (orders inside one 5m market are not independent)."""
from __future__ import annotations

import numpy as np
import pandas as pd

NBOOT, SEED = 4000, 0


def sums(df: pd.DataFrame, cols: list[str], by: str = "slug") -> np.ndarray:
    return df.groupby(by)[cols].sum().to_numpy(float)


def draws(n: int) -> np.ndarray:
    return np.random.default_rng(SEED).integers(0, n, size=(NBOOT, n))


def ratio(s: np.ndarray, num: int, den: int, idx: np.ndarray, scale: float = 100.0) -> dict:
    """scale * sum(num) / sum(den) over clusters with its 95% percentile interval."""
    tot = s.sum(0)
    if tot[den] <= 0:
        return {"est": None, "lo": None, "hi": None}
    b = s[idx].sum(1)
    r = scale * b[:, num][b[:, den] > 0] / b[:, den][b[:, den] > 0]
    lo, hi = np.percentile(r, [2.5, 97.5])
    return {"est": round(scale * tot[num] / tot[den], 3), "lo": round(float(lo), 3), "hi": round(float(hi), 3)}
