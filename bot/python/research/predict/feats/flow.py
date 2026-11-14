"""Trade-flow features of one trade stream (spot @trade, or perp @trade on run 3): signed
volume (taker buys +) and trade arrival intensity, decayed at several time scales and
normalised by the touch depth of the matching book stream."""
from __future__ import annotations

import numpy as np

from .decay import decay_sum, decayed_at

TAUS = (0.05, 0.2, 1.0)


class TradeStream:
    def __init__(self, tr: dict, big_q: float = 1.0):
        self.t = tr["t"]
        sgn = np.where(tr["m"] > 0, -1.0, 1.0)  # buyer is maker -> taker sold
        q = tr["q"].astype(float)
        self.s = {k: decay_sum(self.t, sgn * q, k) for k in TAUS}
        self.n = decay_sum(self.t, np.ones(len(self.t)), 0.2)
        self.big = decay_sum(self.t, sgn * (q >= big_q), 0.2)  # block trades (fixed BTC size)

    def features(self, q: np.ndarray, p: str, depth: np.ndarray) -> dict:
        if not len(self.t):
            return {}
        f = {f"{p}_sv{k:g}": decayed_at(self.t, s, k, q) / depth for k, s in self.s.items()}
        f[f"{p}_tn"] = np.log1p(decayed_at(self.t, self.n, 0.2, q) / 0.2)
        f[f"{p}_big"] = decayed_at(self.t, self.big, 0.2, q)
        return f
