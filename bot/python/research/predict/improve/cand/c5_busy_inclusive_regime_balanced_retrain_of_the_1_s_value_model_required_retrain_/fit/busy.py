"""Busy index of every training row and the regime weights of the retrain.

Busy index = the calibration diagnostic's label-free activity score (ctx/load.busy: mean of the
train-standardised log Binance perp message rate, 60 s realised volatility and Polymarket
trade rate over 60 s), causal at the row time. The ctx cache is aligned with each market's
decision table; loaded rows are matched to it by their receipt time t (strictly increasing
per market, so the match is exact).

Regime weights: tertile cut points of the busy index on run 2 train rows only, then
    w = share(tertile)^-alpha, normalised to mean 1
(alpha = 1: every tertile carries equal total weight, the "regime-balanced" retrain;
alpha = 0: unweighted). `tilt` multiplies the top tertile on top of that (busy upweighting)."""
from __future__ import annotations

import numpy as np
import pandas as pd

from .....model.data import TAB
from ....diag.calibration.ctx.load import busy, ctx


def busy_rows(rows: pd.DataFrame) -> np.ndarray:
    """Busy index per loaded row (rows: fold.load_rows output, columns m and t)."""
    out = np.full(len(rows), np.nan)
    m = rows["m"].to_numpy()
    t = rows["t"].to_numpy(float)
    for i in np.unique(m):
        with np.load(TAB / f"{int(i)}.npz") as z:
            tf = z["t"].astype(float)
        b = busy(ctx(int(i), len(tf)))
        k = np.flatnonzero(m == i)
        j = np.searchsorted(tf, t[k])
        assert (j < len(tf)).all() and np.array_equal(tf[j], t[k]), f"market {i}: rows do not match ctx"
        out[k] = b[j]
    return out


def tertile_cuts(b_train: np.ndarray) -> tuple[float, float]:
    b = b_train[np.isfinite(b_train)]
    return float(np.quantile(b, 1 / 3)), float(np.quantile(b, 2 / 3))


def tertile(b: np.ndarray, cuts) -> np.ndarray:
    return np.digitize(np.nan_to_num(b, nan=0.0), cuts).astype(np.int8)   # 0 quiet, 1 mid, 2 busy


def weights(ter: np.ndarray, alpha: float = 1.0, tilt: float = 1.0) -> tuple[np.ndarray, dict]:
    share = np.array([(ter == k).mean() for k in range(3)])
    w = np.where(share[ter] > 0, share[ter], 1.0) ** -alpha
    w = w * np.where(ter == 2, tilt, 1.0)
    w = w / w.mean()
    info = {"share": share.round(4).tolist(), "w": [float(w[ter == k].mean()) if (ter == k).any() else None
                                                    for k in range(3)]}
    return w, info
