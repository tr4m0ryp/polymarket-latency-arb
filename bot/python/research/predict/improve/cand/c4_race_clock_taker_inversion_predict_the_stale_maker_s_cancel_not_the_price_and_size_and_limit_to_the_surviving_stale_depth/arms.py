"""C4 arms: the frozen firing rules (v1, 3 c taker / 2 c trigger veto) with a race-keyed limit
and size. Firing, refractory and gates are research/predict/sim/rules.vtaker unchanged; only
`limit` and `shares` of each fired order change.

  frz         60 sh, seen + 2 c (control: must equal the frozen arm exactly)
  vlim_tight  60 sh, seen + clip(v* - 2 c, 0, 2 c)                (value-tied limit, no race model)
  rc_lim      60 sh, seen + 1 c if P_alive < 0.3 and edge < 5 c, else seen + 2 c
  rc_size     clip(min(2000 v*, P_alive q_seen + q_next), 30, 200) sh, limit as rc_lim
  ek          clip(2000 v*, 30, 200) sh, seen + 2 c   (C1's ek_vstar_2000, same fill model)
round 2 (after the r1 diagnosis, diag.py on train markets):
  rc_boost    clip(max(2000 v*, P_alive q_seen + q_next), 30, hi) sh, seen + 2 c
  rc_walk     ek size; seen + 2 c if P_alive >= p_thr, else seen + clip(v* - floor, 2 c, wmax)
  vlw_ek      ek size; seen + clip(v* - floor, 2 c, wmax) always (the race-free control of rc_walk)
round 3 (r2: the race-keyed walk lost to vlw_ek, the boost won; is it the cancel prediction?):
  rc_boost_vlw  clip(max(ek, bm (P_alive q_seen + q_next)), 30, hi) sh, vlw_ek limit (bm swept)
  dq_vlw        clip(max(ek, q_seen + q_next), 30, hi) sh, vlw_ek limit (depth, no P_alive)
  max_vlw       hi sh always, vlw_ek limit (size alone: the unfilled rest is free in the sim)
round 4 (r3: neither P_alive nor seen depth beats max size; the boost loses in busy hours):
  heat_vlw      hi sh while Polymarket book msgs/s over 60 s (race heat) < heat, else ek; vlw_ek limit
v* = identity-projected value of the fired side (C1 value.py: (p_side - p_other) / 2 - c / 2,
c = spread + both taker fees). q_seen / q_next from depth.py, P_alive from clock.py (fit "E"
on fair-jump events by default). Limits are clipped to [0.01, 0.99]."""
from __future__ import annotations

from collections import OrderedDict

import numpy as np

from ....sim import rules
from ...harness.api import Arm
from . import clock

_STATE: OrderedDict = OrderedDict()


def _fee(p):
    return 0.07 * p * (1 - p)


def vstar(tab, pu, pd_):
    ba, bb = tab["pm_ba"].to_numpy(float) / 100, tab["pm_bb"].to_numpy(float) / 100
    c = (ba - bb) + _fee(ba) + _fee(1 - bb)
    return (pu - pd_) / 2 - c / 2, (pd_ - pu) / 2 - c / 2


def fired_rows(t_tab, d, pu, pd_) -> np.ndarray:
    j0, j1 = np.searchsorted(t_tab, d["t"], "left"), np.searchsorted(t_tab, d["t"], "right")
    j = j0.copy()
    for n in np.flatnonzero(j1 - j0 > 1):
        c = np.arange(j0[n], j1[n])
        hit = c[np.isclose(np.maximum(pu[c], pd_[c]), d["edge"][n])]
        j[n] = hit[0] if len(hit) else j0[n]
    assert np.allclose(np.maximum(pu[j], pd_[j]), d["edge"]), "fired rows do not match the table"
    return j


def state(mk) -> dict:
    """Per-market race inputs (cached for the last few markets of this process)."""
    if mk.id in _STATE:
        return _STATE[mk.id]
    r = clock.row_inputs(mk)
    _STATE[mk.id] = r
    while len(_STATE) > 3:
        _STATE.popitem(last=False)
    return r


def race(mk, j, side, fit="E", cl=None) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """(P_alive, q_seen, q_next) of the fired rows j on their side."""
    cl = cl or clock.load()
    r = state(mk)
    q = np.where(side > 0, r["qa"][j], r["qb"][j])
    q2 = np.where(side > 0, r["qa2"][j], r["qb2"][j])
    am = clock.ahat(r["dep"], r["t"][j], cl["prior"]) - cl["prior"]
    X = clock.design(np.log1p(q), r["ltsc"][j], am, r["lpm"][j])
    return clock.p_alive(cl[fit]["coef"], X), q, q2


