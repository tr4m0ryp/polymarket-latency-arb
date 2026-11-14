"""Closed-loop calibration on the money label: the fill-level gap of the deployed taker's own
recent fills (10 s markout per share minus the predicted value per share), causal per market.

Label stream: the frozen 1 s taker's simulated fills at the same L (recalibration run,
fills-recal-<win>.pkl, arm vt_v1_m3, identical to the frozen agg files), from markets that
ended at or before this market's start and within `span` s of it (a fill's 10 s markout is
known 10 s after the fill; fills stop 20 s before a market's end). Shrunk toward 0 with a
prior of n0 shares: gap = (sum mk10 - sum pred * shares) / (sum shares + n0), $/share.
Approximation: live, the bot would read its own fills, which change with its margin."""
from __future__ import annotations

from functools import lru_cache

import numpy as np
import pandas as pd

from .. import OUT
from ..safe import SEALED, check, start_of

WINS = ("select", "dev3", "final", "ext")


@lru_cache(maxsize=1)
def fill_table() -> pd.DataFrame:
    parts = []
    for w in WINS:
        f = pd.read_pickle(OUT / "sim" / f"fills-recal-{w}.pkl")
        f = f[f["arm"] == "vt_v1_m3"]
        parts.append(f.assign(pm=f["edge"] * f["shares"]).groupby(["m", "L"]).agg(
            mk=("mk10v", "sum"), pm=("pm", "sum"), sh=("shares", "sum")).reset_index())
    d = pd.concat(parts, ignore_index=True)
    st = start_of(d["m"].to_numpy())
    check(st)
    d["end"] = st + 300.0
    assert d["end"].max() <= SEALED
    return d


@lru_cache(maxsize=16)
def gap_by_market(L: int, span: float, n0: float = 600.0) -> dict[int, float]:
    d = fill_table()
    d = d[d["L"] == L].sort_values("end")
    from ..ctx.slow import market_busy
    mk = market_busy()
    end, cmk, cpm, csh = (d["end"].to_numpy(), np.r_[0, np.cumsum(d["mk"])], np.r_[0, np.cumsum(d["pm"])],
                          np.r_[0, np.cumsum(d["sh"])])
    out = {}
    for i, s in zip(mk["m"], mk["start"]):
        hi, lo = np.searchsorted(end, s, side="right"), np.searchsorted(end, s - span, side="right")
        out[int(i)] = float((cmk[hi] - cmk[lo] - (cpm[hi] - cpm[lo])) / (csh[hi] - csh[lo] + n0))
    return out
