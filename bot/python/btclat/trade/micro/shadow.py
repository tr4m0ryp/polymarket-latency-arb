"""The paper executor in shadow: every signal the arms emit gets the paper bot's prediction
(btclat/paper/execution/paper.py, unchanged: venue-book fill at t + L + 150 ms, 3 s / 10 s
markouts, gap flag) for the SAME order the live leg sends (5 shares, same limit), tagged with
a signal id, and is handed to the live executor at once. The finished paper record (t + 35 s)
goes to the `paper` stream and back to the live executor to be joined with the live result."""
from __future__ import annotations

import itertools

from btclat.paper.execution.paper import PaperExec


class ShadowExec(PaperExec):
    def __init__(self, sink, run: str, on_signal, on_final, shares: float, L: float = 0.0):
        super().__init__(sink, run, L=L)
        self.on_signal, self.on_final, self.shares = on_signal, on_final, shares
        self.sigs = itertools.count()

    def submit(self, o: dict, m, src: str, t_venue: float, lat_us: float) -> None:
        o = dict(o, sig=f"{self.run}:{next(self.sigs)}", arm_shares=o["shares"], shares=self.shares)
        super().submit(o, m, src, t_venue, lat_us)
        self.on_signal(o, m, src, t_venue, lat_us)

    def _final(self, rec: dict, m) -> None:
        super()._final(rec, m)
        self.on_final(rec)
