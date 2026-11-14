"""The maker run's streams (data/trade/<run>/, one JSON line each, first column the write time
in ns on the SNTP clock):

- quotes  every change of a slot's target tick: cause (rule, pull, band, tleft, stale, gap,
          stop, outside, hyst, ...), the decision row's pu / pdn / fair / book (+ rule, h for
          the inside rule);
- ops     insert, insert_ack, cancel, cancel_ack, lookup, skip, would_skip (dry: a money cap
          that would have skipped the quote live), with t_send_ns / t_ack_ns, ms;
- fills   one line per fill, written once its 10 s mark is in: our Up book mid at t + 10 s
          (capped at end + 2 s), and `pull_1s`: was the filled side's pull condition on at the
          fill or switched on within 1 s after it (the model saw us being run over);
- infer   live runs only: the simulator's inferred fills on the same orders (fills/infer.py)."""
from __future__ import annotations

import heapq
import itertools
import json
import math

MARK_S, PULL_S = 10.0, 1.0


def _num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return str(x)


class MakerLog:
    def __init__(self, sinks: dict, now_ns, book_of, note=None, dry: bool = False):
        self.sinks, self.now_ns, self.book_of = sinks, now_ns, book_of
        self.note = note or (lambda kind, **kw: None)
        self.dry = dry
        self.pulled = lambda slug, side, a, b: None
        self.jobs: list = []
        self.seq = itertools.count()
        self.n = {"quotes": 0, "ops": 0, "fills": 0, "infer": 0}

    def _w(self, stream: str, rec: dict) -> None:
        self.sinks[stream].write(self.now_ns(), json.dumps(rec, default=_num))
        self.n[stream] += 1

    def quote(self, s, tick: int, t: float, cause: str, q: dict | None) -> None:
        rec = {"t": t, "slug": s.slug, "side": s.side, "tick": tick, "prev": s.target, "cause": cause,
               "end": s.end, "working": s.order.brief() if s.order else None}
        if q:
            rec.update({k: q.get(k) for k in ("pu", "pdn", "fair", "bb", "ba", "mid", "secs_left", "src")})
            rec.update({k: q[k] for k in ("rule", "h") if k in q})          # inside rule only
        self._w("quotes", rec)

    def order(self, kind: str, o, **res) -> None:
        self._w("ops", {"kind": kind, "t": self.now_ns() / 1e9, **o.brief(), "t_dec": o.t_dec, **res})

    def fill(self, o, sh: float, t_fill: float, src: str) -> None:
        rec = {"t_fill": t_fill, "slug": o.slug, "side": o.side, "up": o.up, "token": o.token, "cid": o.cid,
               "oid": o.oid, "tick": o.tick, "px": o.price, "shares": sh, "cost": sh * o.price, "fee": 0.0,
               "src": src, "dry": self.dry, "end": o.end, "t_on": o.t_on, "t_dec": o.t_dec,
               "t_seen": self.now_ns() / 1e9, "quote": o.quote}
        x = min(t_fill + MARK_S, o.end + 2) if math.isfinite(t_fill) else self.now_ns() / 1e9
        heapq.heappush(self.jobs, (max(x, t_fill + PULL_S), next(self.seq), rec))

    def infer(self, o, sh: float, t_fill: float, how: str) -> None:
        self._w("infer", {"t_fill": t_fill, "slug": o.slug, "side": o.side, "cid": o.cid, "oid": o.oid,
                          "tick": o.tick, "px": o.price, "shares": sh, "how": how, "t_on": o.t_on})

    def advance(self, now: float) -> None:
        while self.jobs and self.jobs[0][0] <= now:
            _, _, rec = heapq.heappop(self.jobs)
            self._final(rec, True)

    def _final(self, rec: dict, final: bool) -> None:
        bk = self.book_of(rec["slug"])
        mid = bk.mid() if bk is not None else math.nan
        rec["mid10_up"] = mid if mid == mid else None
        rec["mk10"] = (mid if rec["up"] else 1 - mid) if mid == mid else None
        rec["pull_1s"] = self.pulled(rec["slug"], rec["side"], rec["t_fill"], rec["t_fill"] + PULL_S)
        rec["final"] = final
        self._w("fills", rec)

    def flush(self) -> None:
        """Shutdown: write every fill still waiting for its mark (final = False)."""
        while self.jobs:
            _, _, rec = heapq.heappop(self.jobs)
            self._final(rec, False)
