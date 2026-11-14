"""Incremental feature state for one Binance bookTicker stream, updated per message in pure
Python: what a live bot keeps instead of recomputing windows. Covers the costly kinds
(decayed OFI at 4 scales, depletion, intensities, microprice history ring) and is timed per
message on recorded perp updates."""
from __future__ import annotations

import math
import time
from collections import deque

import numpy as np

TAUS = (0.025, 0.1, 0.4, 1.6)


class StreamState:
    def __init__(self):
        self.t = None
        self.b = self.a = self.bq = self.aq = None
        self.ofi = [0.0] * len(TAUS)
        self.depb = self.depa = self.lam = 0.0
        self.hist = deque()  # (t, log microprice) for the last second

    def update(self, t, b, a, bq, aq):
        if self.t is not None:
            dt = t - self.t
            for k, tau in enumerate(TAUS):
                self.ofi[k] *= math.exp(-dt / tau)
            d = math.exp(-dt / 0.1)
            self.depb *= d
            self.depa *= d
            self.lam *= d
            e = ((b >= self.b) * bq - (b <= self.b) * self.bq - (a <= self.a) * aq + (a >= self.a) * self.aq)
            for k in range(len(TAUS)):
                self.ofi[k] += e
            self.depb += max(self.bq - bq, 0.0) if b == self.b else (self.bq if b < self.b else 0.0)
            self.depa += max(self.aq - aq, 0.0) if a == self.a else (self.aq if a > self.a else 0.0)
        self.lam += 1.0
        q = bq + aq
        mic = math.log((b * aq + a * bq) / q) if q > 0 else math.log((a + b) / 2)
        self.hist.append((t, mic))
        while self.hist and self.hist[0][0] < t - 1.0:
            self.hist.popleft()
        self.t, self.b, self.a, self.bq, self.aq = t, b, a, bq, aq
        return mic


def bench_state(n: int = 200_000) -> dict:
    from ...strategy import CACHE as SC
    with np.load(next(SC.glob("hour-49767*.npz"))) as z:
        rows = list(zip(z["fb_t"][:n].tolist(), z["fb_b"][:n].tolist(), z["fb_a"][:n].tolist(),
                        z["fb_bq"][:n].astype(float).tolist(), z["fb_aq"][:n].astype(float).tolist()))
    s = StreamState()
    t0 = time.perf_counter_ns()
    for r in rows:
        s.update(*r)
    return {"py_state_update_per_msg_us": (time.perf_counter_ns() - t0) / len(rows) / 1e3,
            "msgs_timed": len(rows)}
