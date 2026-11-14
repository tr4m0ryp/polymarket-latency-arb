"""Append-only time series with as-of lookup and a bounded look-back: what the offline
`at(t, v, q)` (research/predict/feats/decay.py) reads, kept incrementally.

Values are stored in parallel lists; `asof(q)` = index of the last element with t <= q
(-1 if none). Elements older than `keep` seconds behind the newest are dropped, except the
one just before the cut-off, so a look-back of up to `keep` still resolves."""
from __future__ import annotations

from bisect import bisect_right


class Series:
    __slots__ = ("t", "cols", "lo", "keep")

    def __init__(self, n_cols: int, keep: float):
        self.t: list[float] = []
        self.cols: list[list[float]] = [[] for _ in range(n_cols)]
        self.lo, self.keep = 0, keep

    def add(self, t: float, *vals: float) -> None:
        self.t.append(t)
        for c, v in zip(self.cols, vals):
            c.append(v)
        if len(self.t) & 255 == 0:
            self._trim()

    def _trim(self) -> None:
        cut = self.t[-1] - self.keep
        i = bisect_right(self.t, cut, self.lo) - 1
        if i > self.lo:
            self.lo = i
        if self.lo > 4096 and self.lo * 2 > len(self.t):
            del self.t[:self.lo]
            for c in self.cols:
                del c[:self.lo]
            self.lo = 0

    def __len__(self) -> int:
        return len(self.t) - self.lo

    def asof(self, q: float) -> int:
        i = bisect_right(self.t, q, self.lo) - 1
        return i if i >= self.lo else -1

    def at(self, col: int, q: float, fill: float = float("nan")) -> float:
        i = self.asof(q)
        return self.cols[col][i] if i >= 0 else fill

    def last(self, col: int, fill: float = float("nan")) -> float:
        return self.cols[col][-1] if len(self.t) > self.lo else fill
