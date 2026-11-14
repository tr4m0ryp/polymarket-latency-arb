"""Decisions of the deployed arms and the baselines on one market, exactly as the frozen runs
made them (research/predict/sim/run.py): micf on the strategy v2 table, value takers on the
predict table with the frozen models (data/out/predict/models, read only)."""
from __future__ import annotations

import pickle

import numpy as np
import pandas as pd

from ......strategy.eval import sim as ssim
from ......strategy.eval.prep import FEAT2
from .....model.data import TAB
from .....model.store import load_model, predict_sides
from .....sim import rules
from .....sim.arms.base import MICF
from .. import OUT

# name -> (kind, model, params); L list per arm
ARMS = {
    "micf": ("base", None, None),
    "vt_v1_m0.03_any": ("vtaker", "v1", dict(margin=0.03, require=None)),
    "vt_v1_m0.02_trigger": ("vtaker", "v1", dict(margin=0.02, require="trigger")),
    "vt_v3p_m0.02_any": ("vtaker", "v3p", dict(margin=0.02, require=None)),
}
LS = {"micf": (0, -40), "vt_v1_m0.03_any": (0, -40), "vt_v1_m0.02_trigger": (0, -40),
      "vt_v3p_m0.02_any": (0,)}
# race-aware label models (race/label.py, data/out/predict/improve/models), L = 0 only
RACE = {f"vt_{m}_m{g}_{r or 'any'}": ("vtaker", m, dict(margin=g, require=r))
        for m in ("v1rmin", "v1ravg") for g, r in ((0.02, None), (0.03, None), (0.01, "trigger"), (0.02, "trigger"))}
RACE_LS = {k: (0,) for k in RACE}
SLIP = 0.02
_MDL = {}


def _model(key):
    if key not in _MDL:
        if key.startswith("v1r"):
            with open(OUT / "models" / f"{key}.pkl", "rb") as fh:
                _MDL[key] = pickle.load(fh)
        else:
            _MDL[key] = load_model(key)
    return _MDL[key]


def tables(i: int):
    with np.load(TAB / f"{i}.npz") as z:
        tab = pd.DataFrame({k: z[k] for k in z.files})
    p2 = FEAT2 / f"{i}.pkl"
    f2 = pd.read_pickle(p2) if p2.exists() else None
    return tab, f2


def decisions(i: int, race: bool = False) -> list[tuple[str, int, dict]]:
    """[(arm, L, d)] with d = t, side, shares, limit, seen, edge (numpy arrays, sorted by t)."""
    tab, f2 = tables(i)
    preds, out = {}, []
    arms, ls = (RACE, RACE_LS) if race else (ARMS, LS)
    for arm, (kind, mdl, params) in arms.items():
        for L in ls[arm]:
            if kind == "base":
                if f2 is None or not len(f2):
                    continue
                d = ssim.decisions(f2, MICF)
                d = {k: d[k] for k in ("t", "side", "shares", "limit", "edge")}
            else:
                key = f"{mdl}_L{L}"
                if key not in preds:
                    preds[key] = predict_sides(tab, _model(key))
                d = rules.vtaker(tab, *preds[key], **params)
            if not len(d["t"]):
                continue
            d["seen"] = np.round(d["limit"] - SLIP, 2)
            out.append((arm, L, d))
    return out
