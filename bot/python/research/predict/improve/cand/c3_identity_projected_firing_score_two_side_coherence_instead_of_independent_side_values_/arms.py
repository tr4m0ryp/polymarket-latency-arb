"""C3 arms: the frozen v1 firing rule (rules.vtaker, unchanged) scored on identity-projected
side values instead of the independent side predictions. No retraining, no new feed; every
family is fold-invariant (the variants are the margin and the projection form).

    python3 -m research.predict.improve.cand.c3_identity_projected_firing_score_two_side_coherence_instead_of_independent_side_values_.run \
        --arm coh_taker --out data/out/predict/improve/c3_coherence/coh_taker/

Families (CRITERION lcb, SELECT_L 0, chosen on the fold's choose windows only):
    coh_taker   full projection, margins 2.5 / 3 / 3.5 c                    (the pre-registered form)
    coh_veto    full projection on the leaders' trigger, margins 1.5 / 2 / 2.5 c
    *_half      lam = 0.5 (shrink halfway to the identity)
    *_cap       remove only common-mode optimism (e > 0), never admit new rows
    *_gate      frozen edge AND projected edge >= floor (a second gate on the frozen rule)
    cm_*        round 2: the same forms anchored on E[c_m | x] (cost.py) instead of the seen book
    filt_*      round 3: filter-only forms in one family (cap, gate, half), never admitting new rows
    lam_*       round 4: projection strength lam 0.25 / 0.5 / 0.75 (0 = frozen, 1 = full projection)
    anti_*      round 5: lam < 0, the inverted sign (common-mode rows rewarded)"""
from __future__ import annotations

import numpy as np

from research.predict.improve.harness.api import Arm
from research.predict.sim import rules

from .cost import chat, cost_model as chat_ready
from .score import projected


class Coh:
    """decide(mk, L) for one (margin, require, projection) setting."""

    def __init__(self, margin: float, require=None, mode: str = "proj", lam: float = 1.0,
                 floor: float | None = None, anchor: str = "seen"):
        self.margin, self.require, self.mode, self.lam, self.floor = margin, require, mode, lam, floor
        self.anchor = anchor     # "seen": c on the book we saw; "cm": expected match-time cost (cost.py)

    def values(self, tab, pu, pd_, L=None, c=None):
        if self.anchor == "cm" and c is None:
            c = chat(tab, L)
        elif self.anchor != "cm":
            c = None
        if self.floor is not None:   # gate form: frozen edge, plus projected edge of that side >= floor
            vu, vd, e = projected(tab, pu, pd_, "proj", 1.0, c)
            side_up = np.asarray(pu) >= np.asarray(pd_)
            ok = np.where(side_up, vu, vd) >= self.floor
            pu = np.where(ok, pu, -1.0)
            pd_ = np.where(ok, pd_, -1.0)
            return pu, pd_, e
        return projected(tab, pu, pd_, self.mode, self.lam, c)

    def __call__(self, mk, L):
        tab = mk.tab
        pu, pd_ = mk.pred("v1", L)
        c = None
        if self.anchor == "cm":      # one cost-model pass per (market, L), shared by the variants
            c = mk._pred.get(("c3_chat", L))
            if c is None:
                c = mk._pred[("c3_chat", L)] = chat(tab, L)
        vu, vd, _ = self.values(tab, pu, pd_, L, c)
        return rules.vtaker(tab, vu, vd, margin=self.margin, require=self.require)


def _family(prefix: str, margins, require=None, mode="proj", lam=1.0, floors=None, anchor="seen"):
    def cand(fold):
        if anchor == "cm":   # fit (or load) the train-only cost models in the parent, before the fork
            for L in (0, -40):
                chat_ready(L)
        if floors is not None:
            return [Arm(f"{prefix}_m{margins[0]}_f{f}", Coh(margins[0], require, floor=f, anchor=anchor))
                    for f in floors]
        return [Arm(f"{prefix}_m{m}", Coh(m, require, mode, lam, anchor=anchor)) for m in margins]
    cand.FOLD_INVARIANT, cand.CRITERION, cand.SELECT_L = True, "lcb", 0
    return cand


TAKER_M, VETO_M = (0.025, 0.03, 0.035), (0.015, 0.02, 0.025)

