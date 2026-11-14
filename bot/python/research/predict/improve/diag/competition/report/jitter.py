"""Latency-jitter fill models: the race curve averaged over a distribution of match-time
errors e instead of one fixed e. Per-market value = sum_k w_k x value at e_k (trapezoid
weights of a uniform density on the e grid the simulator ran), so paired gains vs micf under
the same mixture keep the market bootstrap.

  sym25  e ~ U(-25, +25) ms   (unbiased L, 25 ms of jitter either way)
  late50 e ~ U(0, +50) ms     (Dublin is systematically late by up to 50 ms)
  late25 e ~ U(0, +25) ms"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .boot import DAY, arm_cols, day_ci, markets, ratio_ci
from .whatif import _paired

GRID = {"sym25": (-25, 0, 10, 25), "late25": (0, 10, 25), "late50": (0, 10, 25, 50)}


def weights(es) -> np.ndarray:
    """Trapezoid weights of a uniform density over [es[0], es[-1]] on the grid es."""
    es = np.asarray(es, float)
    w = np.zeros(len(es))
    gaps = np.diff(es)
    w[:-1] += gaps / 2
    w[1:] += gaps / 2
    return w / w.sum()


def _scen(e: int) -> str:
    return "base" if e == 0 else f"e{e:+d}"


def mix(o, arm, L, mk, name) -> dict:
    es = GRID[name]
    w = weights(es)
    parts = [arm_cols(o, arm, L, _scen(e), mk) for e in es]
    return {"mk": sum(wk * p["mk"] for wk, p in zip(w, parts)),
            "cost": sum(wk * p["cost"] for wk, p in zip(w, parts))}


def table(o: pd.DataFrame, ids: dict, arms, L: int, groups=("unseen", "quiet", "busy")) -> pd.DataFrame:
    rows = []
    for g in groups:
        mk = markets(ids, g)
        for name in ("base",) + tuple(GRID):
            m0 = arm_cols(o, "micf", L, "base", mk) if name == "base" else mix(o, "micf", L, mk, name)
            for arm in arms:
                a = arm_cols(o, arm, L, "base", mk) if name == "base" else mix(o, arm, L, mk, name)
                r = {"group": g, "jitter": name, "arm": arm, "L": L,
                     "mk10 c/$": ratio_ci(a["mk"], a["cost"]), "mk10 $/day": day_ci(a["mk"])}
                if arm != "micf":
                    r["gain vs micf $/day"] = _paired(a["mk"], m0["mk"])
                rows.append(r)
    return pd.DataFrame(rows)
