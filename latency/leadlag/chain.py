"""Does Binance lead the Chainlink BTC/USD feed that settles 5m/15m? (open question 1)
Cross-correlates 1 s log returns on the venues' own clocks (Binance trade time,
Chainlink observation time) for lags -10..+10 s."""
from __future__ import annotations

import numpy as np
import pandas as pd

import spot


def lead(tr: pd.DataFrame, cl: pd.DataFrame, max_lag: int = 10) -> dict:
    cl = cl.drop_duplicates("obs").sort_values("obs")
    lo = int(max(tr["ts"].iloc[0], cl["obs"].iloc[0])) + 1
    hi = int(min(tr["ts"].iloc[-1], cl["obs"].iloc[-1]))
    grid = np.arange(lo, hi, 1.0)
    b = np.diff(np.log(spot.price_at(tr, grid)))
    i = np.searchsorted(cl["obs"].to_numpy(), grid, side="right") - 1
    c = np.diff(np.log(cl["px"].to_numpy()[np.clip(i, 0, None)]))
    xc = {}
    for k in range(-max_lag, max_lag + 1):  # k > 0: Chainlink moves k s after Binance
        x, y = (b[: len(b) - k], c[k:]) if k >= 0 else (b[-k:], c[: len(c) + k])
        xc[k] = float(np.corrcoef(x, y)[0, 1])
    w = np.array([max(xc[k], 0) for k in range(0, max_lag + 1)])
    return {"xcorr": xc, "peak_lag_s": max(xc, key=xc.get),
            "mean_lag_s": float((w * np.arange(len(w))).sum() / w.sum()),
            "recv_delay_s": float((cl["t"] - cl["obs"]).median()),
            "push_delay_s": float((cl["ts"] - cl["obs"]).median()),
            "basis_usd": float(np.nanmedian(spot.price_at(tr, cl["obs"].to_numpy()) - cl["px"].to_numpy())),
            "seconds": len(grid)}
