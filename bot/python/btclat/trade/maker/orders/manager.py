"""Quote targets -> resting post-only orders, at most one per side per market.

- A target change (rule decision, or a guard: < 30 s left, no decision for 1.5 s, CLOB socket
  gap, stop) acts at once: a live order at another tick (or target 0) is cancelled in the same
  call, on every connection (ops/). A replacement goes out only after the venue confirms the
  cancel, so two of our orders never rest on one side of one market.
- Every price change of the target is >= 1 tick (ticks are integers): each one re-quotes.
- Inserts: post-only GTD (or GTC), 5 shares, never crossing our book view; GTD expires at
  server now + 185 s (venue minimum 180 s): a dead bot's quotes die on their own. Caps in
  orders/risk.py (dry: money caps logged as would-skips, not applied).
- Rejects: post-only cross / rate limit back off and retry; region, auth, balance, size,
  tick, payload errors, an insert whose outcome is unknown, or 20 rejects in a row stop.
- A cancel the venue does not confirm is followed by an order lookup: filled or gone frees
  the slot, still resting (or not found: the lookup lags) retries; 3 failed tries stop (the
  session then sends cancel-all). A cancel answered "can't be found - already canceled or
  matched" frees the slot at once; the order stays unsettled (counted as exposure) until its
  fills are known (fills/settle.py)."""
from __future__ import annotations

import itertools

from .. import arm
from .lifecycle import Lifecycle
from .slot import Slot, Working

STALE_S = 1.5


class OrderManager(Lifecycle):
    def __init__(self, ops, risk, log, now, size: float = 5.0, otype: str = "GTD", tleft: float = arm.TLEFT):
        self.ops, self.risk, self.log, self.now = ops, risk, log, now
        self.size, self.otype, self.tleft = size, otype, tleft
        self.slots: dict[tuple, Slot] = {}
        self.orders: dict[str, Working] = {}
        self.watchers: list = []
        self.gaps: dict[str, list] = {}
        self.book_of = lambda slug: None        # our Up book of a market (run.py wires it)
        self.far = False                        # --far: insert at 0.01 (lifecycle.py FAR_PX)
        self.seq = itertools.count()
        self.stop_reason: str | None = None
        self.rejects = 0
        self.n = dict.fromkeys(("targets", "inserts", "live", "rejects", "skips", "cancels", "cancelled",
                                "cancel_unconfirmed", "cancel_gone", "fills", "filled_sh", "would_skips"), 0)

    # readings ------------------------------------------------------------------------------
    def working(self) -> list[Working]:
        return [o for o in self.orders.values() if o.state != "done"]

    def resting(self) -> float:
        return sum(o.resting for o in self.working())

    def exposed(self) -> list[Working]:
        """Orders whose unfilled notional still counts: working, or gone but not settled."""
        return [o for o in self.orders.values() if o.at_risk > 0]

    def unsettled(self) -> list[Working]:
        return [o for o in self.orders.values() if o.state == "done" and not o.settled]

    def pulled(self, slug: str, side: str, a: float, b: float) -> bool | None:
        s = self.slots.get((slug, side))
        return None if s is None else s.pulled_within(a, b)

    # decisions -----------------------------------------------------------------------------
    def on_quote(self, m, q: dict) -> None:
        tick_ok = abs(float(m.meta.get("tick", 0.01)) - 0.01) < 1e-9
        for side in arm.SIDES:
            s = self._slot(m.meta, side)
            s.last_dec = q["t"]
            s.note_pull(q["t"], q[f"pull_{side}"])
            tgt = q[side] if tick_ok else 0
            self.set_target(s, tgt, q["t"], arm.cause(q, side) if tick_ok else "tick", q)

    def _slot(self, meta: dict, side: str) -> Slot:
        key = (meta["slug"], side)
        if key not in self.slots:
            self.slots[key] = Slot.of(meta, side)
        return self.slots[key]

    def set_target(self, s: Slot, tick: int, t: float, cause: str, q: dict | None = None) -> None:
        if tick == s.target:
            return
        self.log.quote(s, tick, t, cause, q)
        s.target, s.t_target, s.cause, s.skip = tick, t, cause, None
        s.ctx = q or {}
        self.n["targets"] += 1
        self.sync(s)

    def sync(self, s: Slot) -> None:
        o = s.order
        if o is None:
            if s.target > 0 and self.stop_reason is None and self.now() >= s.backoff:
                self._insert(s)
        elif o.state == "live" and o.tick != s.target:
            self._cancel(o)

    def on_tick(self, now: float) -> None:
        for key, s in list(self.slots.items()):
            if s.target:
                why = ("tleft" if s.end - now < self.tleft else "stale" if now - s.last_dec > STALE_S
                       else "gap" if self._gap(s.slug) else None)
                if why:
                    self.set_target(s, 0, now, why)
            o = s.order
            if o is None and s.target:
                self.sync(s)
            elif o is not None and o.state == "live" and o.expiration and self.ops.server_now() > o.expiration + 1:
                self._cancel(o)                   # expired at the venue: confirm through the cancel path
            if s.order is None and now > s.end + 120:
                del self.slots[key]
        for cid in [c for c, o in self.orders.items() if o.state == "done" and now > o.end + 120]:
            del self.orders[cid]

    def _gap(self, slug: str) -> bool:
        g = self.gaps.get(slug)
        return bool(g) and g[-1][1] is None

    def stop(self, reason: str) -> None:
        if self.stop_reason is None:
            self.stop_reason = reason
            self.log.note("maker_stop", reason=reason)
        now = self.now()
        for s in list(self.slots.values()):
            self.set_target(s, 0, now, "stop")
