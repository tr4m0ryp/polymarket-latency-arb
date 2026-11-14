"""The life of one working order: insert (non-crossing check, risk check, GTD expiry), its ack,
cancel, its ack or the lookup after an unconfirmed cancel, fills (lookup deltas live, inferred
fills dry), done. Mixed into OrderManager (manager.py), which owns the slots and the decisions.

A cancel the venue answers with "order can't be found - already canceled or matched" means the
order left the book on its own: matched (the 2026-10-14 $1.65 fill, m34) or expired. The slot
is freed, the order stays unsettled (its notional still counts as exposure) until fills/settle.py
knows its matched size from a definitive lookup or the venue's trade records.

GTD expiry: the venue rejects an expiration under server now + 180 s (live hold test,
2026-10-14), so a quote expires at now + 185 s: a dead man's switch for a dead bot, never the
way quotes end (cancels and the < 30 s guard do that). A quote that would cross our book view
is not sent (a crossing order is held ~170 ms as a taker); post-only stays the venue backstop."""
from __future__ import annotations

import math

from ..ops.dry import crosses
from .slot import Slot, Working

FATAL = ("geoblock", "closed_only", "banned", "auth", "forbidden", "balance", "min_size", "tick", "payload")
RETRY_S = {"post_only_crosses": 0.2, "crosses_book": 0.2, "rate_limited": 2.0}
MAX_REJECTS, MAX_CANCEL_TRIES = 20, 3
GTD_MIN_S, GTD_PAD_S = 180, 5            # venue minimum (s ahead of its clock) + margin for clock error
FAR_PX = 0.01                            # --far: every insert at the lowest tick (latency test, no fill risk)
RESTING = ("live", "delayed")


class Lifecycle:
    # inserts -------------------------------------------------------------------------------
    def _insert(self, s: Slot) -> None:
        now = self.now()
        o = Working(f"m{next(self.seq)}", s.slug, s.side, s.token, s.up, s.target, s.price(s.target), self.size,
                    s.end, self.otype, t_dec=now, quote={k: s.ctx.get(k) for k in ("t", "pu", "pdn", "fair", "bb", "ba")})
        if self.far:                          # same decisions, same timing; the order itself cannot fill
            o.price = FAR_PX
        exp = self._expiry() if self.otype == "GTD" else 0
        if crosses(self.book_of(s.slug), s.side, s.target):
            why, would = "would_cross", None
        else:
            why, would = self.risk.gate(o, self.exposed(), now)
        if why:
            if s.skip != why:
                s.skip = why
                self.n["skips"] += 1
                self.log.order("skip", o, reason=why)
            return
        if would:                                 # dry only: a money cap would have skipped it live
            self.n["would_skips"] += 1
            self.log.order("would_skip", o, reason=would)
        o.expiration = exp
        s.order, self.orders[o.cid] = o, o
        self.risk.sent(now)
        self.n["inserts"] += 1
        self.log.order("insert", o)
        self.ops.insert(o, lambda res: self._insert_ack(o, res))

    def _expiry(self) -> int:
        return int(self.ops.server_now()) + GTD_MIN_S + GTD_PAD_S

    def _insert_ack(self, o: Working, res: dict) -> None:
        self.log.order("insert_ack", o, **res)
        s = self.slots.get((o.slug, o.side))
        if res.get("ok"):
            self.rejects = 0
            o.oid, o.state, o.t_on = res.get("order_id"), "live", res.get("t_venue", self.now())
            self.n["live"] += 1
            for w in self.watchers:
                w.on_live(o)
            if res.get("fill_sh", 0.0) > 0:          # impossible for post-only: account for it and stop
                self.fill(o, float(res["fill_sh"]), self.now(), "insert_ack")
                self.stop(f"post-only order {o.oid} matched on insert")
            if s is not None and o.state == "live":
                self.sync(s)
            return
        if res.get("unknown") or "exc" in res:
            self.stop(f"insert outcome unknown ({res.get('err_kind') or res.get('exc')}): {res.get('err')}")
            return
        o.state, o.settled = "done", True
        if s is not None and s.order is o:
            s.order = None
        self.rejects += 1
        self.n["rejects"] += 1
        kind = res.get("err_kind")
        if kind in FATAL or self.rejects >= MAX_REJECTS:
            self.stop(f"insert rejected ({self.rejects} in a row): {kind}: {res.get('err')}")
        elif s is not None:
            s.backoff = self.now() + RETRY_S.get(kind, 1.0)

    # cancels -------------------------------------------------------------------------------
    def _cancel(self, o: Working) -> None:
        o.state, o.t_cancel = "cancelling", self.now()
        o.cancel_tries += 1
        self.n["cancels"] += 1
        self.log.order("cancel", o)
        self.ops.cancel(o, lambda res: self._cancel_ack(o, res))

    def _cancel_ack(self, o: Working, res: dict) -> None:
        self.log.order("cancel_ack", o, **res)
        if o.state == "done":
            return
        if res.get("confirmed"):
            self.n["cancelled"] += 1
            o.t_off = res.get("t_venue", self.now())
            self._done(o)
            return
        if res.get("gone"):                       # not on the book any more: matched or expired
            self.n["cancel_gone"] += 1
            o.t_off = res.get("t_venue", self.now())
            self._done(o)
            return
        self.n["cancel_unconfirmed"] += 1
        self.ops.lookup(o, lambda q: self._after_unconfirmed(o, q))

    def _after_unconfirmed(self, o: Working, q: dict) -> None:
        self.log.order("lookup", o, why="cancel_unconfirmed", **q)
        self.on_matched(o, q, q.get("t_ack", self.now()), "lookup:cancel")
        if o.state == "done":
            return
        if q.get("unknown") or str(q.get("status") or "").lower() in RESTING:
            if o.cancel_tries >= MAX_CANCEL_TRIES:
                self.stop(f"cancel of {o.oid} not confirmed after {o.cancel_tries} tries")
                return
            self._cancel(o)
            return
        o.t_off = self.now()
        self._done(o)

    def _done(self, o: Working) -> None:
        o.state = "done"
        if not getattr(self.ops, "settles_late", False) or o.matched >= o.size - 1e-9:
            o.settled = True                      # dry ops know every fill at once
        for w in self.watchers:
            w.on_off(o)
        s = self.slots.get((o.slug, o.side))
        if s is not None and s.order is o:
            s.order = None
            self.sync(s)

    # fills ---------------------------------------------------------------------------------
    def on_matched(self, o: Working, q: dict, t_fill: float, src: str) -> None:
        """A lookup's size_matched (total): record the increase as a fill."""
        if q.get("unknown"):
            return
        self.fill(o, float(q.get("fill_sh") or 0.0) - o.matched, t_fill, src)

    def fill(self, o: Working, sh: float, t_fill: float, src: str) -> None:
        sh = min(sh, o.size - o.matched)
        if not sh > 1e-9:
            return
        o.matched += sh
        self.risk.fill(o, sh, sh * o.price)
        self.n["fills"] += 1
        self.n["filled_sh"] += sh
        self.log.fill(o, sh, t_fill, src)
        if o.matched >= o.size - 1e-9:
            o.settled = True                      # nothing left that could fill
        if o.matched >= o.size - 1e-9 and o.state != "done":
            o.t_off = t_fill if math.isfinite(t_fill) else self.now()
            self._done(o)
