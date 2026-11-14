"""Competition-adaptive limits: walk up the book only while the predicted value still pays.

The deployed arms send limit = seen ask + 2 c whatever the prediction. When rivals or makers
clear the touch during the 150 ms hold, the order walks up to whatever is left within 2 c.
A value-capped limit sets limit = seen + clip(edge - floor, lo, hi): the remaining levels
are taken only while (predicted value at the seen ask) - (walk-up) >= floor, so a large
predicted value lets the order chase depth that rivals left behind, and a small one stops it
from buying what they priced out.
  vl<floor>   lo = 0     (tighter than + 2 c when edge < floor + 2 c)
  vlw<floor>  lo = 0.02  (never tighter than the deployed + 2 c, only looser)
  ...+ek      shares = 3000 x edge in [60, 200] (the edge-keyed size, diag-competition-edge2)
Decision-time observables only (edge, seen). hi = 0.10."""
from __future__ import annotations

import numpy as np

HI = 0.10


def _limit(floor: float, lo: float):
    def lim(d):
        e = np.nan_to_num(d["edge"], nan=0.0)
        return np.minimum(d["seen"] + np.clip(e - floor, lo, HI), 0.99)
    return lim


def _ek(d, f):
    return np.clip(np.round(3000 * np.nan_to_num(d["edge"], nan=0.0)), 60, 200)


# name -> (limit fn, size rule or None)
VLIM = {}
for _f in (0.0, 0.01, 0.02):
    VLIM[f"vl{_f:g}"] = (_limit(_f, 0.0), None)
    VLIM[f"vlw{_f:g}"] = (_limit(_f, 0.02), None)
    VLIM[f"vlw{_f:g}+ek"] = (_limit(_f, 0.02), _ek)
VLIM["ek3000_60_200"] = (None, _ek)   # size alone, same run (pairing reference)
