"""Shared loaders and statistics for the calibration diagnostic.

chosen(win, model): one row per decision, the side the model would buy (higher prediction),
with `pred` (model output, $/share), the realised 1 / 3 / 10 s taker values at the model's L
and the regime columns. Regime levels use cutpoints fixed on run 2 train rows (`cuts`), so a
window's level mix is its drift. Bootstrap = over markets (all rows of a market together)."""
from __future__ import annotations

from functools import lru_cache

import numpy as np
import pandas as pd

from .. import CACHE, SEALED
from ..safe import check, start_of

L_OF = {"v1_L0": 0, "v1_L-40": -40, "v3p_L0": 0}
REGIMES = ("bn10", "bn60", "rv1", "rv10", "rv60", "pm10", "pmtop10", "pmtr60", "jump10", "busy")
LEVELS = ("quiet", "mid", "busy")


@lru_cache(maxsize=8)
def rows(win: str) -> pd.DataFrame:
    d = pd.read_pickle(CACHE / f"rows-{win}.pkl")
    check(start_of(d["m"].unique()))
    assert d["t"].max() < SEALED
    return d


def busy_index(d: pd.DataFrame, ref: pd.DataFrame | None = None) -> np.ndarray:
    """Composite activity: mean of the train-standardised logs of the Binance message rate,
    the 60 s realised volatility and the Polymarket trade rate (all 60 s windows: slow,
    regime-like, not the instant)."""
    ref = d if ref is None else ref
    z = []
    for c in ("bn60", "rv60", "pmtr60"):
        x, r = np.log1p(d[c].to_numpy(float) * (100 if c == "rv60" else 1)), \
            np.log1p(ref[c].to_numpy(float) * (100 if c == "rv60" else 1))
        z.append((x - r.mean()) / r.std())
    return np.mean(z, axis=0)


@lru_cache(maxsize=1)
def cuts() -> dict:
    """Tertile cutpoints on train chosen rows; a regime with a mass at zero puts all zeros in
    `quiet` and splits the positive rest at its median."""
    tr = rows("train")
    out = {}
    for c in REGIMES:
        x = busy_index(tr) if c == "busy" else tr[c].to_numpy(float)
        if (x == 0).mean() > 0.3:
            out[c] = (1e-12, float(np.median(x[x > 0])))
        else:
            out[c] = tuple(float(v) for v in np.quantile(x, [1 / 3, 2 / 3]))
    return out


def level(d: pd.DataFrame, c: str) -> np.ndarray:
    x = busy_index(d, rows("train")) if c == "busy" else d[c].to_numpy(float)
    lo, hi = cuts()[c]
    return np.where(x < lo, 0, np.where(x < hi, 1, 2))


def chosen(win: str, model: str) -> pd.DataFrame:
    d = rows(win)
    L = L_OF[model]
    key = d["m"].to_numpy().astype(np.int64) * 10_000_000 + d["row"].to_numpy().astype(np.int64)
    d = d.iloc[np.lexsort((-d["side"].to_numpy(), key))]
    sd = d["side"].to_numpy()
    assert (sd[0::2] == 1).all() and (sd[1::2] == -1).all(), "unpaired side rows"
    p = d[f"p_{model}"].to_numpy(float)
    pick = np.where(p[0::2] >= p[1::2], 0, 1) + np.arange(0, len(d), 2)
    c = d.iloc[pick].copy()
    c["pred"] = c[f"p_{model}"].astype(float)
    for k in (1, 3, 10):
        c[f"r{k}"] = c[f"v{k}_{L}"].astype(float)
    c = c[(c[f"bad{L}"] == 0) & np.isfinite(c["r1"]) & np.isfinite(c["r10"])]
    c["busy"] = busy_index(c, rows("train"))
    return c.reset_index(drop=True)


def boot_ratio(m: np.ndarray, num: np.ndarray, den: np.ndarray, B: int = 1000, seed: int = 3):
    """Ratio of sums with a market-bootstrap 95% CI: (point, lo, hi)."""
    if not len(m):
        return np.nan, np.nan, np.nan
    g = pd.DataFrame({"m": m, "n": num, "d": den}).groupby("m").sum()
    n, dd = g["n"].to_numpy(), g["d"].to_numpy()
    k = np.random.default_rng(seed).integers(0, len(g), size=(B, len(g)))
    r = n[k].sum(1) / np.maximum(dd[k].sum(1), 1e-12)
    return n.sum() / max(dd.sum(), 1e-12), np.percentile(r, 2.5), np.percentile(r, 97.5)


def fmt(p, lo, hi, s=100, nd=2) -> str:
    return f"{s * p:+.{nd}f} [{s * lo:+.{nd}f}, {s * hi:+.{nd}f}]"
