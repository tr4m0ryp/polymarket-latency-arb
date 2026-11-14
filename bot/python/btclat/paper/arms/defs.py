"""The arms the paper bot runs, taken from the research arm modules (not copied), so gates,
sizes (60 sh), limits (seen ask + 2 c) and refractory (0.2 s) are the simulator's.

- vt_v1_m0.03_any     predictive taker (pre-registered, prereg2.json)
- vt_v1_m0.02_trigger predictive veto on the leaders' microprice trigger (pre-registered)
- micf                strategy winner: microprice trigger + pzm fair filter (baseline)
- theirs_micro        the leaders' rule, rebuilt (baseline)"""
from __future__ import annotations

from research.predict.sim.arms.base import MICF, THEIRS
from research.predict.sim.arms.sel1 import ARMS as SEL1

PRIMARY = ("vt_v1_m0.03_any", "vt_v1_m0.02_trigger")
VT_ARMS = [a for a in SEL1 if a["name"] in PRIMARY]
MICRO_ARMS = [dict(MICF, name="micf"), dict(THEIRS, name="theirs_micro")]
ARM_NAMES = [a["name"] for a in VT_ARMS] + [a["name"] for a in MICRO_ARMS]
assert len(VT_ARMS) == 2 and {a["model"] for a in VT_ARMS} == {"v1"}


def refr(arm: dict) -> float:
    """Refractory of an arm (rules' defaults when the arm does not set it)."""
    return float(arm["params"].get("refr", 0.2))
assert all(a["params"]["win"] == 0.1 for a in MICRO_ARMS)   # features/raw.py micro_view reads 0.1 s
