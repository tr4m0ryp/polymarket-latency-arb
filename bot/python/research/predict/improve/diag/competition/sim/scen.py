"""Fill scenarios run on the same decisions: competition-aware fill models and size rules.

Fill models (60 sh): base = the frozen simulator (J 10 ms, cap 1); comp = the report's
sensitivity (J 50 ms, half of each level); e+X / e-X = we match X ms later / earlier than the
simulator assumes, with the simulator's rule (a race curve: every rival in the gap beats us).
Size rules (decision-time observables only, base and comp fills):
  s20 / s40 / s100 fixed; dk<k> = shares = k x our-view depth at the seen price, 5..60;
  rv<n>_<s> = s shares when >= n same-side prints arrived in the last 1 s (receipt), else 60.
Limit rules: sl0 / sl1 = limit at the seen ask + 0 / 1 c instead of + 2 c (do not chase depth
that rivals cleared during the hold)."""
from __future__ import annotations

import numpy as np

FILL = {"base": dict(J=0.010, cap=1.0, e=0.0), "comp": dict(J=0.050, cap=0.5, e=0.0)}
for _ms in (-50, -25, 10, 25, 50, 100, 200):
    FILL[f"e{_ms:+d}"] = dict(J=0.010, cap=1.0, e=_ms / 1000)


def _fixed(n):
    return lambda d, f: np.full(len(d["t"]), float(n))


def _depth(k):
    def rule(d, f):
        s = np.clip(np.floor(k * f["dep_seen_r"]), 0, 60)
        return np.where(s >= 5, s, 0.0)
    return rule


def _rival(n, size):
    return lambda d, f: np.where(f["pre1"] >= n, float(size), 60.0)


def _thin_or_rival(k, n):
    def rule(d, f):
        s = np.where(f["pre1"] >= n, 30.0, 60.0)
        s = np.minimum(s, np.clip(np.floor(k * f["dep_seen_r"]), 0, 60))
        return np.where(s >= 5, s, 0.0)
    return rule


SIZE = {"s20": _fixed(20), "s40": _fixed(40), "s100": _fixed(100),
        "dk0.5": _depth(0.5), "dk1": _depth(1.0), "dk2": _depth(2.0),
        "rv1_30": _rival(1, 30), "rv1_0": _rival(1, 0), "rv3_30": _rival(3, 30), "rv3_0": _rival(3, 0),
        "dk1_rv1": _thin_or_rival(1.0, 1)}
SIZE_FILLS = ("base", "comp", "e+25")
LIMIT = {"sl0": 0.0, "sl1": 0.01}


SWEEP = {f"s{n}": _fixed(n) for n in (100, 150, 200, 300)}   # sweep of the size winner


def _edge(k, lo, hi):
    """shares = k x predicted value (per share, $), clipped to [lo, hi]: 2000 x 0.03 = 60 sh."""
    return lambda d, f: np.clip(np.round(k * np.nan_to_num(d["edge"], nan=0.0)), lo, hi)


EDGE = {"ek2000_30_200": _edge(2000, 30, 200), "ek2000_60_200": _edge(2000, 60, 200),
        "ek3000_60_300": _edge(3000, 60, 300), "ek1500_40_150": _edge(1500, 40, 150)}
EDGE2 = {"ek3000_60_200": _edge(3000, 60, 200), "ek4000_60_400": _edge(4000, 60, 400),
         "ek5000_60_500": _edge(5000, 60, 500), "ek3000_100_300": _edge(3000, 100, 300)}
RACE_FILLS = ("comp", "e+10", "e+25", "e-25")
VLIM_FILLS = ("base", "e+25", "comp", "e-25")


def scenarios(kind: str = "main"):
    """[(name, fill kwargs (+ slip for a limit rule), size rule or None)]"""
    if kind in ("sweep", "edge", "edge2"):
        rules = {"sweep": SWEEP, "edge": EDGE, "edge2": EDGE2}[kind]
        return [(f"{sk}@{fk}", FILL[fk], rule) for fk in SIZE_FILLS for sk, rule in rules.items()]
    if kind == "race":
        return [(k, FILL[k], None) for k in RACE_FILLS]
    if kind == "vlim":
        from .vlim import VLIM
        return [(f"{rk}@{fk}", dict(FILL[fk], lim=lf) if lf else FILL[fk], sz)
                for fk in VLIM_FILLS for rk, (lf, sz) in VLIM.items()]
    out = [(k, v, None) for k, v in FILL.items()]
    for fk in SIZE_FILLS:
        out += [(f"{sk}@{fk}", FILL[fk], rule) for sk, rule in SIZE.items()]
        out += [(f"{lk}@{fk}", dict(FILL[fk], slip=v), None) for lk, v in LIMIT.items()]
    return out
