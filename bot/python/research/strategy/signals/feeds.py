"""Binance series of one market on our receipt clock, and the settlement-aware scale.

Sources: 'spot' = last spot trade price, 'smid' = spot bookTicker mid, 'perp' = USD-M perp
bookTicker mid (run 2 only), 'smic' / 'pmic' = spot / perp top-of-book microprice
(bid * ask qty + ask * bid qty) / (bid qty + ask qty), which moves on queue sizes alone
(the leaders' real trigger, reports/hidden-trigger.md). `ret(src, at, a, b)` = move in bp
from at - b to at - a, using only what had been received by then. Settlement: Up wins if the 60 s TWAP at the end >= the
60 s TWAP at the start (K, proxied with Binance spot). `zscale(at)` = 1 / std of ln(close TWAP)
seen from `at`: sigma * sqrt(tau - 40) while tau >= 60 s, sigma * sqrt(tau / 3) after."""
from __future__ import annotations

import numpy as np
from scipy.special import ndtr


def _micro(bk: dict) -> np.ndarray:
    bq, aq = bk["bq"].astype(float), bk["aq"].astype(float)
    q = bq + aq
    mid = (bk["b"] + bk["a"]) / 2
    return np.where(q > 0, (bk["b"] * aq + bk["a"] * bq) / np.where(q > 0, q, 1), mid)


class Feeds:
    def __init__(self, m: dict):
        meta = m["meta"]
        self.start, self.end = float(meta["start"]), float(meta["end"])
        st, sb, fb = m["spot_tr"], m["spot_bk"], m["perp"]
        self.src = {"spot": (st["t"], np.log(st["px"])),
                    "smid": (sb["t"], np.log((sb["b"] + sb["a"]) / 2)),
                    "smic": (sb["t"], np.log(_micro(sb)))}
        if fb and len(fb.get("t", [])) > 100:
            self.src["perp"] = (fb["t"], np.log((fb["b"] + fb["a"]) / 2))
            self.src["pmic"] = (fb["t"], np.log(_micro(fb)))
            q = fb["bq"].astype(float) + fb["aq"]
            self.imb_t, self.imb = fb["t"], np.where(q > 0, (fb["bq"] - fb["aq"]) / q, 0.0)
        self.T, self.lpx = st["T"], np.log(st["px"])
        self.K = self._twap(self.start - 60, self.start)
        g = np.arange(self.start - 300, self.end + 1, 1.0)
        lv = self._at_T(g)
        r = np.diff(lv)
        win = 300
        c1, c2 = np.r_[0, np.cumsum(r)], np.r_[0, np.cumsum(r * r)]
        i = np.arange(len(r) + 1)
        j = np.clip(i - win, 0, None)
        n = np.maximum(i - j, 1)
        var = (c2[i] - c2[j]) / n - ((c1[i] - c1[j]) / n) ** 2
        self.sig_t, self.sig = g, np.sqrt(np.maximum(var, (0.03e-4) ** 2))  # floor 0.03 bp / s

    def _at_T(self, when):
        i = np.searchsorted(self.T, when, side="right") - 1
        return self.lpx[np.clip(i, 0, None)]

    def _twap(self, a: float, b: float) -> float:
        if not len(self.T) or self.T[0] > a + 5:
            return np.nan
        return float(np.exp(self._at_T(np.arange(a, b, 0.25))).mean())

    def has(self, src: str) -> bool:
        return src in self.src

    def level(self, src: str, at) -> np.ndarray:
        t, x = self.src[src]
        i = np.searchsorted(t, at, side="right") - 1
        return np.where(i >= 0, x[np.clip(i, 0, None)], np.nan)

    def ret(self, src: str, at, a: float, b: float) -> np.ndarray:
        at = np.asarray(at, dtype=float)
        return 1e4 * (self.level(src, at - a) - self.level(src, at - b))

    def imbalance(self, at) -> np.ndarray:
        if not hasattr(self, "imb"):
            return np.zeros(len(np.atleast_1d(at)))
        i = np.searchsorted(self.imb_t, at, side="right") - 1
        return np.where(i >= 0, self.imb[np.clip(i, 0, None)], 0.0)

    def sigma(self, at) -> np.ndarray:
        i = np.clip(np.searchsorted(self.sig_t, at, side="right") - 1, 0, len(self.sig) - 1)
        return self.sig[i]

    def zscale(self, at) -> np.ndarray:
        """d z / d ln S: how far one unit of log move shifts the settlement z-score."""
        tau = np.maximum(self.end - np.asarray(at, dtype=float), 3.0)
        eff = np.where(tau >= 60, tau - 40, tau / 3)
        return 1.0 / (self.sigma(at) * np.sqrt(eff))

    def p_model(self, at, src: str = "spot") -> np.ndarray:
        """Level fair P(Up) from the TWAP rule with Binance spot (biased level; used as a
        feature, never alone)."""
        at = np.asarray(at, dtype=float)
        tau = np.maximum(self.end - at, 3.0)
        s = np.exp(self.level(src, at))
        w = np.clip(tau / 60, 0, 1)
        locked = np.array([self._twap(self.end - 60, x) if x > self.end - 60 else np.nan for x in at])
        exp_close = np.where(tau < 60, (1 - w) * np.nan_to_num(locked, nan=0) + w * s, s)
        z = np.log(exp_close / self.K) * self.zscale(at) / np.where(tau < 60, w, 1)
        return ndtr(z)
