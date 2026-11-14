"""Our real fills (live runs): GET /data/order `size_matched` of each resting quote, looked up

- when a tape trade prints at or through its price on the side that would hit it (the first
  such trade's venue stamp since the last lookup is the fill time of new shares matched);
- every `every` s while it rests (fallback);
- once after it is gone (cancel confirmed or expired), for shares matched before the cancel,
  and again at +1 / +3 / +10 s while it is unsettled (fills/settle.py asks: `settle`).
One lookup per order in flight; a request while one runs is queued once. The increase over
what we knew goes to the manager (`on_matched`): risk book, fills stream. A lookup that finds
the order gone in a final state (not LIVE / DELAYED) settles it; one that does not find the
order at all is `unknown` (the venue's read side lags) and settles nothing."""
from __future__ import annotations

from ..orders.lifecycle import RESTING


class LiveFills:
    def __init__(self, ops, manager, now, log=None, every: float = 3.0):
        self.ops, self.mgr, self.now, self.every = ops, manager, now, every
        self.log = log
        self.inflight: set[str] = set()
        self.again: dict[str, str] = {}
        self.last: dict[str, float] = {}
        self.hint: dict[str, list] = {}         # venue stamps of trades at / through the quote
        self.sent_hints: dict[str, int] = {}
        self.n = {"lookups": 0, "trade": 0, "poll": 0, "final": 0, "unknown": 0}

    def on_live(self, o) -> None:
        self.last[o.cid] = self.now()

    def on_off(self, o) -> None:
        self.request(o, "final")

    def on_trade(self, tr: dict) -> None:
        for o in self.mgr.working():
            if o.slug != tr["slug"] or o.state not in ("live", "cancelling"):
                continue
            s = 1 if o.side == "bid" else -1
            px = o.tick / 100
            if tr["d"] == -s and (tr["p"] <= px + 1e-9 if s > 0 else tr["p"] >= px - 1e-9):
                self.hint.setdefault(o.cid, []).append(tr["ts"])
                self.request(o, "trade")

    def on_tick(self, now: float) -> None:
        for o in self.mgr.working():
            if o.state == "live" and now - self.last.get(o.cid, now) >= self.every:
                self.request(o, "poll")

    def request(self, o, why: str) -> None:
        if o.oid is None:
            return
        if o.cid in self.inflight:
            self.again[o.cid] = "final" if why == "final" else self.again.get(o.cid, why)
            return
        self.inflight.add(o.cid)
        self.sent_hints[o.cid] = len(self.hint.get(o.cid, ()))
        self.last[o.cid] = self.now()
        self.n["lookups"] += 1
        self.n[why] = self.n.get(why, 0) + 1
        self.ops.lookup(o, lambda q: self._got(o, q, why))

    def _got(self, o, q: dict, why: str) -> None:
        self.inflight.discard(o.cid)
        if self.log is not None:
            self.log.order("lookup", o, why=why, **q)
        if q.get("unknown"):
            self.n["unknown"] += 1
        hints = self.hint.get(o.cid, [])
        seen, rest = hints[:self.sent_hints.pop(o.cid, 0)], hints
        t_fill = (seen or rest or [q.get("t_ack", self.now())])[0]
        self.mgr.on_matched(o, q, t_fill, f"lookup:{why}")
        if o.state == "done" and not q.get("unknown") and str(q.get("status") or "").lower() not in RESTING:
            o.settled = True
        if seen:                                 # trades before this lookup are now accounted for
            self.hint[o.cid] = hints[len(seen):]
        nxt = self.again.pop(o.cid, None)
        if nxt is not None:
            self.request(o, nxt)
        elif o.state == "done" and why in ("final", "settle") and o.settled:
            self.last.pop(o.cid, None)
            self.hint.pop(o.cid, None)
