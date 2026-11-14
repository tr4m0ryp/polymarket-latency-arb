"""Decision rules of C5: the frozen 1 s taker rule (60 sh, limit seen ask + 2 c, 0.2 s
refractory) driven by a per-fold refit of the value model instead of the frozen v1_L0.

Optional identity projection (the coherence fix of C3, diag-loss-anatomy idea 6): buying Up at
the ask and Down at 1 - bid costs the spread plus both fees more than a share of each is
worth, v_up + v_dn = -c, so the symmetric part of the two side predictions is model error;
v*_side = (pred_side - pred_other) / 2 - c / 2 removes it (= pred_side when e = 0)."""
from __future__ import annotations

import numpy as np

from ....model.derive import add_derived
from ....model.data import features
from ....model.learners import clean
from ....model.orient import orient
from ....sim import rules
from ...diag.calibration.ctx.load import busy, ctx
from ...harness.api import Arm
from .fit.model import BUSY_FEAT


def fee(p):
    return 0.07 * p * (1 - p)


def project(tab, pu, pd_):
    ba, bb = tab["pm_ba"].to_numpy(float) / 100, tab["pm_bb"].to_numpy(float) / 100
    c = (ba - bb) + fee(ba) + fee(1 - bb)
    pu, pd_ = np.asarray(pu, float), np.asarray(pd_, float)
    return (pu - pd_) / 2 - c / 2, (pd_ - pu) / 2 - c / 2


def predict(mk, mdl: dict) -> tuple[np.ndarray, np.ndarray]:
    """Both side predictions of a refit model on one market (model.store.predict_sides, plus the
    unsigned busy index column when the model was fitted with it)."""
    if BUSY_FEAT not in mdl["vf"]:
        return mk.pred(mdl)
    key = ("c5", id(mdl))
    if key not in mk._pred:
        d = add_derived(mk.tab.copy())
        feats = features(d)
        b = busy(ctx(mk.id, len(d)))
        out = []
        for side in (1, -1):
            o = orient(d, feats, side)
            o[BUSY_FEAT] = b
            for c in mdl["vf"]:
                if c not in o:
                    o[c] = 0.0
            out.append(mdl["model"].predict(clean(o[mdl["vf"]].to_numpy())))
        mk._pred[key] = (out[0], out[1])
    return mk._pred[key]


class Refit:
    """blend = weight of the refit in a mix with the frozen v1_L0 predictions (1 = refit only)."""

    def __init__(self, mdl: dict, margin: float = 0.03, coh: bool = False, blend: float = 1.0):
        self.mdl, self.margin, self.coh, self.blend = mdl, margin, coh, blend

    def __call__(self, mk, L):
        assert L == 0, "C5 refits the L = 0 model only (run the harness with --L=0)"
        pu, pdn = predict(mk, self.mdl)
        if self.blend < 1:
            fu, fd = mk.pred("v1", L)
            pu, pdn = self.blend * pu + (1 - self.blend) * fu, self.blend * pdn + (1 - self.blend) * fd
        if self.coh:
            pu, pdn = project(mk.tab, pu, pdn)
        return rules.vtaker(mk.tab, pu, pdn, margin=self.margin)


def arm(name: str, mdl: dict, margin: float = 0.03, coh: bool = False, blend: float = 1.0) -> Arm:
    return Arm(name, Refit(mdl, margin, coh, blend))
