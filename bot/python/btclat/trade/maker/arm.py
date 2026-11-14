"""The frozen value maker `vm_fair0.03_p-0.03` (research/predict/sim/arms/sel1.py), evaluated on
one live decision row by research/predict/sim/rules.py `vmaker` itself (not a copy).

Model: the arm's "v1" at the simulator's L = 50 ms row (sim/run.py appends `_L{L}`), i.e.
v1_L50, hash-checked against prereg2.json by btclat.paper.model.load. Quotes are Up-frame ticks:
an Up bid b is a BUY of the Up token at b c; an Up ask a is a BUY of the Down token at
100 - a c (we hold no Up to sell). Each side also gets its pull flag (the model condition that
drops it), whatever the band and the clock say, for the adverse-selection split. The inside
gate (`--rule inside`) lives in rules.py; `cause` reads its gate trail too."""
from __future__ import annotations

import inspect
import math

import numpy as np

from btclat.paper.arms.frame import Frame
from research.predict.sim import rules as vrules
from research.predict.sim.arms.sel1 import ARMS as SEL1

NAME = "vm_fair0.03_p-0.03"
ARM = next(a for a in SEL1 if a["name"] == NAME)
L_MS = 50
MODEL = f"{ARM['model']}_L{L_MS}"
PARAMS = dict(ARM["params"])
_SIG = inspect.signature(vrules.vmaker).parameters
BAND = tuple(PARAMS.get("band", _SIG["band"].default))
TLEFT = float(PARAMS.get("tleft", _SIG["tleft"].default))
COLS = ("t", "pm_bb", "pm_ba", "pm_mid", "secs_left", "fair_p")
SIDES = ("bid", "ask")
assert PARAMS == {"half": 0.03, "pull": -0.03, "anchor": "fair"} and MODEL == "v1_L50"


def quote(r: dict, pu: float, pdn: float) -> dict:
    """Target ticks (0 = no quote) and pull flags of one decision row."""
    _, b, a = vrules.vmaker(Frame({k: r[k] for k in COLS}), np.array([pu]), np.array([pdn]), **PARAMS)
    pull = PARAMS["pull"]
    return {"bid": int(b[0]), "ask": int(a[0]),
            "pull_bid": not pdn < pull,      # the Up bid is run over when Down gains
            "pull_ask": not pu < pull}       # the Up ask is lifted when Up gains


def cause(q: dict, side: str) -> str:
    """Why a side has no quote (first failing gate, in the rule's order)."""
    if q.get(side):
        return "rule"
    mid = q.get("mid", math.nan)
    if not q.get("secs_left", 0.0) >= TLEFT:
        return "tleft"
    if not (BAND[0] <= mid <= BAND[1]):
        return "band"
    if not math.isfinite(q.get("fair", math.nan)):
        return "fair"
    if not (q.get("bb", 0) > 0 and q.get("ba", 100) < 100):
        return "book"
    if q.get(f"pull_{side}"):
        return "pull"
    if q.get(f"in_{side}"):
        return "hyst"           # inside rule: held back by the insert hysteresis
    if q.get(f"raw_{side}"):
        return "outside"        # inside rule: the rule's tick is not strictly inside the spread
    return "range"


def price(side: str, tick: int) -> float:
    """Price of the token we BUY for an Up-frame quote tick."""
    return round(tick / 100 if side == "bid" else (100 - tick) / 100, 2)
