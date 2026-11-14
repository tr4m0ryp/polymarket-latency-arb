"""Binance features in windows placed relative to a query time tau (venue clock), signed by a
side d (+1 Up). The leaders' fills follow perp book events by ~250-300 ms (irf.py), so the
trigger window is [tau - 0.33, tau - 0.21]; 'pre' is [tau - 1.0, tau - 0.33] and 'post' is
[tau - 0.21, tau]. Other venues (Coinbase, OKX, Bybit) exist only in side-recorder hours. Moves in bp, flows in BTC (signed taker volume), imbalance in [-1, 1]."""
from __future__ import annotations

import numpy as np

TRIG = (0.33, 0.21)
WINDOWS = {"trig": TRIG, "pre": (1.0, 0.33), "post": (0.21, 0.0), "wide": (0.5, 0.2)}
PRICES = ("perp_micro", "perp_mid", "spot_micro", "spot_mid", "spot_tr",
          "coinbase_micro", "coinbase_mid", "okx_micro", "okx_mid", "bybit_micro", "bybit_mid")
FLOWS = ("spot_flow", "perp_flow", "coinbase_flow", "okx_flow", "bybit_flow")


def move(st, tau, a, b) -> np.ndarray:
    return 1e4 * np.log(st.at(tau - b) / st.at(tau - a))


def binance(s: dict, tau: np.ndarray, d: np.ndarray) -> dict[str, np.ndarray]:
    out: dict[str, np.ndarray] = {}
    for name, (a, b) in WINDOWS.items():
        for k in PRICES:
            if k in s:
                out[f"{k}_{name}"] = d * move(s[k], tau, a, b)
        for k in FLOWS:
            if k in s:
                out[f"{k}_{name}"] = d * (s[k].at(tau - b) - s[k].at(tau - a))
    if "perp_imb" in s:
        out["perp_imb_trig"] = d * s["perp_imb"].at(tau - TRIG[1])
        out["perp_imb_chg"] = d * (s["perp_imb"].at(tau - TRIG[1]) - s["perp_imb"].at(tau - TRIG[0]))
    return out