coh_taker = _family("coh_any", TAKER_M)
coh_veto = _family("coh_trig", VETO_M, require="trigger")
coh_taker_half = _family("cohh_any", TAKER_M, lam=0.5)
coh_veto_half = _family("cohh_trig", VETO_M, require="trigger", lam=0.5)
coh_taker_cap = _family("cohc_any", TAKER_M, mode="cap")
coh_veto_cap = _family("cohc_trig", VETO_M, require="trigger", mode="cap")
coh_taker_gate = _family("cohg_any", (0.03,), floors=(0.0, 0.01, 0.02))
coh_veto_gate = _family("cohg_trig", (0.02,), require="trigger", floors=(0.0, 0.01, 0.02))

# round 2: anchor on the expected match-time cost (cost.py), the identity's actual zero
cm_taker = _family("cm_any", TAKER_M, anchor="cm")
cm_veto = _family("cm_trig", VETO_M, require="trigger", anchor="cm")
cm_taker_cap = _family("cmc_any", TAKER_M, mode="cap", anchor="cm")
cm_veto_cap = _family("cmc_trig", VETO_M, require="trigger", mode="cap", anchor="cm")
cm_taker_half = _family("cmh_any", TAKER_M, lam=0.5, anchor="cm")
cm_veto_half = _family("cmh_trig", VETO_M, require="trigger", lam=0.5, anchor="cm")


def _mixed(name: str, arms):
    """One family over several projection forms (the harness picks one on the choose windows)."""
    def cand(fold):
        return [Arm(n, c) for n, c in arms]
    cand.FOLD_INVARIANT, cand.CRITERION, cand.SELECT_L = True, "lcb", 0
    cand.__name__ = name
    return cand


# round 3: filter-only forms (never admit rows the frozen rule would not fire on, up to refractory)
filt_taker = _mixed("filt_taker", [("cohc_any_m0.025", Coh(0.025, None, "cap")), ("cohc_any_m0.03", Coh(0.03, None, "cap")),
                                   ("cohg_any_m0.03_f0.0", Coh(0.03, floor=0.0)), ("cohg_any_m0.03_f0.01", Coh(0.03, floor=0.01)),
                                   ("cohh_any_m0.03", Coh(0.03, None, "proj", 0.5))])
filt_veto = _mixed("filt_veto", [("cohc_trig_m0.015", Coh(0.015, "trigger", "cap")), ("cohc_trig_m0.02", Coh(0.02, "trigger", "cap")),
                                 ("cohg_trig_m0.02_f0.0", Coh(0.02, "trigger", floor=0.0)),
                                 ("cohg_trig_m0.02_f0.01", Coh(0.02, "trigger", floor=0.01)),
                                 ("cohh_trig_m0.02", Coh(0.02, "trigger", "proj", 0.5))])

# round 4: projection strength sweep (lam = 0 is the frozen rule, 1 the full identity projection)
lam_taker = _mixed("lam_taker", [(f"cmh{l}_any_m0.03", Coh(0.03, None, "proj", l, anchor="cm")) for l in (0.25, 0.5, 0.75)]
                   + [(f"cohh{l}_any_m0.03", Coh(0.03, None, "proj", l)) for l in (0.25,)])
lam_veto = _mixed("lam_veto", [(f"cmh{l}_trig_m0.02", Coh(0.02, "trigger", "proj", l, anchor="cm")) for l in (0.25, 0.5, 0.75)]
                  + [(f"cohh{l}_trig_m0.02", Coh(0.02, "trigger", "proj", l)) for l in (0.25,)])

# round 5: the inversion the split diagnostic points at (orders the projection drops earn MORE in the
# simulator than the ones it admits): reward the common mode instead, lam < 0 (edge = pred + |lam| e / 2)
anti_taker = _mixed("anti_taker", [(f"anti{l}_any_m0.03", Coh(0.03, None, "proj", l)) for l in (-0.25, -0.5, -1.0)]
                    + [("anticm-0.5_any_m0.03", Coh(0.03, None, "proj", -0.5, anchor="cm"))])
anti_veto = _mixed("anti_veto", [(f"anti{l}_trig_m0.02", Coh(0.02, "trigger", "proj", l)) for l in (-0.25, -0.5, -1.0)]
                   + [("anticm-0.5_trig_m0.02", Coh(0.02, "trigger", "proj", -0.5, anchor="cm"))])
# round 5 sweep (post hoc: designed after anti_veto's every-variant table): the match-cost-anchored
# inversion on the veto, lam and margin around anticm-0.5_trig_m0.02
anticm_veto = _mixed("anticm_veto", [(f"anticm{l}_trig_m0.02", Coh(0.02, "trigger", "proj", l, anchor="cm"))
                                     for l in (-0.25, -0.5, -0.75, -1.0)]
                     + [("anticm-0.5_trig_m0.025", Coh(0.025, "trigger", "proj", -0.5, anchor="cm"))])
