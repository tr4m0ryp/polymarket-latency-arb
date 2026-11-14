"""Market sets the harness reports: each evaluated window, the fold's pooled evaluation, the
busy hours, and the cross-validated pool over both folds.

Busy hours, fixed before any candidate: (1) `busy15` = 2026-10-11 15:00-16:00 UTC starts,
the hour where the retired primary lost -11 c/$; (2) `busyQ` = clock hours whose mean count
of leaders'-trigger-sized perp microprice moves per market (|p_dmic0.1| >= 0.002 bp, the
report's busy signature) is in the top quartile of all allowed hours. Label-free, so it can
use every allowed window."""
from __future__ import annotations

import numpy as np
import pandas as pd

from .. import windows as W


def hours(act: pd.DataFrame) -> pd.DataFrame:
    """Per clock hour (market start): markets and mean trigger moves per market."""
    a = act.assign(hour=(act["start"] // 3600).astype(int))
    return a.groupby("hour").agg(mkts=("m", "size"), trig=("n_trig", "mean")).reset_index()


def busy_markets(act: pd.DataFrame, q: float = 0.75) -> set[int]:
    h = hours(act)
    thr = np.quantile(h["trig"], q)
    busy = set(h.loc[h["trig"] >= thr, "hour"])
    return set(act.loc[(act["start"] // 3600).astype(int).isin(busy), "m"].astype(int))


def build(act: pd.DataFrame) -> dict[str, list[int]]:
    """Ordered set name -> sorted market ids."""
    busy = busy_markets(act)
    s15 = {i for w in W.WINDOWS for i, s in W.starts(w).items() if W.BUSY15[0] <= s < W.BUSY15[1]}
    out = {}
    for f, (_, ev) in W.FOLDS.items():
        ids = sorted(i for w in ev for i in W.ids(w))
        for w in ev:
            out[f"{f}:{w}"] = W.ids(w)
        out[f"{f}:eval"] = ids
        out[f"{f}:busy15"] = sorted(set(ids) & s15)
        out[f"{f}:busyQ"] = sorted(set(ids) & busy)
    every = W.all_eval_ids()
    out["CV:all"] = every
    out["CV:busyQ"] = sorted(set(every) & busy)
    out["unseen251"] = sorted(i for w in ("dev3", "test3r1", "ext") for i in W.ids(w))
    return {k: v for k, v in out.items() if v}
