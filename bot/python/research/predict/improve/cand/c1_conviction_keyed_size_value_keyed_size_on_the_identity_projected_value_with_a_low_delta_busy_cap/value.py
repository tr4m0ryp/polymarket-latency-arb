"""Per-row quantities the conviction-keyed size reads, from the receipt-clock decision table.

At the match, buying Up at the ask and buying Down at 1 - bid cost together the spread plus
both taker fees more than one share of each side is worth, whatever the later mark:

    v_up + v_dn = -(spread + fee(ask_up) + fee(ask_dn)) = -c

so the symmetric part of a model's two side predictions, e = pred_up + pred_dn + c, is pure
model error (value predicted on BOTH sides is volatility, not direction). The antisymmetric
projection v* = (pred_side - pred_other) / 2 - c / 2 removes it and equals pred_side when
the model respects the identity (e = 0).

delta: cents of fair Up price per bp of BTC at the current mid and time left
(research/predict/model/derive.py), low when volatility is high (the busy hours)."""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.special import ndtri


def fee(p):
    """Taker fee per share at our 0% rebate tier."""
    return 0.07 * p * (1 - p)


def costs(tab: pd.DataFrame) -> np.ndarray:
    """c = spread + fee(ask_up) + fee(ask_dn), $ per share pair, on the book we saw."""
    ba, bb = tab["pm_ba"].to_numpy(float) / 100, tab["pm_bb"].to_numpy(float) / 100
    return (ba - bb) + fee(ba) + fee(1 - bb)


def vstar(tab: pd.DataFrame, pu, pd_) -> tuple[np.ndarray, np.ndarray]:
    """Identity-projected side values (v*_up, v*_dn), $ per share."""
    c = costs(tab)
    pu, pd_ = np.asarray(pu, float), np.asarray(pd_, float)
    return (pu - pd_) / 2 - c / 2, (pd_ - pu) / 2 - c / 2


def resid(tab: pd.DataFrame, pu, pd_) -> np.ndarray:
    """Symmetric residual e = pred_up + pred_dn + c (0 for an identity-consistent model)."""
    return np.asarray(pu, float) + np.asarray(pd_, float) + costs(tab)


def delta(tab: pd.DataFrame) -> np.ndarray:
    """Settlement delta, cents of fair Up price per bp (NaN where the mid is unknown)."""
    z = ndtri(np.clip(tab["pm_mid"].to_numpy(float), 0.02, 0.98))
    return 100 * np.exp(-z ** 2 / 2) / np.sqrt(2 * np.pi) * tab["zs"].to_numpy(float) * 1e-4
