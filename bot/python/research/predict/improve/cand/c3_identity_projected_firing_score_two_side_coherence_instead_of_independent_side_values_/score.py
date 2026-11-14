"""The two-side identity and the projected firing score (candidate C3).

At the match, buying Up at the ask and buying Down at 1 - bid obey, whatever the later mark,

    v_up + v_dn = -(spread_m + fee(ask_up_m) + fee(ask_dn_m)) = -c_m

(research/predict/model/derive.py side_values: the two targets share the mid mark). The frozen
v1 model predicts each side on its own side-oriented row, so pred_up + pred_dn drifts from
-c. e = pred_up + pred_dn + c (c on the book we saw) is the common-mode part: e > 0 means the
model sees value on BOTH sides (volatility without direction).

Scores (edge of the side the frozen rule picks; side = argmax pred, unchanged, because
v_up - v_dn = pred_up - pred_dn under every projection below):
    proj, lam : edge = pred - lam * e / 2       (lam = 1: (pred - pred_other) / 2 - c / 2)
    cap,  lam : edge = pred - lam * max(e, 0) / 2   (only removes common-mode optimism)
    floor     : edge = pred, and fire only if pred - e / 2 >= floor (a second gate)"""
from __future__ import annotations

import numpy as np
import pandas as pd


def fee(p):
    """Taker fee per share at our 0% rebate tier (research/strategy fee)."""
    return 0.07 * p * (1 - p)


def costs(tab: pd.DataFrame) -> np.ndarray:
    """c = spread + fee(ask_up) + fee(ask_dn), $ per share pair, on the book we saw."""
    ba, bb = tab["pm_ba"].to_numpy(float) / 100, tab["pm_bb"].to_numpy(float) / 100
    return (ba - bb) + fee(ba) + fee(1 - bb)


def resid(tab: pd.DataFrame, pu, pd_, c=None) -> np.ndarray:
    """Common-mode residual e = pred_up + pred_dn + c ($ per share; 0 if the model is coherent).
    c defaults to the seen book's cost; cost.chat gives the expected match-time cost."""
    return np.asarray(pu, float) + np.asarray(pd_, float) + (costs(tab) if c is None else c)


def projected(tab: pd.DataFrame, pu, pd_, mode: str = "proj", lam: float = 1.0, c=None):
    """Side values (v_up, v_dn) the firing rule thresholds, and e."""
    pu, pd_ = np.asarray(pu, float), np.asarray(pd_, float)
    e = resid(tab, pu, pd_, c)
    if mode == "proj":
        s = lam * e / 2
    elif mode == "cap":
        s = lam * np.maximum(e, 0.0) / 2
    elif mode == "none":
        s = np.zeros_like(e)
    else:
        raise ValueError(mode)
    return pu - s, pd_ - s, e
