"""Run many paths of one cap set in parallel (numba prange)."""
from __future__ import annotations

import numpy as np
from numba import njit, prange

from .kernel import DAY0, path


@njit(parallel=True, cache=False)   # cache=True would keep a stale inlined kernel.path
def _many(seqs, seeds, cfg, start, day_len, m_lo, m_hi, tr, side, lim, won, score, tau, v1val,
          h, off, nlev, lcol, ltick, lsh, out):
    for p in prange(seqs.shape[0]):
        path(seqs[p], seeds[p], cfg, start, day_len, m_lo, m_hi, tr, side, lim, won, score, tau, v1val,
             h, off, nlev, lcol, ltick, lsh, out[p])


def simulate(pool, seqs: np.ndarray, cfg: np.ndarray, start: float, seed: int = 0, day_len: int = 288) -> np.ndarray:
    """(paths, DAY0 + days) result rows for one cap vector (sim/kernel.py `out` layout)."""
    nd = int(np.ceil(seqs.shape[1] / day_len))
    out = np.zeros((seqs.shape[0], DAY0 + nd))
    seeds = (np.arange(seqs.shape[0]) * 7919 + seed * 104729).astype(np.int64)
    _many(seqs, seeds, cfg, float(start), day_len, *pool.arrays(), out)
    return out
