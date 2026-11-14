"""Polymarket Up-token book of one 5m market, as received (our view), with the history
the decision features and the paper fills read.

- Our view: best bid / ask tick (0 / 100 when a side is empty), the receipt time of the last
  top change, and the mid history (for the book's own repricing, bk0..bk2).
- Venue view: every level change is logged with its venue stamp ts (`log`: ts, col, old,
  new; col 0..99 = bid ticks, 100..199 = ask ticks as in research/strategy/sim/grid.py) so
  the paper executor can roll the book back to any venue time of the last few seconds."""
from __future__ import annotations

from collections import deque

from .series import Series

NAN = float("nan")


class PMBook:
    def __init__(self, keep_log: float = 20.0):
        self.size = [0.0] * 200
        self.bb, self.ba = 0, 100
        self.top_t = None                 # receipt time of the last top change
        self.mids = Series(1, 10.0)       # (t, mid or nan) at each top change
        self.log: deque = deque()         # (ts, col, old, new), arrival order
        self.keep_log = keep_log
        self.delay = 0.016                # receipt - venue lag, for messages without ts
        self.n_msgs = 0

    def apply(self, t: float, ts: float, snap: bool, chg: list) -> bool:
        """Apply one message; True if our view's top changed. A (0, 0, 0) entry in chg
        starts a full book (only the merged replay groups use it; see replay/source.py)."""
        if ts != ts:  # NaN: stamp it like the research Book does (median lag)
            ts = t - self.delay
        else:
            self.delay += 0.01 * ((t - ts) - self.delay)
        sz, log = self.size, self.log
        if snap:
            chg = [(0, 0, 0.0)] + list(chg)
        new = None
        for side, k, s in chg:
            if side == 0:              # full book follows: diff against it when it ends
                new = [0.0] * 200
                continue
            c = k if side > 0 else 100 + k
            if new is not None:
                new[c] = s
            elif sz[c] != s:
                log.append((ts, c, sz[c], s))
                sz[c] = s
        if new is not None:
            for c in range(1, 200):
                if sz[c] != new[c]:
                    log.append((ts, c, sz[c], new[c]))
                    sz[c] = new[c]
        while log and log[0][0] < ts - self.keep_log:
            log.popleft()
        self.n_msgs += 1
        bb, ba = _top(sz)
        if (bb, ba) != (self.bb, self.ba) or self.top_t is None:
            changed = self.top_t is not None
            self.bb, self.ba, self.top_t = bb, ba, t
            self.mids.add(t, self.mid())
            return changed
        return False

    def mid(self) -> float:
        return (self.bb + self.ba) / 200 if self.bb > 0 and self.ba < 100 else NAN

    def mid_at(self, q: float) -> float:
        return self.mids.at(0, q)

    def depth_at_seen(self, side: int) -> float:
        return self.size[100 + self.ba] if side > 0 else self.size[self.bb]


def _top(sz: list) -> tuple[int, int]:
    bb = next((k for k in range(99, 0, -1) if sz[k] > 0), 0)
    ba = next((k for k in range(1, 100) if sz[100 + k] > 0), 100)
    return bb, ba


def top_of(sz) -> tuple[int, int]:
    return _top(sz)
