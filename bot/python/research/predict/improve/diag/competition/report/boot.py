"""Market-bootstrap helpers (as the report: resample markets, 2.5 / 97.5 percentiles), loading
the per-order tables, and the window groups."""
from __future__ import annotations

import numpy as np
import pandas as pd

from .. import CACHE, SEALED
from ..data.safe import market_ids

DAY = 288
BOOT = 2000
GROUPS = {"select": ("select",), "quiet": ("dev3", "final"), "busy": ("ext",),
          "unseen": ("dev3", "final", "ext"), "test3": ("final", "ext")}


def load(wins=("select", "dev3", "final", "ext")) -> tuple[pd.DataFrame, dict]:
    ids = market_ids(wins)
    parts = []
    for w in wins:
        p = CACHE / f"orders-{w}.pkl"
        if p.exists():
            parts.append(pd.read_pickle(p))
    o = pd.concat(parts, ignore_index=True)
    assert o["end"].max() <= SEALED
    return o, ids


def markets(ids: dict, group: str) -> np.ndarray:
    return np.array([i for w in GROUPS[group] for i in ids.get(w, [])])


def per_market(o: pd.DataFrame, col: str, mk: np.ndarray) -> np.ndarray:
    return o.groupby("m")[col].sum().reindex(mk).fillna(0).to_numpy()


def _idx(n: int, seed: int) -> np.ndarray:
    return np.random.default_rng(seed).integers(0, n, size=(BOOT, n))


def day_ci(v: np.ndarray, seed: int = 1) -> tuple[float, float, float]:
    """Sum per day with a market-bootstrap CI; v = per-market values."""
    days = len(v) / DAY
    s = v[_idx(len(v), seed)].sum(1)
    return v.sum() / days, np.percentile(s, 2.5) / days, np.percentile(s, 97.5) / days


def ratio_ci(num: np.ndarray, den: np.ndarray, seed: int = 1) -> tuple[float, float, float]:
    """100 * sum(num) / sum(den) (c per $) with a market-bootstrap CI."""
    k = _idx(len(num), seed)
    r = 100 * num[k].sum(1) / np.maximum(den[k].sum(1), 1e-9)
    return 100 * num.sum() / max(den.sum(), 1e-9), np.percentile(r, 2.5), np.percentile(r, 97.5)


def fmt(x: tuple, nd: int = 0) -> str:
    f = f"{{:+,.{nd}f}}"
    return f"{f.format(x[0])} [{f.format(x[1])}, {f.format(x[2])}]"


def arm_cols(o: pd.DataFrame, arm: str, L: int, scen: str, mk: np.ndarray) -> dict:
    a = o[(o["arm"] == arm) & (o["L"] == L) & o["m"].isin(mk)]
    return {"mk": per_market(a, f"{scen}_mk10v", mk), "cost": per_market(a, f"{scen}_cost", mk),
            "n": int((a[f"{scen}_got"] > 0).sum()), "sh": float(a[f"{scen}_got"].sum())}
