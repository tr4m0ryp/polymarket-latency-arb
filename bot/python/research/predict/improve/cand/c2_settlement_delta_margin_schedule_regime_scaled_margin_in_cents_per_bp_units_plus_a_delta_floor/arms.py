"""The delta-margin rule and its variant families (harness plug-ins).

_DM(sched, floor, require, base): per decision row, margin = base, then for each
(threshold, margin) of `sched` in ascending threshold order margin = that value where
delta >= threshold, and no order where delta < floor. The frozen vtaker does the rest
(`edge >= margin` broadcasts the per-row array; 60 sh, seen ask + 2 c, 0.2 s refractory).

Families (fold-invariant: the rule never reads a label, so each variant is simulated once):
    dm_taker  the pre-registered C2 taker schedule (5 variants)
    dm_veto   the trigger veto with a delta floor (3 variants)"""
from __future__ import annotations

import numpy as np

from ....sim import rules
from ...harness.api import Arm
from .delta import SEALED, delta


class _DM:
    def __init__(self, sched=(), floor: float = 0.0, require=None, base: float = 0.03):
        self.sched = tuple(sorted(sched))
        self.floor, self.require, self.base = float(floor), require, float(base)

    def margin(self, tab) -> np.ndarray:
        dl = delta(tab)
        m = np.full(len(tab), self.base)
        for thr, mc in self.sched:
            m[dl >= thr] = mc
        m[dl < self.floor] = np.inf
        return m

    def __call__(self, mk, L):
        assert mk.start < SEALED, f"market {mk.id} is sealed"
        pu, pdn = mk.pred("v1", L)
        return rules.vtaker(mk.tab, pu, pdn, margin=self.margin(mk.tab), require=self.require)


class _DC(_DM):
    """Continuous schedule: margin = clip(base * (ref / delta) ** a, lo, hi), no order below
    `floor`; the margin is set in the units in which the Binance lead converts into token
    cents (a = 1: a fixed margin in bp of BTC, a = 0: the frozen fixed cents margin)."""

    def __init__(self, a: float, ref: float = 25.0, lo: float = 0.02, hi: float = 0.08,
                 floor: float = 0.0, require=None, base: float = 0.03):
        super().__init__((), floor, require, base)
        self.a, self.ref, self.lo, self.hi = float(a), float(ref), float(lo), float(hi)

    def margin(self, tab) -> np.ndarray:
        dl = delta(tab)
        with np.errstate(divide="ignore", invalid="ignore"):
            m = np.clip(self.base * (self.ref / np.maximum(dl, 1e-6)) ** self.a, self.lo, self.hi)
        m = np.where(np.isfinite(dl), m, self.base)
        return np.where(dl < self.floor, np.inf, m)


def _tag(sched, floor) -> str:
    # threshold, with "@<cents>" when that step's margin is not the pre-registered 2.5 c
    s = "_".join(f"{t:g}" + ("" if m == .025 else f"@{100 * m:g}") for t, m in sorted(sched)) or "none"
    return f"dm{s}_f{floor:g}" if floor else f"dm{s}"


def taker_arms(specs) -> list[Arm]:
    """specs: (sched, floor[, base]) tuples -> taker Arms named dm<thr..>[_f<floor>]."""
    out = []
    for sp in specs:
        sched, floor = sp[0], sp[1]
        base = sp[2] if len(sp) > 2 else 0.03
        name = _tag(sched, floor) + ("" if base == 0.03 else f"_b{base:g}")
        out.append(Arm(name, _DM(sched, floor, None, base)))
    return out


def _mark(fn):
    fn.FOLD_INVARIANT, fn.CRITERION, fn.SELECT_L = True, "lcb", 0
    return fn


TAKER = [([(25, .025)], 0), ([(25, .025)], 3), ([(40, .025)], 3), ([(12, .025)], 3),
         ([(25, .025), (40, .02)], 3)]


@_mark
def dm_taker(fold):
    return taker_arms(TAKER)


@_mark
def dm_veto(fold):
    return [Arm(f"dmv_f{f:g}", _DM((), f, "trigger", 0.02)) for f in (3, 4, 6)]


# ---- follow-up families (diagnosis-driven variants; each is its own CV candidate) ----

@_mark
def dm_floor(fold):
    """Floor alone on the taker (no lowering): isolates the low-delta cut."""
    return taker_arms([([], f) for f in (3, 5, 8)])


@_mark
def dm_cont(fold):
    """Continuous margin in cents-per-bp units: 3 c at delta 25, rising as delta falls."""
    out = []
    for a in (0.5, 1.0):
        for f in (0, 3):
            out.append(Arm(f"dc{a:g}_r25" + (f"_f{f}" if f else ""), _DC(a, 25.0, 0.02, 0.08, f)))
    return out


@_mark
def dm_deep(fold):
    """Deeper lowering at high delta (2 c) with the 3 c/bp floor."""
    return taker_arms([([(25, .02)], 3), ([(40, .02)], 3), ([(25, .025), (60, .02)], 3)])


@_mark
def dm_more(fold):
    """One simulation pass for every follow-up variant (sub-families are re-scored offline with
    the harness's own choice rule, cvsub.py): one-at-a-time sweep around the winner dm25_f3,
    the floor alone, the continuous bp-unit margin, and a lowering band capped at 80 c/bp."""
    arms = taker_arms([([(25, .025)], 3), ([(20, .025)], 3), ([(30, .025)], 3), ([(25, .0225)], 3),
                       ([(25, .0275)], 3), ([(25, .025)], 2), ([(25, .025)], 4), ([], 3), ([], 5),
                       ([(25, .025), (80, .03)], 3)])
    arms += [Arm("dc0.5_r25", _DC(0.5)), Arm("dc0.5_r25_f3", _DC(0.5, floor=3)),
             Arm("dc1_r25_f3", _DC(1.0, floor=3))]
    return arms


@_mark
def dm_veto_more(fold):
    """Veto follow-ups: the floor swept below and between the pre-registered {3, 4, 6}, and the
    taker's high-delta lowering carried to the veto (2 c -> 1.5 c at delta >= 25) on the f3 floor."""
    arms = [Arm(f"dmv_f{f:g}", _DM((), f, "trigger", 0.02)) for f in (2, 3, 5)]
    arms.append(Arm("dmv25@1.5_f3", _DM([(25, .015)], 3, "trigger", 0.02)))
    return arms


@_mark
def dm_veto_lower(fold):
    """Sweep of the veto's high-delta lowering (threshold x lowered margin) on the f3 floor."""
    grid = [(25, .015), (25, .01), (25, .0175), (12, .015), (40, .015)]
    return [Arm(f"dmv{t:g}@{100 * m:g}_f3", _DM([(t, m)], 3, "trigger", 0.02)) for t, m in grid]
