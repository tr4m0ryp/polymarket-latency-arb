"""One decision row -> the two side-oriented model inputs, without pandas.

Reproduces research/predict/model/derive.py `add_derived` and orient.py `orient` on a single
row, including their float32 arithmetic: the offline table stores features as float32 and
pandas keeps float32 through the derived columns, so the same tree thresholds see the same
values. Column roles (neutral, swapped bid / ask kinds, sign-flipped) come from the research
module itself, not a copy."""
from __future__ import annotations

import math
import struct

import numpy as np
from scipy.special import ndtri

from research.predict.model.derive import SCALED
from research.predict.model.orient import NEUTRAL, SWAP

F32 = np.float32
_SW = dict(SWAP + [(b, a) for a, b in SWAP])


_S = struct.Struct("f")


def f32(x: float) -> float:
    """Round to float32: one float32 array operation (+ - * / are correctly rounded, so the
    float64 result rounded once equals numpy's float32 result)."""
    return _S.unpack(_S.pack(x))[0]


F007 = f32(0.07)   # pandas casts the 0.07 scalar to the float32 column dtype


def _fee32(p: float) -> float:
    return f32(f32(F007 * p) * f32(1 - p))


class Vectorizer:
    def __init__(self, vf: list[str]):
        self.vf = list(vf)
        self.base = sorted({c for c in vf if c not in ("tok_mid", "seen", "half_spread")}
                           | {_SW[c] for c in vf if c in _SW} | {"pm_mid", "pm_ba", "pm_bb", "zs", "fair_p"})
        pos = {c: i for i, c in enumerate(self.base)}
        n = len(vf)
        self.iu, self.idn = np.zeros(n, int), np.zeros(n, int)
        self.sdn = np.ones(n, F32)
        self.special = {}
        for j, c in enumerate(vf):
            if c in ("tok_mid", "seen", "half_spread"):
                self.special[j] = c
                continue
            self.iu[j] = pos[c]
            if c in NEUTRAL:
                self.idn[j] = pos[c]
            elif c in _SW:
                self.idn[j] = pos[_SW[c]]
            else:
                self.idn[j], self.sdn[j] = pos[c], F32(-1)
        self.pos = pos
        self.scaled = [(c, pos[f"{c}_c"]) for c in SCALED if f"{c}_c" in pos]

    def base_vec(self, f: dict) -> np.ndarray:
        """Base columns as float32, derived columns as research/predict/model/derive.py
        computes them (float32 column arithmetic emulated with f32 per operation)."""
        nan = math.nan
        v = np.array([f.get(c, nan) for c in self.base], dtype=F32)
        pos = self.pos
        mid = float(v[pos["pm_mid"]])
        zq = float(ndtri(min(max(mid, 0.02), 0.98))) if mid == mid else nan
        delta = 100 * math.exp(-zq ** 2 / 2) / math.sqrt(2 * math.pi) * float(v[pos["zs"]]) * 1e-4
        if "delta" in pos:
            v[pos["delta"]] = delta
        for c, k in self.scaled:
            v[k] = float(v[pos[c]]) * delta
        ba, bb = f32(float(v[pos["pm_ba"]]) / 100), f32(float(v[pos["pm_bb"]]) / 100)
        fp = float(v[pos["fair_p"]])
        if "fair_edge_up" in pos:
            v[pos["fair_edge_up"]] = f32(f32(fp - ba) - _fee32(ba))
        if "fair_edge_dn" in pos:
            b1 = f32(1 - bb)
            v[pos["fair_edge_dn"]] = f32(f32(f32(1 - fp) - b1) - _fee32(b1))
        self._seen = (ba, bb, mid)
        return v

    def sides(self, f: dict) -> tuple[np.ndarray, np.ndarray]:
        """(x_up, x_down) as float64, NaN / inf -> 0 (research model/learners.py clean)."""
        v = self.base_vec(f)
        ba, bb, mid = self._seen
        xu, xd = v[self.iu], v[self.idn] * self.sdn
        su, sd, mdn = ba, f32(1 - bb), f32(1 - mid)
        for j, c in self.special.items():
            if c == "tok_mid":
                xu[j], xd[j] = mid, mdn
            elif c == "seen":
                xu[j], xd[j] = su, sd
            else:
                xu[j], xd[j] = f32(su - mid), f32(sd - mdn)
        return _clean(xu), _clean(xd)


def _clean(x: np.ndarray) -> np.ndarray:
    return np.nan_to_num(x, nan=0.0, posinf=0.0, neginf=0.0).astype(np.float64)
