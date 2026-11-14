"""Calibration of the frozen 1 s model by mechanism covariate: does it over-predict when the
leading venue is busy, when our feed lags, or when the receipt clock compresses a burst?"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .stats import boot_ratio, deciles, fmt
from .tables import edges


def _slope(g: pd.DataFrame) -> float:
    x, y = g["pred"].to_numpy(float), g["y1"].to_numpy(float)
    x = x - x.mean()
    return float((x * (y - y.mean())).sum() / (x * x).sum()) if (x * x).sum() > 0 else np.nan


def _row(g: pd.DataFrame) -> dict:
    f = g[g["pred"] >= 0.03]
    y1 = boot_ratio(g, "y1")
    yf = boot_ratio(f, "y1") if len(f) > 20 else (np.nan,) * 3
    return {"rows": len(g), "mkts": g["m"].nunique(),
            "pred c": f"{100 * g['pred'].mean():.2f}",
            "real 1s c": fmt(y1[0], y1[1], y1[2], 2, 100),
            "real 10s c": f"{100 * g['y10'].mean():+.2f}",
            "real/pred": f"{g['y1'].mean() / g['pred'].mean():.2f}",
            "slope": f"{_slope(g):.2f}",
            "fire rows (>=3c)": len(f),
            "fire pred c": f"{100 * f['pred'].mean():.2f}" if len(f) else "n/a",
            "fire real 1s c": fmt(yf[0], yf[1], yf[2], 2, 100)}


def calib_tables(rows: pd.DataFrame):
    r = rows[np.isfinite(rows["y1"]) & np.isfinite(rows["pred"])].copy()
    out = []
    for col, name in (("cvol30", "fair-value churn cvol30"), ("pmsg10", "perp msgs / s"),
                      ("lag_feed", "our perp feed lag"), ("compress", "receipt compression"),
                      ("sigma", "model sigma input"), ("pm_stale", "pm_stale input")):
        if col not in r:
            continue
        rr = r[np.isfinite(r[col])].copy()
        b = deciles(rr[col], 5)
        rows_ = []
        for k, e in zip(sorted(b.unique()), edges(rr, col, b)):
            d = {col: f"Q{k + 1} {e}"}
            d.update(_row(rr[b == k]))
            rows_.append(d)
        out.append((f"frozen v1_L0 calibration by quintile of {name} (rows pred >= 2 c)",
                    pd.DataFrame(rows_), f"calib_{col}"))
    rows_ = []
    for w in ("dev3", "test3r1", "ext"):
        d = {"window": w}
        d.update(_row(r[r["window"] == w]))
        rows_.append(d)
    out.append(("frozen v1_L0 calibration by window", pd.DataFrame(rows_), "calib_window"))
    return out
