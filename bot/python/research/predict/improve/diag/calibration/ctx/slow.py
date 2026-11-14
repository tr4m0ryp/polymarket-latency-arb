"""Slow (hour-scale) activity regime of a market, label-free and causal: the mean busy index
(ctx/load.busy) over every decision row of the markets that started in the `span` seconds
before this market's start (their rows all precede it). The calibration drift was a
window-level shift (a residual model failed across markets, R2 -0.04), so the regime the
margin should follow may be the hour, not the instant.

Uses only the ctx cache of allowed markets (train .. ext); a market with no earlier market in
the span gets NaN (callers fall back to the frozen margin)."""
from __future__ import annotations

from functools import lru_cache

import numpy as np
import pandas as pd

from ..safe import SEALED, market_ids, start_of
from .load import busy, ctx

WINS = ("train", "select", "dev3", "final", "ext")


@lru_cache(maxsize=1)
def market_busy() -> pd.DataFrame:
    """Per allowed market: start and mean busy index over its rows."""
    ids = sorted({i for w in WINS for i in market_ids(w)})
    st = start_of(ids)
    assert st.max() < SEALED
    mb = [float(np.mean(busy(ctx(i)))) for i in ids]
    return pd.DataFrame({"m": ids, "start": st, "mb": mb}).sort_values("start").reset_index(drop=True)


@lru_cache(maxsize=4)
def slow_index(span: float = 1800.0) -> dict[int, float]:
    d = market_busy()
    s, mb = d["start"].to_numpy(), d["mb"].to_numpy()
    out = {}
    for i, t in zip(d["m"], s):
        w = (s >= t - span) & (s <= t - 300)          # markets that ended by this start
        out[int(i)] = float(mb[w].mean()) if w.any() else np.nan
    return out
