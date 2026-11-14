"""Anatomy of the losing fills (10 s markout < 0, base fills): how much of the loss is the
hold (we paid above the price we saw because rivals or makers cleared it) and how much is the
book moving against us after the match, and whether losers were crowded by rivals.

Per filled order: slip = VWAP - seen ask (per share); markout at the seen price = markout +
slip x shares (the fee difference is ignored, < 0.1 c). mk1 / mk3 / mk10 = the markout path
1, 3, 10 s after the match, per share."""
from __future__ import annotations

import numpy as np
import pandas as pd

from .boot import markets, per_market, ratio_ci


def anatomy(o: pd.DataFrame, ids: dict, arms, groups=("quiet", "busy")) -> pd.DataFrame:
    f = o[o["base_got"] > 0].copy()
    f["slip_v"] = f["base_cost"] - f["base_got"] * f["seen"]
    rows = []
    for g in groups:
        mk = markets(ids, g)
        for arm, L in arms:
            a = f[(f["arm"] == arm) & (f["L"] == L) & f["m"].isin(mk)]
            for lab, s in (("losers", a[a["base_mk10v"] < 0]), ("winners", a[a["base_mk10v"] >= 0])):
                sh = s["base_got"].sum()
                c = ratio_ci(per_market(s, "base_mk10v", mk), per_market(s, "base_cost", mk))
                rows.append({
                    "regime": g, "arm": arm, "L": L, "fills": lab, "n": len(s),
                    "mk10 $": s["base_mk10v"].sum(), "mk10 c/$": c[0],
                    "hold slip $": -s["slip_v"].sum(),
                    "slip share of loss": (s["slip_v"].sum() / -s["base_mk10v"].sum()) if lab == "losers" else np.nan,
                    "mk1 c/sh": 100 * s["base_mk1v"].sum() / sh, "mk3 c/sh": 100 * s["base_mk3v"].sum() / sh,
                    "mk10 c/sh": 100 * s["base_mk10v"].sum() / sh,
                    "rival in hold (our levels)": (s["hold_n_lim"] > 0).mean(),
                    "taken <= 50 ms after": s["tr50"].sum() / sh,
                    "e+25 keeps $": s["e+25_mk10v"].sum(), "comp keeps $": s["comp_mk10v"].sum()})
    return pd.DataFrame(rows)
