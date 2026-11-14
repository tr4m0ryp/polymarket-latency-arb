"""Paper execution: what each would-be order would have got, measured on the live venue book.

Per order (receipt clock t, assumed one-way latency L, hold 150 ms, race window J):
  t + L + hold + J + grace  fill on the venue rows (execution/venue.py, research taker sim)
  tf + 3 s, tf + 10 s       venue mid markouts (capped at end + 2 s, as the simulator's book)
  t + 35 s                  gap check (CLOB socket errors: 30 s before to 5 s after a
                            reconnect, research/strategy/ingest/markets.py gaps), then one
                            JSON line per order to the `orders` stream.
Nothing is sent anywhere: this module only reads the book the bot already holds."""
from __future__ import annotations

import heapq
import itertools
import json
import math

from . import venue

FINAL_S = 35.0


class PaperExec:
    def __init__(self, sink, run: str, L: float = 0.0, J: float = 0.010, hold: float = 0.150,
                 grace: float = 0.5):
        self.sink, self.run = sink, run
        self.L, self.J, self.hold, self.grace = L, J, hold, grace
        self.jobs: list = []
        self.seq = itertools.count()
        self.taken: dict[tuple, list] = {}
        self.n = {"orders": 0, "filled": 0, "skipped": 0, "written": 0}

    def _at(self, due: float, fn, *args) -> None:
        heapq.heappush(self.jobs, (due, next(self.seq), fn, args))

    def submit(self, o: dict, m, src: str, t_venue: float, lat_us: float) -> None:
        meta = m.meta
        rec = dict(o, run=self.run, slug=meta["slug"], start=m.start, end=m.end, src=src,
                   t_venue=t_venue, lat_us=lat_us, L=self.L, hold=self.hold, J=self.J,
                   token=meta["up"] if o["side"] > 0 else meta["down"],
                   seen_depth=m.book.depth_at_seen(o["side"]), tm=o["t"] + self.L + self.hold)
        self.n["orders"] += 1
        self._at(rec["tm"] + self.J + self.grace, self._fill, rec, m)
        self._at(o["t"] + FINAL_S, self._final, rec, m)

    def _fill(self, rec: dict, m) -> None:
        key = (rec["arm"], rec["slug"])
        taken = [x for x in self.taken.get(key, []) if x[0] > rec["t"] - venue.MEMORY]
        f, new, levels = venue.fill(m.book, m.start - 2, rec["t"], rec["side"], rec["shares"],
                                    rec["limit"], self.L, self.J, self.hold, taken)
        rec["levels"] = levels
        if f is None:
            rec.update(fill_sh=0.0, cost=0.0, fee=0.0, px=None)
        else:
            rec.update(fill_sh=f["shares"], cost=f["cost"], fee=f["fee"], px=f["px"])
            self.taken[key] = taken + new
            self.n["filled"] += 1
            tf = rec["tm"]
            for h in (3, 10):
                x = min(tf + h, m.end + 2)
                self._at(x + self.grace, self._mark, rec, m, h, x)

    def _mark(self, rec: dict, m, h: int, x: float) -> None:
        mid = venue.mid_at(m.book, m.start - 2, x)
        rec[f"mk{h}"] = (mid if rec["side"] > 0 else 1 - mid) if mid == mid else None

    def _final(self, rec: dict, m) -> None:
        lo, hi = rec["tm"], rec["tm"] + self.J
        gap = any(e - 30 <= hi and (r is None or lo <= r + 5) for e, r in getattr(m, "gaps", []))
        rec["gap"] = gap
        if gap:
            self.n["skipped"] += 1
        self.sink.write(int(rec["t"] * 1e9), json.dumps(rec, default=_num))
        self.n["written"] += 1

    def advance(self, now: float) -> None:
        while self.jobs and self.jobs[0][0] <= now:
            _, _, fn, args = heapq.heappop(self.jobs)
            fn(*args)

    def flush(self) -> None:
        """Run every pending job (end of a replay or shutdown)."""
        self.advance(math.inf)


def _num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return str(x)
