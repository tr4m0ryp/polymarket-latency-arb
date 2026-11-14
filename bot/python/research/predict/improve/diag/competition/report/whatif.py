"""What-if tables: the arms under competition-aware fill models (incl. the race curve) and
under size rules, each with market-bootstrap CIs and paired gains."""
from __future__ import annotations

import numpy as np
import pandas as pd

from .boot import DAY, _idx, arm_cols, day_ci, markets, ratio_ci


def _paired(a: np.ndarray, b: np.ndarray, seed: int = 2) -> tuple[float, float, float, float]:
    d = a - b
    days = len(d) / DAY
    s = d[_idx(len(d), seed)].sum(1)
    return d.sum() / days, np.percentile(s, 2.5) / days, np.percentile(s, 97.5) / days, float((s <= 0).mean())


def fill_models(o, ids, arms, L, scens, groups=("unseen", "quiet", "busy")) -> pd.DataFrame:
    """Each arm under each fill model: markout c/$, $/day, paired gain vs micf in the same model."""
    rows = []
    for g in groups:
        mk = markets(ids, g)
        for sc in scens:
            base = arm_cols(o, "micf", L, sc, mk)
            for arm in arms:
                a = arm_cols(o, arm, L, sc, mk)
                r = {"group": g, "fill model": sc, "arm": arm, "L": L,
                     "fills/day": a["n"] / (len(mk) / DAY), "mk10 c/$": ratio_ci(a["mk"], a["cost"]),
                     "mk10 $/day": day_ci(a["mk"])}
                if arm != "micf" and a["cost"].sum() > 0:
                    r["gain vs micf $/day"] = _paired(a["mk"], base["mk"])
                rows.append(r)
    return pd.DataFrame(rows)


def size_rules(o, ids, arm, L, rules, fills=("base", "comp", "e+25"),
               groups=("select", "quiet", "busy", "unseen")) -> pd.DataFrame:
    """Size rule vs the same arm at 60 sh under the same fill model (paired, same markets)."""
    rows = []
    for g in groups:
        mk = markets(ids, g)
        for fm in fills:
            ref = arm_cols(o, arm, L, fm, mk)
            for rule in ("60",) + tuple(rules):
                sc = fm if rule == "60" else f"{rule}@{fm}"
                a = arm_cols(o, arm, L, sc, mk)
                r = {"group": g, "arm": arm, "L": L, "fill model": fm, "size": rule,
                     "fills/day": a["n"] / (len(mk) / DAY), "sh/fill": a["sh"] / max(a["n"], 1),
                     "mk10 c/$": ratio_ci(a["mk"], a["cost"]), "mk10 $/day": day_ci(a["mk"])}
                if rule != "60":
                    r["vs 60 sh $/day"] = _paired(a["mk"], ref["mk"])
                    m0 = arm_cols(o, "micf", L, fm, mk)
                    r["gain vs micf $/day"] = _paired(a["mk"], m0["mk"])
                rows.append(r)
    return pd.DataFrame(rows)


def race_curve(o, ids, arms, L, es=(-50, -25, 0, 10, 25, 50, 100, 200), groups=("quiet", "busy")) -> pd.DataFrame:
    rows = []
    for g in groups:
        mk = markets(ids, g)
        for arm in arms:
            for e in es:
                sc = "base" if e == 0 else f"e{e:+d}"
                a = arm_cols(o, arm, L, sc, mk)
                rows.append({"group": g, "arm": arm, "e ms": e, "fills/day": a["n"] / (len(mk) / DAY),
                             "sh/fill": a["sh"] / max(a["n"], 1),
                             "mk10 c/$": 100 * a["mk"].sum() / max(a["cost"].sum(), 1e-9),
                             "mk10 $/day": a["mk"].sum() / (len(mk) / DAY)})
    return pd.DataFrame(rows)
