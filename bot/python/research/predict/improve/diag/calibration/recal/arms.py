"""Arms of the recalibration simulator run and the fitted state they need.

Takers: the deployed vt_v1_m0.03_any rule (60 sh, limit seen ask + 2 c, 0.2 s refractory,
gates unchanged) on each registry form (recal/registry.py); `vt_v1_m3` is the frozen arm
rebuilt (reproduction check). Vetoes: the deployed vt_v1_m0.02_trigger (leaders' trigger kept
when p >= 2 c) on the VETO forms, every margin 1 c lower than the taker's."""
from __future__ import annotations

import pickle

import numpy as np
import pandas as pd

from .. import CACHE
from ..analyze.common import cuts, rows
from .registry import FORMS, make_fit, score

VETO = ("m3", "m4", "onl_r10_30")


def _busy(rg: dict, ref: dict) -> np.ndarray:
    z = [(np.log1p(rg[c].astype(float) * (100 if c == "rv60" else 1)) - ref[c][0]) / ref[c][1]
         for c in ("bn60", "rv60", "pmtr60")]
    return np.mean(z, axis=0)


def prepare(names: str | None):
    from .rows import timeline
    names = FORMS if names is None else names.split(",")
    tr = rows("train")
    ref = {}
    for c in ("bn60", "rv60", "pmtr60"):
        x = np.log1p(tr[c].to_numpy(float) * (100 if c == "rv60" else 1))
        ref[c] = (float(x.mean()), float(x.std()))
    cache = CACHE / "recal_fit.pkl"
    if cache.exists():
        with open(cache, "rb") as fh:
            fit = pickle.load(fh)
    else:
        fit = make_fit({L: timeline(f"v1_L{L}") for L in (0, -40)}, {"busy": cuts()["busy"], "pmtr60": cuts()["pmtr60"]})
        fit["ref"] = ref
        with open(cache, "wb") as fh:
            pickle.dump(fit, fh)
    arms = [{"name": f"vt_v1_{n}", "form": n, "shift": 0.0, "params": {}} for n in names]
    arms += [{"name": f"vt_v1_trig_{n}", "form": n, "shift": -0.01, "params": {"require": "trigger"}}
             for n in names if n in VETO]
    return arms, fit


def adjust(arm: dict, preds, tab: pd.DataFrame, rg: dict, L: int, fit: dict):
    """(score_up, score_down, margin) for rules.vtaker."""
    t = tab["t"].to_numpy(float)
    lo, hi = fit["cuts"]["busy"]
    b = _busy(rg, fit["ref"])
    lv = np.where(b < lo, 0, np.where(b < hi, 1, 2))
    plo, phi = fit["cuts"]["pmtr60"]
    x = rg["pmtr60"].astype(float)
    lvp = np.where(x < plo, 0, np.where(x < phi, 1, 2))
    su, m = score(arm["form"], preds[0], t, lv, lvp, L, fit, b)
    sd, _ = score(arm["form"], preds[1], t, lv, lvp, L, fit, b)
    return su, sd, m + arm["shift"]
