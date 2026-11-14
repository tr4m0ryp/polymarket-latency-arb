"""Exponentially decayed event sums (the Hawkes-style intensity of a marked point process)
and as-of lookups on the receipt clock.

S(t_i) = sum_{j <= i} x_j exp(-(t_i - t_j) / tau), computed in vectorized chunks so the
exponent never overflows; S(q) at any later time q decays from the last event <= q."""
from __future__ import annotations

import numpy as np


def decay_sum(t: np.ndarray, x: np.ndarray, tau: float) -> np.ndarray:
    n = len(t)
    out = np.empty(n, dtype=float)
    if not n:
        return out
    span = 400.0 * tau
    edges = np.flatnonzero(np.diff(np.floor((t - t[0]) / span))) + 1
    starts, ends = np.r_[0, edges], np.r_[edges, n]
    carry, t_prev = 0.0, t[0]
    for s, e in zip(starts, ends):
        tc = t[s]
        w = np.exp((t[s:e] - tc) / tau)
        cs = np.cumsum(x[s:e] * w)
        out[s:e] = (cs + carry * np.exp(-(tc - t_prev) / tau)) / w
        carry, t_prev = out[e - 1], t[e - 1]
    return out


def asof(t: np.ndarray, q: np.ndarray) -> np.ndarray:
    """Index of the last event with t <= q (-1 if none)."""
    return np.searchsorted(t, q, side="right") - 1


def at(t: np.ndarray, v: np.ndarray, q: np.ndarray, fill=np.nan) -> np.ndarray:
    i = asof(t, q)
    return np.where(i >= 0, v[np.clip(i, 0, None)], fill)


def decayed_at(t: np.ndarray, s: np.ndarray, tau: float, q: np.ndarray) -> np.ndarray:
    """S(q) from the per-event sums s = decay_sum(t, x, tau)."""
    i = asof(t, q)
    ok = i >= 0
    ic = np.clip(i, 0, None)
    return np.where(ok, s[ic] * np.exp(-(q - t[ic]) / tau), 0.0)


def ewma_level(t: np.ndarray, x: np.ndarray, tau: float) -> np.ndarray:
    """Time-weighted EWMA of a level series (per event), normalised by the decayed weight."""
    num = decay_sum(t, x, tau)
    den = decay_sum(t, np.ones_like(x), tau)
    return num / np.maximum(den, 1e-12)
