"""Where does the projection lose? Diagnostic arms (read from variants.csv, never a candidate):
the projected rule's orders split against the frozen rule's on the same market and L.

    promo_* : orders the projected rule sends at times the frozen rule does not (rows it admits)
    drop_*  : orders the frozen rule sends at times the projected rule does not (rows it removes)

If promo loses money per $ in the simulator while the best-level 1 s / 10 s value of the same
rows is positive (diag_ols top-k), the loss is execution (depth, rivals, limit), not ranking.

    nice -n 10 python3 -m research.predict.improve.cand.<pkg>.run --arm split_taker --out .../split_taker/"""
from __future__ import annotations

import numpy as np

from research.predict.improve.harness.api import Arm

from .arms import Coh


class _Split:
    def __init__(self, proj: Coh, frozen: Coh, keep: str):
        self.proj, self.frozen, self.keep = proj, frozen, keep

    def __call__(self, mk, L):
        a, b = self.proj(mk, L), self.frozen(mk, L)
        src, other = (a, b) if self.keep == "promo" else (b, a)
        m = ~np.isin(src["t"], other["t"])
        return {k: np.asarray(v)[m] for k, v in src.items()}


def _fam(name, pairs):
    def cand(fold):
        return [Arm(n, _Split(p, f, k)) for n, p, f, k in pairs]
    cand.FOLD_INVARIANT, cand.CRITERION, cand.SELECT_L = True, "mk", 0
    cand.__name__ = name
    return cand


_VT, _VETO = Coh(0.03, None, "none"), Coh(0.02, "trigger", "none")
split_taker = _fam("split_taker", [
    ("promo_seen_any", Coh(0.03), _VT, "promo"), ("drop_seen_any", Coh(0.03), _VT, "drop"),
    ("promo_cm_any", Coh(0.03, anchor="cm"), _VT, "promo"), ("drop_cm_any", Coh(0.03, anchor="cm"), _VT, "drop"),
    ("promo_seen_trig", Coh(0.02, "trigger"), _VETO, "promo"), ("drop_seen_trig", Coh(0.02, "trigger"), _VETO, "drop")])
