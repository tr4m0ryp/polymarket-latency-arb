"""Spot-trade state: the trade-flow features (research/predict/feats/flow.py `TradeStream`)
and the settlement scale of research/strategy/signals/feeds.py `Feeds`, incremental.

Settlement (5m markets): Up wins if the 60 s TWAP at the end >= the 60 s TWAP at the start
(K, Binance spot proxy on the trade clock T). sigma = std of 1 s log returns of the last
trade price over the last 300 s ending at floor(q); zscale = 1 / (sigma * sqrt(eff)) with
eff = tau - 40 while tau >= 60 s, tau / 3 after. Values on the trade clock use what has been
received; the offline arrays also hold trades received a few ms after q (tiny look-ahead)."""
from __future__ import annotations

import math
from bisect import bisect_right

import numpy as np
from scipy.special import ndtr

from .series import Series

TAUS = (0.05, 0.2, 1.0)
SIG_FLOOR = 0.03e-4
NAN = float("nan")


class TradeFlow:
    """Signed taker volume (buyer taker +) and arrival intensity, decayed."""

    def __init__(self, big_q: float = 0.5):
        self.big_q, self.t = big_q, None
        self.sv = [0.0, 0.0, 0.0]
        self.n = self.big = 0.0

    def update(self, t: float, q: float, m: float) -> None:
        sgn = -1.0 if m > 0 else 1.0
        if self.t is not None:
            dt = t - self.t
            self.sv = [v * math.exp(-dt / k) for v, k in zip(self.sv, TAUS)]
            d = math.exp(-dt / 0.2)
            self.n *= d
            self.big *= d
        self.sv = [v + sgn * q for v in self.sv]
        self.n += 1.0
        self.big += sgn * (q >= self.big_q)
        self.t = t

    def features(self, q: float, depth: float, f: dict, p: str = "st") -> None:
        if self.t is None:
            return
        dt = q - self.t
        for v, k in zip(self.sv, TAUS):
            f[f"{p}_sv{k:g}"] = v * math.exp(-dt / k) / depth
        f[f"{p}_tn"] = math.log1p(self.n * math.exp(-dt / 0.2) / 0.2)
        f[f"{p}_big"] = self.big * math.exp(-dt / 0.2)


class Settle:
    """Spot trade prices on the trade clock T (for K, sigma, the locked TWAP) and the last
    price on the receipt clock (for the level model)."""

    def __init__(self, keep: float = 700.0):
        self.T = Series(1, keep)          # (T, log px), arrival order
        self.last_lpx, self.last_t = NAN, None
        self.prev_lpx = NAN               # for "spot trade price changed" candidates
        self._sig: dict[int, float] = {}

    def update(self, t: float, T: float, px: float) -> None:
        lpx = math.log(px)
        self.prev_lpx, self.last_lpx, self.last_t = self.last_lpx, lpx, t
        self.T.add(T, lpx)
        if self._sig and T <= max(self._sig):   # a late trade inside a cached window
            self._sig.clear()

    def first_T(self) -> float:
        return self.T.t[self.T.lo] if len(self.T) else math.inf

    def _at_T(self, g: float) -> float:
        i = bisect_right(self.T.t, g, self.T.lo) - 1
        return self.T.cols[0][max(i, self.T.lo)]

    def twap(self, a: float, b: float) -> float:
        if not len(self.T) or self.first_T() > a + 5:
            return NAN
        pts = np.arange(a, b, 0.25)
        if not len(pts):
            return NAN
        return float(np.exp([self._at_T(g) for g in pts]).mean())

    def sigma(self, q: float) -> float:
        G = math.floor(q)
        s = self._sig.get(G)
        if s is None:
            lv = [self._at_T(g) for g in range(G - 300, G + 1)]
            r = np.diff(np.array(lv))
            var = (r * r).sum() / 300 - (r.sum() / 300) ** 2
            s = math.sqrt(max(var, SIG_FLOOR ** 2))
            if len(self._sig) > 8:
                self._sig.clear()
            self._sig[G] = s
        return s

    def zscale(self, q: float, end: float) -> float:
        tau = max(end - q, 3.0)
        eff = tau - 40 if tau >= 60 else tau / 3
        return 1.0 / (self.sigma(q) * math.sqrt(eff))


class LockedTwap:
    """Per-market cache of the last-minute TWAP points end - 60 + 0.25 k (trade clock)."""

    def __init__(self, end: float):
        self.end, self.pts = end, []   # exp(px) at settled grid points

    def value(self, st: Settle, q: float) -> float:
        a = self.end - 60
        pts = np.arange(a, q, 0.25)
        n = len(pts)
        if n == 0:
            return NAN
        settled = max(0, min(n, int((q - 2.0 - a) / 0.25)))   # points >= 2 s old are final
        while len(self.pts) < settled:
            self.pts.append(math.exp(st._at_T(pts[len(self.pts)])))
        vals = self.pts[:settled] + [math.exp(st._at_T(g)) for g in pts[settled:]]
        return float(np.mean(vals))


def p_model(st: Settle, q: float, start: float, end: float, K: float, lock: LockedTwap) -> float:
    """Level fair P(Up) from the TWAP rule with the last spot trade (Feeds.p_model)."""
    tau = max(end - q, 3.0)
    s = math.exp(st.last_lpx)
    w = min(max(tau / 60, 0.0), 1.0)
    zs = st.zscale(q, end)
    if tau < 60:
        locked = lock.value(st, q) if q > end - 60 else NAN
        exp_close = (1 - w) * (0.0 if math.isnan(locked) else locked) + w * s
        z = math.log(exp_close / K) * zs / w
    else:
        z = math.log(s / K) * zs
    return float(ndtr(z))
