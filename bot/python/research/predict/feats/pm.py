"""Polymarket-side and settlement features at query times: our view of the Up book, time
left, the settlement z-scale, how much the perp microprice moved since our view of the book
last changed (staleness, in settlement z-units), the book's own recent repricing, and the
strategy fair model's pending repricing (`pzm`, the value filter of micf)."""
from __future__ import annotations

import numpy as np

from ...strategy import fee  # noqa: F401  (re-exported for callers)
from ...strategy.signals.features import BUCKETS, z


def pm_features(q: np.ndarray, book, fd, perp) -> dict:
    g = book.g_floor(q)
    bb, ba = book.bb_r[g].astype(float), book.ba_r[g].astype(float)
    mid = book.mid(g, ours=True)
    zs = fd.zscale(q) * 1e-4                      # z per bp
    f = {"pm_bb": bb, "pm_ba": ba, "pm_mid": mid, "pm_spr": ba - bb,
         "secs_left": fd.end - q, "lzs": np.log(zs), "sigma": fd.sigma(q)}
    top = np.flatnonzero((np.diff(book.bb_r) != 0) | (np.diff(book.ba_r) != 0)) + 1
    tt = book.t0 + top * 0.005
    i = np.searchsorted(tt, q, side="right") - 1
    last = np.where(i >= 0, tt[np.clip(i, 0, None)], q - 5.0)
    f["pm_tsc"] = np.log(np.maximum(q - last, 1e-3))
    if perp is not None:
        f["pm_stale"] = 1e4 * (perp.level("lmic", q) - perp.level("lmic", last)) * zs
    zm = z(mid)
    for k, (a, b) in enumerate(((0, .2), (.2, 1), (1, 3))):
        ma = book.mid(book.g_floor(q - a), ours=True)
        mb = book.mid(book.g_floor(q - b), ours=True)
        f[f"bk{k}"] = z(ma) - z(mb)
    f["gap"] = np.clip(z(fd.p_model(q)) - zm, -2, 2)
    f["zs"] = zs * 1e4
    return f


def fair_columns(q: np.ndarray, fd) -> dict:
    """Columns the strategy fair models read (signals/fair.py design)."""
    d = {"zs": fd.zscale(q)}
    for s in ("perp", "smid", "pmic", "smic"):
        for k, (a, b) in enumerate(BUCKETS):
            d[f"{s}{k}"] = fd.ret(s, q, a, b) if fd.has(s) else np.full(len(q), np.nan)
    return d
