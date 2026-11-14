"""Amendment 2 (prereg.json): floors added; stage 1 for the new floors, stage 1b (7 d screen),
stage 2 on the 7 d-screened points. Selection hours, v1_frozen, hold `old`.

    PYTHONPATH=. python3 -m research.bankroll.search.screen2 -> screen2.csv, screen7.csv, final2.csv"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from .. import OUT, START
from ..sim import Pool_, bootstrap, encode, simulate
from .evaluate import evaluate
from .final import FIELDS, caps_of
from .prereg import FLOOR, grid
from .stats import summary


def stage1(pool) -> pd.DataFrame:
    p = OUT / "screen2.csv"
    if p.exists():
        return pd.read_csv(p)
    seqs = bootstrap(pool.n_markets, 200, 288, seed=1)
    rows = []
    for c in grid(FLOOR[1:]):
        s = summary(simulate(pool, seqs, encode(c), START, seed=1), START, 24.0, 50.0)
        rows.append({**c.dict(), "label": c.label(), **s})
    df = pd.concat([pd.read_csv(OUT / "screen.csv"), pd.DataFrame(rows)], ignore_index=True)
    df["floor"] = df["floor"].fillna(1e18)
    df.to_csv(p, index=False)
    return df


def stage1b(pool, sc: pd.DataFrame) -> pd.DataFrame:
    p = OUT / "screen7.csv"
    if p.exists():
        return pd.read_csv(p)
    ok = sc[sc["p_ruin"] <= 0.08].sort_values(["med_log", "p10_log"], ascending=False)
    ok = ok.drop_duplicates(["floor", "med_log", "p10_log", "fills_h"])
    top = ok.groupby("floor", group_keys=False).head(2000)
    seqs = bootstrap(pool.n_markets, 200, 288 * 7, seed=5)
    p7 = []
    for _, r in top.iterrows():
        s = summary(simulate(pool, seqs, encode(caps_of(r)), START, seed=5), START, 168.0, 25.0)
        p7.append((s["p_ruin"], s["median"], s["p10"]))
    top = top.copy()
    top["p7_ruin"], top["med7"], top["p10_7"] = np.array(p7).T
    top.to_csv(p, index=False)
    return top


def main():
    pool = Pool_("v1_frozen", "old", "selection")
    sc = stage1(pool)
    s7 = stage1b(pool, sc)
    cand = s7[s7["p7_ruin"] <= 0.02].sort_values(["med_log", "p10_log"], ascending=False)
    top = pd.concat([cand.head(100), cand[cand["size_mode"] > 0].head(100)]).drop_duplicates("label")
    rows = []
    for _, r in top.iterrows():
        c = caps_of(r)
        rows.append({"label": c.label(), **c.dict(), **evaluate(pool, c)})
        print(rows[-1]["label"], round(rows[-1]["b_med_log"], 3), rows[-1]["feasible"], flush=True)
    df = pd.DataFrame(rows).sort_values(["b_med_log", "b_p10_log"], ascending=False)
    df.to_csv(OUT / "final2.csv", index=False)
    feas = df[df["feasible"]]
    comp = feas[feas["size_mode"] > 0]
    pick = {"compounding": comp.iloc[0]["label"] if len(comp) else None,
            "fixed_best": feas[feas["size_mode"] == 0].iloc[0]["label"] if (feas["size_mode"] == 0).any() else None,
            "n_feasible": int(len(feas)), "n_candidates": int(len(df))}
    (OUT / "final2.json").write_text(json.dumps(pick, indent=1))
    print(pick)


if __name__ == "__main__":
    main()
