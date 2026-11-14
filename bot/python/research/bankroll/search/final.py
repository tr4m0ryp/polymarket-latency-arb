"""Stage 2: finalists from the screen on selection hours (v1_frozen, hold `old`), the winner,
then report-only runs (test hours, both arms, holds, redeem delay, $26 start, ablation, side
policies, the uncapped live config).

    PYTHONPATH=. python3 -m research.bankroll.search.final -> data/out/bankroll/{final,report}.json"""
from __future__ import annotations

import json
from dataclasses import replace

import pandas as pd

from .. import OUT
from ..sim import Caps, Pool_
from ..sim.caps import INF
from .evaluate import evaluate

FIELDS = ("size_mode", "size", "max_sh", "market_frac", "open_frac", "side_policy", "max_fills", "dd_stop",
          "min_edge", "fit", "redeem_s", "floor")


def caps_of(row) -> Caps:
    d = {k: (int(row[k]) if k in ("size_mode", "side_policy", "fit") else float(row[k])) for k in FIELDS if k in row}
    if d.get("floor", 0) != d.get("floor", 0):     # NaN in the pre-amendment screen
        d.pop("floor")
    return Caps(**d)


def finalists(sc: pd.DataFrame, n: int = 100) -> list[Caps]:
    ok = sc[sc["p_ruin"] <= 0.08].sort_values(["med_log", "p10_log"], ascending=False)
    ok = ok.drop_duplicates(["med_log", "p10_log", "fills_h"])        # caps that never bind: first in grid
    top = pd.concat([ok.head(n), ok[ok["size_mode"] > 0].head(n)]).drop_duplicates("label")
    return [caps_of(r) for _, r in top.iterrows()]


def main():
    sc = pd.read_csv(OUT / "screen.csv")
    pool = Pool_("v1_frozen", "old", "selection")
    rows = []
    for c in finalists(sc):
        rows.append({"label": c.label(), **c.dict(), **evaluate(pool, c)})
        print(rows[-1]["label"], round(rows[-1]["b_med_log"], 3), rows[-1]["feasible"], flush=True)
    df = pd.DataFrame(rows).sort_values(["b_med_log", "b_p10_log"], ascending=False)
    df.to_csv(OUT / "final.csv", index=False)
    feas = df[df["feasible"]]
    comp = feas[feas["size_mode"] > 0]
    pick = {"overall": feas.iloc[0]["label"] if len(feas) else None,
            "compounding": comp.iloc[0]["label"] if len(comp) else None}
    (OUT / "final.json").write_text(json.dumps(pick, indent=1))
    print(pick)


if __name__ == "__main__":
    main()
