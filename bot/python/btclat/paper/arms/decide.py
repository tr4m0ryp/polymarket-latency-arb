"""Per-event decisions of the four arms, with the simulator's candidate sets.

Value arms (research/predict/sim/rules.py `vtaker`) decide on the predict table's instants
(research/predict/feats/build.py `decision_times`): every perp / spot bookTicker update and
every change of our view of the Up top, thinned to one per 20 ms unless the perp or spot
mid moved, the top changed, or the perp microprice moved >= 0.002 bp since the last kept one.
Micro arms (research/strategy/signals/rules.py `micro`) decide on the strategy v2 table's
instants (signals/features.py `candidates`, micro=True): changes of the spot trade price,
spot mid, perp mid, Up top, and perp / spot microprice moves >= 0.001 bp over 0.1 s.
The simulator evaluates at ms-rounded times; live evaluates at the event itself.
Refractory per arm and market = the rules' `_refractory` over the passing rows."""
from __future__ import annotations

import math
import time

import numpy as np

from research.predict.sim import rules as vrules
from research.strategy.signals import rules as srules

from .defs import MICRO_ARMS, VT_ARMS, refr
from .frame import Frame
from ..features.raw import micro_view, row


VT_COLS = ("t", "pm_ba", "pm_bb", "pm_mid", "secs_left", "p_dmic0.1", "s_dmic0.1", "fair_p")


class MarketArms:
    """Per-market decision state (offline tables are per market)."""

    def __init__(self):
        self.vt_last_t, self.vt_last_m, self.vt_prev_q = -math.inf, math.nan, None
        self.fired = {a["name"]: -math.inf for a in VT_ARMS + MICRO_ARMS}


class Decider:
    def __init__(self, ctx, model, arms=None):
        self.ctx, self.model = ctx, model
        names = set(arms) if arms else None
        self.vt = [a for a in VT_ARMS if names is None or a["name"] in names]
        self.micro = [a for a in MICRO_ARMS if names is None or a["name"] in names]
        self.state: dict[str, MarketArms] = {}
        self._live: set = set()
        self.n_vt = self.n_micro = 0
        self.vt_us: list[float] = []      # per value decision: features + 2 tree scores + rules

    def _vt_candidate(self, kind: str, flag: bool, t: float, st: MarketArms) -> bool:
        if kind not in ("pb", "sb", "pm") or (kind == "pm" and not flag):
            return False
        mic = self.ctx.perp.lmic(t) * 1e4
        keep = flag or kind == "pm" or t - st.vt_last_t >= 0.02 or abs(mic - st.vt_last_m) >= 0.002
        if keep:
            st.vt_last_t, st.vt_last_m = t, mic
            if st.vt_prev_q == t:   # offline np.unique: one row per instant
                return False
            st.vt_prev_q = t
        return keep

    def _micro_candidate(self, kind: str, flag: bool, t: float) -> bool:
        if flag:
            return kind in ("pb", "sb", "st", "pm")
        c = self.ctx
        if kind == "pb":
            return abs(1e4 * (c.perp.lmic(t) - c.perp.lmic(t - 0.1))) >= 0.001
        if kind == "sb":
            return abs(1e4 * (c.spot.lmic(t) - c.spot.lmic(t - 0.1))) >= 0.001
        return False

    def on_event(self, kind: str, flag: bool, t: float, m) -> list[dict]:
        """Orders the arms would send for this event of market m's decision window."""
        st = self.state.get(m.meta["slug"])
        if st is None:
            if len(self.state) > 8:
                self.state = {k: v for k, v in self.state.items() if k in self._live}
            st = self.state[m.meta["slug"]] = MarketArms()
            self._live = {m.meta["slug"]}
        out = []
        if self.vt and m.start + 3 < t < m.end - 5 and self._vt_candidate(kind, flag, t, st):
            self.n_vt += 1
            out += self._value(t, m, st)
        tr = round(t, 3)
        if self.micro and m.start + 3 < tr < m.end - 5 and self._micro_candidate(kind, flag, t):
            self.n_micro += 1
            out += self._micro(t, m, st)
        return out

    def _value(self, t, m, st) -> list[dict]:
        t0 = time.perf_counter_ns()
        r = row(t, self.ctx, m)
        pu, pdn = self.model(r)
        fr = Frame({k: r[k] for k in VT_COLS})
        out = []
        for a in self.vt:
            if not max(pu, pdn) >= a["params"]["margin"]:   # necessary for vtaker: skip the call
                continue
            d = vrules.vtaker(fr, np.array([pu]), np.array([pdn]), **a["params"])
            if len(d["t"]) and t - st.fired[a["name"]] >= refr(a):
                st.fired[a["name"]] = t
                out.append(_order(a["name"], t, d, r, pu, pdn))
        us = (time.perf_counter_ns() - t0) / 1e3
        self.vt_us.append(us)
        for o in out:
            o["compute_us"] = us
        return out

    def _micro(self, t, m, st) -> list[dict]:
        c = self.ctx
        pm = 1e4 * (c.perp.lmic(t) - c.perp.lmic(t - 0.1))
        if not abs(pm) >= min(a["params"]["thr"] for a in self.micro):   # necessary for micro
            return []
        t0 = time.perf_counter_ns()
        v = micro_view(t, self.ctx, m, with_fair=True)
        fr = Frame({k: v[k] for k in ("t", "secs_left", "bb", "ba", "mid", "pmic_r0.1", "smic_r0.1")})
        out = []
        for a in self.micro:
            p = dict(a["params"])
            fair = np.array([v["p_fair"]]) if p.pop("model", None) else None
            d = srules.micro(fr, p_fair=fair, **p)
            if len(d["t"]) and t - st.fired[a["name"]] >= refr(a):
                st.fired[a["name"]] = t
                r = row(t, self.ctx, m)            # logged model value of the micro fire
                pu, pdn = self.model(r)
                out.append(_order(a["name"], t, d, r, pu, pdn, p_fair=v["p_fair"]))
        us = (time.perf_counter_ns() - t0) / 1e3
        for o in out:
            o["compute_us"] = us
        return out


def _order(arm, t, d, r, pu, pdn, p_fair=None) -> dict:
    side = int(d["side"][0])
    seen = r["pm_ba"] / 100 if side > 0 else 1 - r["pm_bb"] / 100
    return {"arm": arm, "t": t, "side": side, "shares": float(d["shares"][0]),
            "limit": float(d["limit"][0]), "edge": float(d["edge"][0]), "seen": seen,
            "pred_up": pu, "pred_dn": pdn, "value": pu if side > 0 else pdn,
            "fair_p": r["fair_p"] if p_fair is None else p_fair, "pm_bb": r["pm_bb"], "pm_ba": r["pm_ba"]}
