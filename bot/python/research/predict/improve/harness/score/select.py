"""Variant choice on a fold's choose windows (fixed rule, declared by the candidate before it
runs): among variants with 10 s markout > 0 and >= 100 fills/day at SELECT_L (base fills),
take the highest criterion on the pooled choose windows:

    gain : paired 10 s markout $/day gain over the frozen vt_v1_m0.03_any (default)
    lcb  : the 2.5% bound of that gain (robust choice: penalises fat-tailed variants)
    mk   : 10 s markout $/day

If no variant meets the floor, the best criterion wins anyway and the choice is flagged."""
from __future__ import annotations

import pandas as pd

CRITERIA = {"gain": "g_vt", "lcb": "g_vt_lo", "mk": "mk10_day"}


def choose(tab: pd.DataFrame, criterion: str = "gain") -> tuple[str, dict]:
    col = CRITERIA[criterion]
    ok = (tab["mk10_c"] > 0) & (tab["fills_day"] >= 100)
    pool = tab[ok] if ok.any() else tab
    best = pool.sort_values([col, "arm"], ascending=[False, True]).iloc[0]
    return str(best["arm"]), {"criterion": criterion, "value": float(best[col]),
                              "met_floor": bool(ok.any()), "variants": int(len(tab))}
