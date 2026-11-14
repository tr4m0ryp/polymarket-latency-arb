"""The strategy's `pzm` fair value (research/strategy/signals/fair.py, weights from
data/out/strategy/fair-pzm.json), evaluated on one instant.

fair = Phi( Phi^-1(mid) + w . x ), x = lag-bucket log moves (bp) of the perp mid, spot mid,
perp microprice and spot microprice, each times zscale * 1e-4 (settlement z-units)."""
from __future__ import annotations

import json

import numpy as np
from scipy.special import ndtr, ndtri

from research.strategy import OUT as SOUT
from research.strategy.signals.features import BUCKETS

from ..state.book import LMIC, LMID


def zq(p: float) -> float:
    return float(ndtri(min(max(p, 0.02), 0.98))) if p == p else float("nan")


class PZM:
    def __init__(self, path=SOUT / "fair-pzm.json"):
        d = json.loads(path.read_text())
        assert tuple(d["srcs"]) == ("perp", "smid", "pmic", "smic") and not d["extra"] and not d["imb"]
        self.w = np.array(d["w"], dtype=float)

    def x(self, q: float, perp, spot, zs: float) -> np.ndarray:
        out = []
        for st, col in ((perp, LMID), (spot, LMID), (perp, LMIC), (spot, LMIC)):
            h = st.hist
            for a, b in BUCKETS:
                r = 1e4 * (h.at(col, q - a) - h.at(col, q - b))
                out.append((0.0 if r != r else r) * zs * 1e-4)
        return np.array(out)

    def dz(self, q: float, perp, spot, zs: float) -> float:
        return float(self.x(q, perp, spot, zs) @ self.w)

    @staticmethod
    def p(mid: float, dz: float) -> float:
        return float(ndtr(zq(mid) + dz))
