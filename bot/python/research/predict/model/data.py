"""Load the per-market decision tables (feats/run.py) of one or more segments.

Feature columns = everything that is not a target (y_*), an outcome path column (x_*), the
time or the outcome. `features(df, perp_trades=False)` drops the run-3-only perp trade
columns unless asked, so run-2 models never see them."""
from __future__ import annotations

import numpy as np
import pandas as pd

from .. import CACHE, segment
from ...strategy.ingest.load import Store

TAB = CACHE / "tab"
NOT_FEAT = ("t", "outcome", "pm_bb", "pm_ba", "zs", "fair_p")


def market_ids(segs, st: Store | None = None) -> list[int]:
    st = st or Store()
    segs = set(segs.split(",")) if isinstance(segs, str) else set(segs)
    have = {int(p.stem) for p in TAB.glob("*.npz") if "tmp" not in p.name}
    return [i for i in sorted(have) if segment(st.mk.start[i]) in segs]


def load(segs, cols=None, frac: float = 1.0, seed: int = 0, st: Store | None = None) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    parts = []
    for i in market_ids(segs, st):
        with np.load(TAB / f"{i}.npz") as z:
            keys = z.files if cols is None else [c for c in cols if c in z.files]
            d = {k: z[k] for k in keys}
        n = len(next(iter(d.values())))
        w = rng.random(n) < frac if frac < 1 else np.ones(n, bool)
        df = pd.DataFrame({k: v[w] for k, v in d.items()})
        df["m"] = i
        parts.append(df)
    return pd.concat(parts, ignore_index=True)


def features(df: pd.DataFrame, perp_trades: bool = False) -> list[str]:
    out = []
    for c in df.columns:
        if c in NOT_FEAT or c == "m" or c.startswith(("y_", "x_")):
            continue
        if c.startswith("ft_") and not perp_trades:
            continue
        out.append(c)
    return out
