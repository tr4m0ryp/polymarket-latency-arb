"""Summaries of path results (sim/kernel.py `out` rows)."""
from __future__ import annotations

import numpy as np


def summary(out: np.ndarray, start: float, hours: float, ruin: float) -> dict:
    fin, mn = out[:, 0], out[:, 1]
    lg = np.log(np.maximum(fin, 1e-9) / start)
    return {"med_log": float(np.median(lg)), "p10_log": float(np.percentile(lg, 10)),
            "mean": float(fin.mean()), "median": float(np.median(fin)), "p10": float(np.percentile(fin, 10)),
            "p90": float(np.percentile(fin, 90)), "p_ruin": float((mn < ruin).mean()),
            "p_loss": float((fin < start).mean()), "maxdd_med": float(np.median(out[:, 2])),
            "maxdd_p90": float(np.percentile(out[:, 2], 90)), "orders_h": float(out[:, 3].mean() / hours),
            "fills_h": float(out[:, 4].mean() / hours), "skips_h": float(out[:, 5].mean() / hours),
            "worst_mkt_$": float(out[:, 6].max()), "worst_mkt_p99_$": float(np.percentile(out[:, 6], 99)),
            "worst_mkt_frac": float(out[:, 7].max()), "worst_mkt_frac_p99": float(np.percentile(out[:, 7], 99)),
            "both_sides": float(out[:, 9].sum() / max(out[:, 8].sum(), 1)),
            "pair_locks": float(out[:, 10].sum() / max(out[:, 9].sum(), 1))}
