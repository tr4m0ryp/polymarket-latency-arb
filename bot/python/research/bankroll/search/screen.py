"""Stage 1: every pre-registered grid point on selection hours, v1_frozen, hold `old`,
200 bootstrap 24 h paths (same paths for every point).

    PYTHONPATH=. python3 -m research.bankroll.search.screen -> data/out/bankroll/screen.csv"""
from __future__ import annotations

import json
import time

import numpy as np
import pandas as pd

from .. import OUT, START
from ..sim import Pool_, bootstrap, encode, simulate
from .prereg import grid
from .stats import summary

PATHS = 200


def main():
    assert (OUT / "prereg.json").exists(), "freeze the grid first (search.prereg)"
    pool = Pool_("v1_frozen", "old", "selection")
    seqs = bootstrap(pool.n_markets, PATHS, 288, seed=1)
    g = grid()
    rows, t0 = [], time.time()
    for n, c in enumerate(g):
        s = summary(simulate(pool, seqs, encode(c), START, seed=1), START, 24.0, 50.0)
        rows.append({**c.dict(), "label": c.label(), **s})
        if n % 2000 == 0:
            print(n, f"{time.time() - t0:.0f}s", flush=True)
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "screen.csv", index=False)
    plan = json.loads((OUT / "prereg.json").read_text())
    ok = df[df["p_ruin"] <= 0.08].sort_values(["med_log", "p10_log"], ascending=False)
    print(ok.head(20)[["label", "med_log", "p10_log", "median", "p10", "p_ruin", "fills_h"]].to_string())
    print("feasible", len(ok), "of", len(df), "frozen", plan["frozen_utc"])


if __name__ == "__main__":
    main()
