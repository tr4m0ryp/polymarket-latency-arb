"""The paper bot's engine with the maker rule in place of the arms: same feeds, state, features
and frozen model (btclat.paper, imported), same decision instants as the value arms
(`Decider._vt_candidate`: research/predict/feats/build.py `decision_times`, on which the
simulator evaluated `vmaker`), one row + two tree scores per instant, then the rule's quote
(rules.py: the frozen arm.quote, or the inside gate with its per-market hysteresis)."""
from __future__ import annotations

import time

from btclat.paper.arms.decide import Decider, MarketArms
from btclat.paper.engine.core import Engine
from btclat.paper.features.raw import row

from . import rules

NO_ARMS = ("-",)          # Decider filters its taker / micro arms by name: none match


class MakerDecider(Decider):
    def __init__(self, ctx, model, rule=None):
        super().__init__(ctx, model, NO_ARMS)
        self.rule = rule or rules.Frozen()
        self.n_quotes = 0
        self.us: list[float] = []

    def _state(self, m) -> MarketArms:
        st = self.state.get(m.meta["slug"])
        if st is None:
            if len(self.state) > 8:
                self.state = {k: v for k, v in self.state.items() if k in self._live}
            st = self.state[m.meta["slug"]] = MarketArms()
            self._live = {m.meta["slug"]}
        return st

    def decide(self, kind: str, flag: bool, t: float, m) -> dict | None:
        """The maker's quote at this event, or None when it is not a decision instant."""
        if not (m.start + 3 < t < m.end - 5 and self._vt_candidate(kind, flag, t, self._state(m))):
            return None
        t0 = time.perf_counter_ns()
        r = row(t, self.ctx, m)
        pu, pdn = self.model(r)
        q = self.rule.quote(r, pu, pdn, m.meta["slug"])
        q.update(t=t, pu=pu, pdn=pdn, fair=r["fair_p"], bb=r["pm_bb"], ba=r["pm_ba"], mid=r["pm_mid"],
                 secs_left=r["secs_left"], src=kind)
        self.n_quotes += 1
        self.us.append((time.perf_counter_ns() - t0) / 1e3)
        return q


class MakerEngine(Engine):
    """on_quote(m, q) per decision instant; on_book(m, t, ts) after every Up-book message."""

    def __init__(self, model, on_quote, on_book=None, now=None, rule=None):
        super().__init__(model, None, "maker", arms=NO_ARMS, now=now)
        self.decider = MakerDecider(self.world.ctx, model, rule)
        self.on_quote = on_quote
        self.on_book = on_book or (lambda m, t, ts: None)

    def on_event(self, ev: tuple) -> None:
        kind, m, flag = self.world.apply(ev)
        t = ev[1]
        if kind == "pm" and m is not None:
            self.on_book(m, t, ev[2])
            if not (m.start + 3 < round(t, 3) < m.end - 5):
                m = None
        elif kind in ("pb", "sb", "st"):
            m = self.world.active(t)
        else:
            m = None
        if m is not None and self.world.ctx.perp.t is not None and self.tradable(m, t):
            t0 = time.perf_counter_ns()
            q = self.decider.decide(kind, flag, t, m)
            self.compute_us.append((time.perf_counter_ns() - t0) / 1e3)
            if q is not None:
                self.on_quote(m, q)
        if t - self._last_drop > 30:
            self.world.drop_old(t)
            self._last_drop = t

    def stats(self, reset: bool = True) -> dict:
        d = self.decider
        out = {"n_events": self.world.n_ev, "quotes": d.n_quotes, "markets": len(self.world.mkts),
               **{f"decision_us_p{p}": _pct(d.us, p) for p in (50, 90, 99)}}
        if reset:
            d.us, self.compute_us = [], []
        return out


def _pct(x: list, p: int) -> float | None:
    if not x:
        return None
    s = sorted(x)
    return s[min(len(s) - 1, int(p / 100 * len(s)))]
