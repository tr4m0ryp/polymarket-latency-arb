"""Recalibration forms for a frozen value model's prediction p ($/share).

online(...)   : self-calibration from delayed labels. The 1 s target of a decision at t is
                observable at t + L + 150 ms + 1 s from the public book (the 10 s markout 9 s
                later), for every row (traded or not), so the bot can track its own bias live.
                On "calibration rows" (the chosen side with p in a band) keep exponentially
                decayed sums (time constant tau) of the realised value y and of p, over labels
                already observed at query time; ratio form: p * (S_y + k) / (S_p + k);
                additive form: p + (S_y - S_p) / (W + n0); applied to rows with p >= domain.
                k = n0 * 0.05 shrinks toward no change when few labels are in the window.
isotonic(...) : static monotone map p -> E[y | p] per regime level, fitted on select rows.
margin_scale  : static margin per regime level (the margin multiplied by a factor)."""
from __future__ import annotations

import numpy as np
from sklearn.isotonic import IsotonicRegression

from ......predict.feats.decay import decay_sum, decayed_at

HOLD = 0.150
MARK = 1.0


def online(tq: np.ndarray, pq: np.ndarray, t: np.ndarray, p: np.ndarray, y: np.ndarray, L: int,
           tau: float, band=(0.02, 1.0), domain: float = 0.02, n0: float = 30.0, kind: str = "ratio",
           lag: float = MARK) -> np.ndarray:
    """Adjusted predictions at query times tq (any order) from labelled rows (t, p, y): labels
    are rows with band[0] <= p < band[1]; a label is usable `lag` s after its match (1 s for
    the 1 s target, 10 s for the 10 s markout); only queries with pq >= domain move (rows
    below never fire, and the bias is only measured on the band)."""
    w = (p >= band[0]) & (p < band[1]) & np.isfinite(y)
    tl = t[w] + L / 1000 + HOLD + lag + 0.005
    o = np.argsort(tl, kind="stable")
    tl, pl, yl = tl[o], p[w][o], y[w][o]
    if not len(tl):
        return pq.copy()
    sy = decayed_at(tl, decay_sum(tl, yl, tau), tau, tq)
    sp = decayed_at(tl, decay_sum(tl, pl, tau), tau, tq)
    if kind == "ratio":
        k = n0 * 0.05
        adj = pq * (np.maximum(sy, 0) + k) / (np.maximum(sp, 0) + k)
    else:
        sw = decayed_at(tl, decay_sum(tl, np.ones(len(tl)), tau), tau, tq)
        adj = pq + (sy - sp) / (sw + n0)
    return np.where(pq >= domain, adj, pq)


class Isotonic:
    """p -> E[y | p] per regime level (levels from common.level), fitted on rows with p >= a;
    rows below a keep p (they never fire)."""

    def __init__(self, a: float = 0.0):
        self.a, self.f = a, {}

    def fit(self, p: np.ndarray, y: np.ndarray, lv: np.ndarray) -> "Isotonic":
        for k in np.unique(lv):
            w = (lv == k) & (p >= self.a) & np.isfinite(y)
            self.f[k] = IsotonicRegression(out_of_bounds="clip").fit(p[w], y[w])
        return self

    def __call__(self, p: np.ndarray, lv: np.ndarray) -> np.ndarray:
        out = p.copy()
        for k, f in self.f.items():
            w = (lv == k) & (p >= self.a)
            if w.any():
                out[w] = f.predict(p[w])
        return out


def margin_scale(p: np.ndarray, lv: np.ndarray, factors: dict) -> np.ndarray:
    """Dividing p by the level's factor = firing at margin * factor."""
    f = np.vectorize(lambda k: factors.get(int(k), 1.0))(lv) if len(lv) else lv
    return p / f
