"""Read the per-row context of a market and derive the busy index of the earlier regime-margin
arms (recal/arms.py): mean of the train-standardised log Binance perp message rate, 60 s
realised volatility and Polymarket trade rate. The reference moments come from the gated
train rows of the calibration row cache (rows-train.pkl), as in recal/arms.prepare."""
from __future__ import annotations

import json
from functools import lru_cache

import numpy as np

from .. import CACHE
from . import DIR

BUSY_COLS = ("bn60", "rv60", "pmtr60")


def ctx(i: int, n: int | None = None) -> dict:
    with np.load(DIR / f"{i}.npz") as z:
        out = {k: z[k] for k in z.files}
    if n is not None:
        assert len(out["bn60"]) == n, f"ctx of market {i} does not match its table"
    return out


def _tf(c: str, x: np.ndarray) -> np.ndarray:
    return np.log1p(np.asarray(x, float) * (100 if c == "rv60" else 1))


@lru_cache(maxsize=1)
def busy_ref() -> dict:
    p = CACHE / "busy_ref.json"
    if p.exists():
        return json.loads(p.read_text())
    import pandas as pd
    tr = pd.read_pickle(CACHE / "rows-train.pkl")
    ref = {c: (float(_tf(c, tr[c].to_numpy()).mean()), float(_tf(c, tr[c].to_numpy()).std())) for c in BUSY_COLS}
    p.write_text(json.dumps(ref))
    return ref


def busy(c: dict) -> np.ndarray:
    ref = busy_ref()
    return np.mean([(_tf(k, c[k]) - ref[k][0]) / ref[k][1] for k in BUSY_COLS], axis=0)
