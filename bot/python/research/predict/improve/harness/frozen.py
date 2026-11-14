"""The deployed arms and the baseline as plug-in Arms, built from the frozen specs
(research/predict/sim/arms/sel1.py, base.py; data/out/predict/freeze.json).

    vt_v1_m0.03_any     : 1 s value model, margin 3 c, 60 sh, limit seen ask + 2 c, refr 0.2 s
    vt_v1_m0.02_trigger : leaders' microprice trigger kept when the 1 s model predicts >= 2 c
    micf                : leaders' trigger + fair-value filter (strategy winner), the baseline

`from_spec` turns any predict sim arm dict (kinds base / vtaker / vmaker) into an Arm, so a
candidate can be a spec dict ("a model + rule") instead of a decision function."""
from __future__ import annotations

from ...sim import rules
from ...sim.arms.base import ARMS as BASE
from ...sim.arms.sel1 import ARMS as SEL1
from ....strategy.eval import sim as ssim
from .api import Arm

VT_ANY, VETO, MICF = "vt_v1_m0.03_any", "vt_v1_m0.02_trigger", "micf"
FROZEN = (VT_ANY, VETO, MICF)
SPECS = {a["name"]: a for a in SEL1 + BASE if a["name"] in FROZEN}


class _VTaker:
    def __init__(self, model, params, per_L=True):
        self.model, self.params, self.per_L = model, params, per_L

    def __call__(self, mk, L):
        pu, pdn = mk.pred(self.model, L if self.per_L else None)
        return rules.vtaker(mk.tab, pu, pdn, **self.params)


class _VMaker(_VTaker):
    def __call__(self, mk, L):
        pu, pdn = mk.pred(self.model, L if self.per_L else None)
        t, b, a = rules.vmaker(mk.tab, pu, pdn, **self.params)
        return {"t": t, "bid": b, "ask": a}


class _Base:
    def __init__(self, arm):
        self.arm = arm

    def __call__(self, mk, L):
        f2 = mk.f2
        if f2 is None or not len(f2):
            return None
        return ssim.decisions(f2, self.arm)


def from_spec(spec: dict) -> Arm:
    k = spec["kind"]
    if k == "base":
        return Arm(spec["name"], _Base(spec["arm"]))
    if k == "vtaker":
        return Arm(spec["name"], _VTaker(spec["model"], spec["params"], spec.get("per_L", True)))
    if k == "vmaker":
        return Arm(spec["name"], _VMaker(spec["model"], spec["params"], spec.get("per_L", True)),
                   kind="maker", size=spec.get("size", 60.0), max_open=spec.get("max_open", 300.0))
    raise ValueError(f"spec kind {k} not supported (base, vtaker, vmaker)")


def frozen_arms() -> list[Arm]:
    return [from_spec(SPECS[n]) for n in FROZEN]


def _ref(name: str) -> Arm:
    a = from_spec(SPECS[name])
    a.ref = name
    return a


def vt_any(fold):
    return _ref(VT_ANY)


def veto(fold):
    return _ref(VETO)


def micf(fold):
    return _ref(MICF)


for _f in (vt_any, veto, micf):
    _f.FOLD_INVARIANT = True
