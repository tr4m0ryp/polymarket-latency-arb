"""Binance trade series, burst detection, and the spot-implied P(Up).

P(Up) = Phi(ln(S/K) / (sigma * sqrt(tau))): K = mean Binance trade price over the
60 s before the window opens (the strike TWAP proxy, 99% outcome agreement in
the forensic study), sigma = realized 1 s log-return vol over the last 300 s,
tau = seconds to the end (floored at 5 s). Only its CHANGE across a burst is
used, anchored on the book mid before the burst, so a biased level cancels."""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.special import ndtr


def trades(bn: pd.DataFrame) -> pd.DataFrame:
    tr = bn[bn["is_trade"] == 1][["t", "ts", "px"]].sort_values("ts", kind="stable")
    return tr.reset_index(drop=True)


def bursts(tr: pd.DataFrame, thr_bp: float, win: float = 1.0, refractory: float = 3.0) -> pd.DataFrame:
    """Onsets where the trade price moved >= thr_bp over the trailing `win` s
    (Binance server clock). One onset per `refractory` s."""
    ts, px, tr_t = tr["ts"].to_numpy(), tr["px"].to_numpy(), tr["t"].to_numpy()
    j = np.searchsorted(ts, ts - win, side="left")
    r = 1e4 * np.log(px / px[j])
    hit = np.flatnonzero(np.abs(r) >= thr_bp)
    out, last = [], -np.inf
    for i in hit:
        if ts[i] - last >= refractory:
            out.append((ts[i], tr_t[i], np.sign(r[i]), r[i], px[j[i]], px[i]))
            last = ts[i]
    return pd.DataFrame(out, columns=["T0", "R0", "d", "move_bp", "s_before", "s_after"])


def price_at(tr: pd.DataFrame, when: np.ndarray) -> np.ndarray:
    ts, px = tr["ts"].to_numpy(), tr["px"].to_numpy()
    i = np.searchsorted(ts, when, side="right") - 1
    return np.where(i >= 0, px[np.clip(i, 0, None)], np.nan)


def strike(tr: pd.DataFrame, start: float) -> float:
    ts = tr["ts"].to_numpy()
    a, b = np.searchsorted(ts, [start - 60, start])
    if b - a < 30 or ts[0] > start - 55:
        return np.nan
    return float(tr["px"].to_numpy()[a:b].mean())


def sigma_1s(tr: pd.DataFrame, at: float, look: float = 300.0) -> float:
    grid = np.arange(at - look, at, 1.0)
    p = price_at(tr, grid)
    r = np.diff(np.log(p[~np.isnan(p)]))
    return float(r.std()) if len(r) > 60 else np.nan


def p_up(s: np.ndarray, k: float, sig: float, tau: np.ndarray) -> np.ndarray:
    tau = np.maximum(tau, 5.0)
    return ndtr(np.log(s / k) / (sig * np.sqrt(tau)))


def fee(p):
    """Taker fee per share (crypto_fees_v2)."""
    return 0.07 * p * (1 - p)
