"""The paper bot's event loop body, identical for live feeds and replays: update state,
let the arms decide, hand would-be orders to the paper executor, run due paper jobs.

Latency per decision is the receipt-to-decision time: `now() - t` after the arms ran
(live: SNTP-corrected wall clock, so it includes event-loop queueing; replay: compute only)."""
from __future__ import annotations

import math
import time

import numpy as np

from ..arms.decide import Decider
from ..execution.paper import PaperExec
from .world import World

VENUE_IDX = {"pb": 2, "st": 2, "pm": 2}


class Engine:
    def __init__(self, model, sink, run: str, L: float = 0.0, arms=None, now=None):
        self.world = World()
        self.decider = Decider(self.world.ctx, model, arms)
        self.paper = PaperExec(sink, run, L=L)
        self.now = now
        self.lat_us: list[float] = []
        self.compute_us: list[float] = []
        self.n_dec = 0
        self._last_drop = 0.0

    def tradable(self, m, t: float) -> bool:
        """Settlement inputs present (decided once, after the start): K from the 60 s before
        the start and 300 s of spot trades for sigma."""
        ok = getattr(m, "ok", None)
        if ok is None:
            if t < m.start + 1:
                return False
            st = self.world.ctx.settle
            ok = m.ok = st.first_T() <= m.start - 300 and m.strike(st) == m.strike(st)
        return ok

    def on_event(self, ev: tuple) -> None:
        kind, m, flag = self.world.apply(ev)
        t = ev[1]
        if kind in ("pb", "sb", "st"):
            m = self.world.active(t)
        elif kind == "pm" and m is not None and not (m.start + 3 < round(t, 3) < m.end - 5):
            m = None
        if m is not None and self.world.ctx.perp.t is not None and self.tradable(m, t):
            t0 = time.perf_counter_ns()
            orders = self.decider.on_event(kind, flag, t, m)
            self.compute_us.append((time.perf_counter_ns() - t0) / 1e3)
            if orders:
                lat = (self.now() - t) * 1e6 if self.now else self.compute_us[-1]
                i = VENUE_IDX.get(kind)
                tv = ev[i] if i is not None else math.nan
                for o in orders:
                    self.paper.submit(o, m, kind, tv, lat)
                    self.lat_us.append(lat)
                self.n_dec += len(orders)
        self.paper.advance(t if self.now is None else self.now())
        if t - self._last_drop > 30:
            self.world.drop_old(t)
            self._last_drop = t

    def stats(self, reset: bool = True) -> dict:
        def pct(x):
            return {f"p{p}": float(np.percentile(x, p)) for p in (50, 90, 99)} if x else {}
        d = self.decider
        out = {"n_events": self.world.n_ev, "vt_candidates": d.n_vt, "micro_candidates": d.n_micro,
               "orders": self.n_dec, "event_us": pct(self.compute_us), "value_decision_us": pct(d.vt_us),
               "order_lat_us": pct(self.lat_us), **self.paper.n}
        if reset:
            self.compute_us, self.lat_us, d.vt_us = [], [], []
        return out
