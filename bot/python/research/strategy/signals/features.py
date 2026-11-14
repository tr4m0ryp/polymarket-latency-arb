"""Decision candidates of one market and everything a rule may read at those instants.

Candidates (our receipt clock): every change of the perp mid, the spot trade price, the spot
mid, or our view of the Up book's top, inside [start + 3, end - 5]. Features use only data
received by then. The target (for fitting fair value only, never for decisions) is the venue
Up mid 3 s later in z-space, relative to our current view of the mid.

micro=True (v2 tables) adds every perp / spot bookTicker update whose microprice moved
>= 0.001 bp over the last 0.1 s as a candidate, and the microprice moves (pmic*, smic*)."""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.special import ndtri

from .feeds import Feeds

BUCKETS = ((0, .05), (.05, .1), (.1, .2), (.2, .4), (.4, .8), (.8, 1.6), (1.6, 3.2))
H = 3.0


def z(p):
    return ndtri(np.clip(p, 0.02, 0.98))


def _changes(t, x):
    if len(t) < 2:
        return t[:0]
    return t[1:][np.diff(x) != 0]


MIC_WIN = (0.05, 0.1, 0.25, 0.5, 1.0)


def candidates(fd: Feeds, book, micro: bool = False) -> np.ndarray:
    parts = [_changes(*fd.src[s]) for s in ("spot", "smid", "perp") if fd.has(s)]
    for s in (("pmic", "smic") if micro else ()):
        if fd.has(s):
            t = fd.src[s][0]
            parts.append(t[np.abs(fd.ret(s, t, 0, 0.1)) >= 0.001])
    g = np.arange(book.n)
    top = np.flatnonzero((np.diff(book.bb_r) != 0) | (np.diff(book.ba_r) != 0)) + 1
    parts.append(book.t0 + g[top] * 0.005)
    t = np.unique(np.round(np.concatenate(parts), 3))
    return t[(t > fd.start + 3) & (t < fd.end - 5)]


def table(m: dict, book, micro: bool = False) -> pd.DataFrame:
    fd = Feeds(m)
    t = candidates(fd, book, micro)
    if not len(t) or np.isnan(fd.K):
        return pd.DataFrame()
    g = book.g_floor(t)
    d = {"t": t, "secs_left": fd.end - t, "bb": book.bb_r[g], "ba": book.ba_r[g],
         "mid": book.mid(g, ours=True), "zs": fd.zscale(t), "sigma": fd.sigma(t)}
    for s in ("perp", "smid"):
        for k, (a, b) in enumerate(BUCKETS):
            d[f"{s}{k}"] = fd.ret(s, t, a, b) if fd.has(s) else np.full(len(t), np.nan)
    for s in ("spot", "perp", "smid"):
        for w in (0.2, 0.5, 1.0, 3.0):
            d[f"{s}_r{w:g}"] = fd.ret(s, t, 0, w) if fd.has(s) else np.full(len(t), np.nan)
    if micro:
        for s in ("pmic", "smic"):
            nan = np.full(len(t), np.nan)
            for w in MIC_WIN:
                d[f"{s}_r{w:g}"] = fd.ret(s, t, 0, w) if fd.has(s) else nan
            for k, (a, b) in enumerate(BUCKETS):
                d[f"{s}{k}"] = fd.ret(s, t, a, b) if fd.has(s) else nan
    zm = z(d["mid"])
    for k, (a, b) in enumerate(((0, .2), (.2, 1), (1, 3))):
        ma, mb = book.mid(book.g_floor(t - a), ours=True), book.mid(book.g_floor(t - b), ours=True)
        d[f"bk{k}"] = z(ma) - z(mb)
    d["gap"] = z(fd.p_model(t)) - zm
    d["imb"] = fd.imbalance(t)
    gv = book.g_ceil(t + H)
    d["mid_h"] = book.mid(gv)
    d["y"] = z(d["mid_h"]) - zm
    df = pd.DataFrame(d)
    df["outcome"] = np.nan if m["outcome"] is None else float(m["outcome"])
    for c in df.columns:
        if df[c].dtype == np.float64 and c not in ("t",):
            df[c] = df[c].astype(np.float32)
    return df
