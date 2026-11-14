"""Score simulated fills like research/strategy/eval/sim.py: hold to resolution at our 0%
tier, plus the 3 s and 10 s venue-mid markouts; aggregate per arm x L x market."""
from __future__ import annotations

import numpy as np
import pandas as pd

AGG = dict(n=("shares", "size"), won_n=("won", "sum"), shares=("shares", "sum"),
           cost=("cost", "sum"), fee=("fee", "sum"), pnl=("pnl", "sum"), mk3v=("mk3v", "sum"),
           mk10v=("mk10v", "sum"))


def score(f: pd.DataFrame, book, outcome: float) -> pd.DataFrame:
    won = np.where(f["side"] > 0, outcome, 1 - outcome)
    f["won"] = won
    f["pnl"] = f["shares"] * won - f["cost"] - f["fee"]
    for h in (3, 10):
        mid = book.mid(book.g_ceil(f["tf"].to_numpy() + h))
        f[f"mk{h}"] = np.where(f["side"] > 0, mid, 1 - mid)
        f[f"mk{h}v"] = f["shares"] * f[f"mk{h}"].fillna(f["won"]) - f["cost"] - f["fee"]
    return f


def aggregate(f: pd.DataFrame) -> pd.DataFrame:
    return f.groupby(["arm", "L", "m", "end"]).agg(**AGG).reset_index()
