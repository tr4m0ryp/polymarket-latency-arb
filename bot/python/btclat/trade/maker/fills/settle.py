"""Settling our orders' fills (live runs): no matched order may go unseen.

The 2026-10-14 live hour lost $1.65 to a fill the bot never saw (order m34): the venue matched
it while our cancel was in flight, the cancel came back "can't be found - already canceled or
matched", and six GET /data/order lookups 40-370 ms after the ack all answered without the order
(the read side lags), which the bot read as 0 matched. Three sources now settle an order:

1. lookups after it left the book, at +1, +3, +10 s (fills/live.py `settle`), until one answers
   with the order in a final state (CANCELED, MATCHED, ...): its size_matched is final;
2. the venue's trade records, GET /data/trades of our wallet since the run started, every
   POLL_S while an order works or is unsettled (else every IDLE_S): each trade's maker legs
   carry our order ids and matched shares (fills/ledger.py). An order gone > DEADLINE_S before
   a poll was sent is settled by that poll's totals;
3. the user websocket channel (fills/userws.py), when connected: the same trade objects within
   milliseconds of the match, and the engine's own CANCELLATION / UPDATE of each order.
Every source feeds the manager the order's matched TOTAL (`on_matched`), so a fill seen by two
sources counts once. Until an order settles its unfilled notional counts as exposure.
At the end of the run `final()` applies one more trade read and logs a reconciliation line."""
from __future__ import annotations

from .ledger import Ledger, stamp

STEPS_S = (1.0, 3.0, 10.0)
POLL_S, IDLE_S, DEADLINE_S = 2.0, 30.0, 10.0
FINAL_TYPES = ("CANCELLATION",)


class Settle:
    def __init__(self, ops, manager, fills, now, note=None, t0: float | None = None):
        self.ops, self.mgr, self.fills, self.now = ops, manager, fills, now
        self.note = note or (lambda kind, **kw: None)
        self.t0 = now() if t0 is None else t0
        self.ledger = Ledger()
        self.known: dict[str, object] = {}
        self.due: dict[str, tuple] = {}            # cid -> (order, next step, time it left the book)
        self.next_poll, self.polling, self.last_err = 0.0, False, -1e18
        self.n = {"polls": 0, "poll_errors": 0, "trades": 0, "ws_trades": 0, "ws_orders": 0, "fills": 0,
                  "settled_early": 0, "settled_trades": 0, "settled_ws": 0, "foreign": 0}

    # watcher interface -----------------------------------------------------------------------
    def on_live(self, o) -> None:
        if o.oid:
            self.known[o.oid] = o

    def on_off(self, o) -> None:
        if not o.settled:
            self.due[o.cid] = (o, 0, self.now())

    def on_trade(self, tr: dict) -> None:
        pass

    def on_tick(self, now: float) -> None:
        for cid, (o, i, t_off) in list(self.due.items()):
            if o.settled:
                self.n["settled_early"] += 1
                del self.due[cid]
            elif now >= t_off + STEPS_S[i]:
                self.fills.request(o, "settle")
                if i + 1 < len(STEPS_S):
                    self.due[cid] = (o, i + 1, t_off)
                else:
                    del self.due[cid]              # the trade records settle it now
        if not self.polling and now >= self.next_poll:
            self.poll(now)

    # trade records ---------------------------------------------------------------------------
    def poll(self, now: float) -> None:
        self.polling, t_req = True, now
        self.n["polls"] += 1
        self.ops.trades(int(self.t0) - 60, lambda trs: self._polled(trs, t_req))

    def _polled(self, trs, t_req: float) -> None:
        self.polling = False
        busy = self.mgr.working() or self.mgr.unsettled()
        self.next_poll = self.now() + (POLL_S if busy else IDLE_S)
        if trs is None:
            self.n["poll_errors"] += 1
            if self.now() - self.last_err > 60:
                self.last_err = self.now()
                self.note("trades_poll_error", n=self.n["poll_errors"])
            return
        for tr in trs:
            self.apply(tr, "trades:rest")
        for o in self.mgr.unsettled():
            if o.t_off + DEADLINE_S <= t_req:
                o.settled = True
                self.n["settled_trades"] += 1

    def apply(self, tr: dict, src: str) -> None:
        n_foreign = len(self.ledger.foreign)
        for oid in self.ledger.add(tr, self.known.__contains__):
            o = self.known[oid]
            before = o.matched
            t = self.ledger.t_first.get(oid) or stamp(tr) or self.now()
            self.mgr.on_matched(o, {"fill_sh": self.ledger.total(oid)}, t, src)
            if o.matched > before + 1e-9:
                self.n["fills"] += 1
                self.note("fill_found", src=src, cid=o.cid, oid=oid, shares=o.matched - before,
                          trades=self.ledger.trades(oid), state=o.state)
        if len(self.ledger.foreign) > n_foreign:
            self.n["foreign"] = len(self.ledger.foreign)
            self.note("foreign_trade", src=src, trade=str(tr.get("id")), market=tr.get("market"),
                      asset=tr.get("asset_id"), side=tr.get("side"), size=tr.get("size"), price=tr.get("price"))

    # user websocket --------------------------------------------------------------------------
    def on_user(self, msg: dict) -> None:
        kind = str(msg.get("event_type") or "").lower()
        if kind == "trade":
            self.n["ws_trades"] += 1
            self.apply(msg, "trades:ws")
        elif kind == "order":
            self.n["ws_orders"] += 1
            o = self.known.get(msg.get("id"))
            if o is None:
                return
            if msg.get("size_matched") is not None:
                self.mgr.on_matched(o, {"fill_sh": msg["size_matched"]}, self.now(), "order:ws")
            if str(msg.get("type") or "").upper() in FINAL_TYPES and o.state == "done" and not o.settled:
                o.settled = True
                self.n["settled_ws"] += 1

    def final(self, trs, public: dict | None = None) -> dict:
        """End of run: apply one last trade read; the reconciliation of what we booked (and the
        public Data API's count of our wallet's trades, `public`, when it could be read)."""
        for tr in trs or []:
            self.apply(tr, "trades:final")
        miss = {o.cid: {"booked": o.matched, "trades": self.ledger.total(oid)} for oid, o in self.known.items()
                if abs(self.ledger.total(oid) - o.matched) > 1e-6}
        rec = {"orders": len(self.known), "matched_orders": sum(1 for x in self.ledger.by_oid.values() if x),
               "matched_sh": sum(self.ledger.total(k) for k in self.ledger.by_oid), "mismatch": miss,
               "foreign_trades": sorted(self.ledger.foreign), "unsettled": [o.cid for o in self.mgr.unsettled()],
               "booked_sh": sum(o.matched for o in self.known.values()), "public": public,
               "read_ok": trs is not None, **self.n}
        self.note("reconcile", **rec)
        return rec
