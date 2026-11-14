"""Order pools (one arm, one hold scenario, one set of hours) and path resampling.

A path is a sequence of pool markets played back to back (5 min each). `rotations`: the real
time order started at every market (circular), the hours' own clustering kept. `bootstrap`:
markets drawn with replacement (market-block bootstrap), any number of days."""
from __future__ import annotations

from functools import lru_cache

import numpy as np

from .. import OUT


@lru_cache(maxsize=1)
def stream() -> dict:
    with np.load(OUT / "stream.npz") as z:
        return {k: z[k] for k in z.files}


class Pool_:
    def __init__(self, arm: str, scen: str, hours: str):
        s = stream()
        sel = (s["arm"] == arm) & s["ok"]
        if hours != "all":
            sel &= s["test"] if hours == "test" else ~s["test"]
        idx = np.flatnonzero(sel)
        idx = idx[np.lexsort((s["t"][idx], s["m"][idx]))]
        m = s["m"][idx]
        self.markets, lo = np.unique(m, return_index=True)
        self.m_lo = lo.astype(np.int64)
        self.m_hi = np.r_[lo[1:], len(idx)].astype(np.int64)
        self.n_markets = len(self.markets)
        self.tr = (s["t"][idx] - (s["end"][idx] - 300.0)).astype(np.float64)
        self.side = s["side"][idx].astype(np.float64)
        self.lim = s["seen"][idx].astype(np.float64)
        self.won = s["won"][idx].astype(np.float64)
        self.score = s["score"][idx].astype(np.float64)
        self.tau = s["tau"][idx].astype(np.float64)
        self.v1val = s["v1val"][idx].astype(np.float64)
        self.h = s[f"{scen}_h"][idx].astype(np.float64)
        self.off = s[f"{scen}_off"][idx].astype(np.int64)
        self.nlev = s[f"{scen}_n"][idx].astype(np.int64)
        self.lcol = s[f"{scen}_col"].astype(np.int64)
        self.ltick = s[f"{scen}_tick"].astype(np.int64)
        self.lsh = s[f"{scen}_sh"].astype(np.float64)
        self.name = f"{arm}/{scen}/{hours}"

    def arrays(self):
        return (self.m_lo, self.m_hi, self.tr, self.side, self.lim, self.won, self.score, self.tau, self.v1val,
                self.h, self.off, self.nlev, self.lcol, self.ltick, self.lsh)


def rotations(n: int, length: int = 288) -> np.ndarray:
    """Every start market of the real order, `length` markets each (wrapping)."""
    return ((np.arange(n)[:, None] + np.arange(length)[None, :]) % n).astype(np.int64)


def bootstrap(n: int, paths: int, length: int = 288, seed: int = 0) -> np.ndarray:
    return np.random.default_rng(seed).integers(0, n, (paths, length)).astype(np.int64)