class Race:
    def __init__(self, mode: str, margin=0.03, require=None, fit="E", p_lo=0.3, e_hi=0.05, K=2000.0,
                 lo=30.0, hi=200.0, lo_by_L=None, p_thr=0.5, floor=0.01, wmax=0.06,
                 bm=1.0, heat=None):
        self.mode, self.margin, self.require, self.fit = mode, margin, require, fit
        self.p_lo, self.e_hi, self.K, self.lo, self.hi = p_lo, e_hi, K, lo, hi
        self.p_thr, self.floor, self.wmax, self.bm, self.heat = p_thr, floor, wmax, bm, heat
        self.lo_by_L, self._cl = lo_by_L or {}, None

    def _rule(self, mk, j, side, vs, edge, L):
        """(slip above the seen price, shares) per fired order."""
        n, m = len(j), self.mode
        ek = np.clip(self.K * np.maximum(vs, 0.0), self.lo_by_L.get(L, self.lo), self.hi)
        walk = np.clip(vs - self.floor, 0.02, self.wmax)
        if m == "vlim_tight":
            return np.clip(vs - 0.02, 0.0, 0.02), np.full(n, 60.0)
        if m == "ek":
            return np.full(n, 0.02), ek
        if m == "vlw_ek":                               # value-tied walk, no race model (control)
            return walk, ek
        if m == "max_vlw":                              # always the size cap (unfilled rest is free)
            return walk, np.full(n, float(self.hi))
        if m == "heat_vlw":                             # full size only while the race is cool (pm60 < heat)
            pm = np.expm1(state(mk)["lpm"][j])
            return walk, np.where(pm < self.heat, float(self.hi), ek)
        if m == "dq_vlw":                               # seen depth without the cancel prediction
            q, q2 = self._depth(mk, j, side)
            return walk, np.clip(np.maximum(ek, q + q2), self.lo, self.hi)
        self._cl = self._cl or clock.load()
        p, q, q2 = race(mk, j, side, self.fit, self._cl)
        if m in ("rc_lim", "rc_size"):                  # r1: tighten when the stale level is predicted gone
            slip = np.where((p < self.p_lo) & (edge < self.e_hi), 0.01, 0.02)
            sh = np.clip(np.minimum(self.K * np.maximum(vs, 0.0), p * q + q2), self.lo, self.hi) \
                if m == "rc_size" else np.full(n, 60.0)
            return slip, sh
        if m == "rc_boost":                             # size up to the depth predicted to survive
            return np.full(n, 0.02), np.clip(np.maximum(self.K * np.maximum(vs, 0.0), self.bm * (p * q + q2)), self.lo, self.hi)
        if m == "rc_walk":                              # chase repriced levels only when the stale one is gone
            return np.where(p >= self.p_thr, 0.02, walk), ek
        if m == "rc_boost_vlw":                         # race-sized boost, value-tied walk
            return walk, np.clip(np.maximum(ek, self.bm * (p * q + q2)), self.lo, self.hi)
        raise ValueError(m)

    @staticmethod
    def _depth(mk, j, side):
        r = state(mk)
        return np.where(side > 0, r["qa"][j], r["qb"][j]), np.where(side > 0, r["qa2"][j], r["qb2"][j])

    def __call__(self, mk, L):
        pu, pd_ = mk.pred("v1", L)
        tab = mk.tab
        d = rules.vtaker(tab, pu, pd_, margin=self.margin, require=self.require)
        if not len(d["t"]) or self.mode == "frz":
            return d
        j = fired_rows(tab["t"].to_numpy(), d, pu, pd_)
        side = d["side"]
        seen = np.where(side > 0, tab["pm_ba"].to_numpy(float)[j] / 100, 1 - tab["pm_bb"].to_numpy(float)[j] / 100)
        vu, vd = vstar(tab, pu, pd_)
        slip, sh = self._rule(mk, j, side, np.where(side > 0, vu[j], vd[j]), d["edge"], L)
        d["limit"] = np.clip(seen + slip, 0.01, 0.99)
        d["shares"] = np.round(sh, 2)
        return d


def _flag(f):
    f.FOLD_INVARIANT, f.CRITERION, f.SELECT_L = True, "lcb", 0
    return f


def family(margin=0.03, require=None, tag="", fit="E"):
    return [Arm(f"{m}{tag}", Race(m, margin, require, fit)) for m in ("vlim_tight", "rc_lim", "rc_size")]


@_flag
def race_taker(fold):
    return family(0.03, None, "")


@_flag
def race_veto(fold):
    return family(0.02, "trigger", "_veto")
