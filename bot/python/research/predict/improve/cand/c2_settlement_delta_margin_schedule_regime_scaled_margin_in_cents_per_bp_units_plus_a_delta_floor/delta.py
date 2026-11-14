"""Settlement delta of every decision row: cents of the token per bp of BTC at the current venue
mid and time left (same formula as model/derive.py and the loss-anatomy diagnostic; symmetric
in mid, so it is the same for the Up and the Down token)."""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.special import ndtri

SEALED = 1791744900          # prereg2 test segment starts here: never touched


def delta(tab: pd.DataFrame) -> np.ndarray:
    """100 * phi(Phi^-1(mid)) * zscale * 1e-4 per row; NaN where zs or the mid is missing."""
    zq = ndtri(np.clip(tab["pm_mid"].to_numpy(float), 0.02, 0.98))
    return 100 * np.exp(-zq ** 2 / 2) / np.sqrt(2 * np.pi) * tab["zs"].to_numpy(float) * 1e-4


def assert_unsealed(starts, what: str = "markets") -> None:
    s = np.asarray(starts, dtype=float)
    assert len(s) == 0 or (np.isfinite(s).all() and s.max() < SEALED), f"{what}: sealed market"
