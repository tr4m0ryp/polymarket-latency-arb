"""Lead-lag by cross-correlation, a clock-free supplement to the per-move race.

Each signal is sampled on a 5 ms grid of local receipt time (last price), turned into 100 ms
price changes, and correlated with the reference signal's changes at shifts of -300..+300 ms.
The peak shift is how far the signal leads the reference (> 0 = signal earlier)."""
from __future__ import annotations

import numpy as np

STEP_NS, H, MAXLAG = 5_000_000, 20, 60  # 5 ms grid, 100 ms changes, +-300 ms


def grid(t: np.ndarray, p: np.ndarray, t0: int, n: int) -> np.ndarray:
    g = t0 + STEP_NS * np.arange(n)
    i = np.searchsorted(t, g, side="right") - 1
    return np.where(i >= 0, p[np.clip(i, 0, None)], np.nan)


def lead(sigs: dict, ref: str) -> dict:
    t0 = max(int(t[0]) for t, _ in sigs.values() if len(t)) + 2_000_000_000
    t1 = min(int(t[-1]) for t, _ in sigs.values() if len(t))
    n = (t1 - t0) // STEP_NS
    if n < 10 * MAXLAG:
        return {}
    r = grid(*sigs[ref], t0, n)
    r = r[H:] - r[:-H]
    out = {}
    for name, (t, p) in sigs.items():
        x = grid(t, p, t0, n)
        x = x[H:] - x[:-H]
        cs = []
        for lag in range(-MAXLAG, MAXLAG + 1):  # corr(x(t), r(t + lag))
            a, b = (x[:len(x) - lag], r[lag:]) if lag >= 0 else (x[-lag:], r[:lag])
            ok = np.isfinite(a) & np.isfinite(b)
            cs.append(np.corrcoef(a[ok], b[ok])[0, 1] if ok.sum() > 100 else np.nan)
        cs = np.array(cs)
        k = int(np.nanargmax(cs))
        out[name] = {"peak_lead_ms": (k - MAXLAG) * STEP_NS / 1e6,
                     "peak_corr": round(float(cs[k]), 3),
                     "corr_at_0": round(float(cs[MAXLAG]), 3)}
    return out
