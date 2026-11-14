"""Two worked candidates showing the plug-in interface (not results).

    python3 -m research.predict.improve.harness --arm research.predict.improve.harness.example:margin_sweep --out ...

margin_sweep: the frozen 1 s taker with its margin as the variant (no retraining, so
FOLD_INVARIANT: each (variant, market) is simulated once and reused by both folds).
retrained: refits the 1 s value model per fold on run 2 train + that fold's choose windows
(Fold.load_rows; small sample for speed), then trades it with the frozen rule."""
from __future__ import annotations

import numpy as np

from ...model.learners import clean, gbdt_reg
from ...model.stack import stacked
from ...sim import rules
from .api import Arm


class _Margin:
    def __init__(self, margin: float):
        self.margin = margin

    def __call__(self, mk, L):
        pu, pdn = mk.pred("v1", L)                      # frozen v1_L{L} predictions, cached
        return rules.vtaker(mk.tab, pu, pdn, margin=self.margin)


def margin_sweep(fold):
    return [Arm(f"vt_v1_m{m}", _Margin(m)) for m in (0.025, 0.03, 0.035, 0.04)]


margin_sweep.FOLD_INVARIANT = True
margin_sweep.CRITERION = "gain"


class _Fitted:
    def __init__(self, models: dict, margin: float):
        self.models, self.margin = models, margin

    def __call__(self, mk, L):
        pu, pdn = mk.pred(self.models[L])               # candidate-fitted model dict {"model", "vf"}
        return rules.vtaker(mk.tab, pu, pdn, margin=self.margin)


def retrained(fold, frac: float = 0.05, iters: int = 50):
    tr, vf = stacked(fold.load_rows(frac=frac, seed=1))   # train + this fold's choose windows only
    models = {}
    for L in (0, -40):
        w = np.isfinite(tr[f"v1_{L}"].to_numpy()) & (tr[f"bad{L}"] == 0).to_numpy()
        m = gbdt_reg(max_iter=iters, leaves=15, lr=0.05, min_leaf=200).fit(
            clean(tr.loc[w, vf].to_numpy()), np.clip(tr.loc[w, f"v1_{L}"].to_numpy(float), -0.3, 0.3))
        models[L] = {"model": m, "vf": vf}
    return Arm("vt_refit_m0.03", _Fitted(models, 0.03))
