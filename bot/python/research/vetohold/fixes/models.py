"""The four per-order predictors behind the fixes, all from decision-time features (receipt
clock, research/vetohold/replay/feats.py), fixed hyper-parameters (no tuning).

  p_surv  share of hold draws in which the order fills at seen (i = 0)  (fillp_k0)
  v_fill  10 s markout PnL per filled share, given a fill               (pnl / sh, filled rows)
  istar   needed offset i* (c): first ask with depth at the match instant minus seen, mean
          over hold draws, 31 when no depth within seen + 30 c
  dep_m   shares at <= seen + 2 c still resting at match (log1p)
  ev      PnL per $ of intended notional under the hold                 (pnl / (60 seen))"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor

HGB = dict(max_iter=200, learning_rate=0.05, max_leaf_nodes=15, min_samples_leaf=50, l2_regularization=1.0,
           random_state=0)
TARGETS = ("p_surv", "v_fill", "istar", "dep_m", "ev")


def feats(d: pd.DataFrame) -> list[str]:
    return sorted(c for c in d.columns if c.startswith("f_"))


def target(d: pd.DataFrame, name: str) -> tuple[np.ndarray, np.ndarray]:
    """(y, mask of rows that train this target)."""
    if name == "p_surv":
        return d["fillp_k0"].to_numpy(), np.ones(len(d), bool)
    if name == "v_fill":
        sh = d["sh_k0_60"].to_numpy()
        return np.where(sh > 0, d["pnl_k0_60"].to_numpy() / np.maximum(sh, 1e-9), 0.0), sh > 0.5
    if name == "istar":
        return istar_target(d), np.ones(len(d), bool)
    if name == "dep_m":
        return np.log1p(d["dep_m"].to_numpy()), np.ones(len(d), bool)
    return d["pnl_k0_60"].to_numpy() / (60 * d["seen"].to_numpy()), np.ones(len(d), bool)


def istar_target(d: pd.DataFrame) -> np.ndarray:
    x = d["istar1"].to_numpy(float)
    return np.where(np.isfinite(x), x * (1 - d["istar1_nan"]) + 31 * d["istar1_nan"], 31.0)


def fit(d: pd.DataFrame, cols: list[str]) -> dict:
    out = {}
    for name in TARGETS:
        y, m = target(d, name)
        w = d["sh_k0_60"].to_numpy()[m] if name == "v_fill" else None
        out[name] = HistGradientBoostingRegressor(**HGB).fit(d.loc[m, cols].to_numpy(float), y[m], sample_weight=w)
    return out


def predict(models: dict, d: pd.DataFrame, cols: list[str]) -> dict:
    X = d[cols].to_numpy(float)
    p = {k: m.predict(X) for k, m in models.items()}
    p["p_surv"] = np.clip(p["p_surv"], 0, 1)
    p["dep_m"] = np.expm1(p["dep_m"])
    return p
