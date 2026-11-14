"""Derived columns shared by the trading models: the settlement delta (cents of the Up token
per bp of BTC), Binance predictors converted to Polymarket cents through it, and the
per-side taker values at each L (targets, never features).

delta = 100 * phi(Phi^-1(mid)) * zscale: a 1 bp perp move shifts fair P(Up) by about
`delta` cents at the current price and time left (signals/feeds.py zscale)."""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.special import ndtri

from ...strategy import fee

SCALED = ["p_dmic0.025", "p_dmic0.05", "p_dmic0.1", "p_dmic0.25", "p_dmic1", "s_dmic0.1",
          "s_dmic0.25", "p_micoff", "s_micoff", "p_imb", "s_imb", "p_ofi0.1", "p_ofi0.4",
          "st_sv0.2", "mic_dev", "basis_dev"]


def add_derived(df: pd.DataFrame) -> pd.DataFrame:
    mid = df["pm_mid"].to_numpy(float)
    zq = ndtri(np.clip(mid, 0.02, 0.98))
    delta = 100 * np.exp(-zq ** 2 / 2) / np.sqrt(2 * np.pi) * df["zs"].to_numpy(float) * 1e-4
    df["delta"] = delta.astype(np.float32)
    for c in SCALED:
        if c in df:
            df[f"{c}_c"] = (df[c].to_numpy(float) * delta).astype(np.float32)
    if "ft_sv0.2" in df:
        df["ft_sv0.2_c"] = (df["ft_sv0.2"].to_numpy(float) * delta).astype(np.float32)
    df["fair_edge_up"] = (df["fair_p"] - df["pm_ba"] / 100 - fee(df["pm_ba"] / 100)).astype(np.float32)
    df["fair_edge_dn"] = ((1 - df["fair_p"]) - (1 - df["pm_bb"] / 100)
                          - fee(1 - df["pm_bb"] / 100)).astype(np.float32)
    return df


def side_values(df: pd.DataFrame, L: int, k: int = 10) -> tuple[np.ndarray, np.ndarray]:
    """Per-share value in $ of buying Up / Down at the best venue ask at the match time
    (t + L + 150 ms), marked at the venue mid k s later, after the taker fee. Best level
    only, no competition: the simulator does depth and rivals."""
    ba, bb = df[f"x_ba{L}"].to_numpy(float) / 100, df[f"x_bb{L}"].to_numpy(float) / 100
    mk = df[f"x_m{k}_{L}"].to_numpy(float)
    up = np.where((ba > 0.005) & (ba < 0.995), mk - ba - fee(ba), np.nan)
    dn = np.where((bb > 0.005) & (bb < 0.995), (1 - mk) - (1 - bb) - fee(1 - bb), np.nan)
    return up, dn
