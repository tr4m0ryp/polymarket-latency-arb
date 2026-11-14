"""Report-only runs around the stage-2 winner (never used to choose it).

Pools: selection hours (v1, the choice pool), test hours for v1 and v1h_G_h250x_L0 (primary
model), holds old / new / fast50, all 48 h for 7 d projections. Rows: winner, runner-ups, the
best fixed-size point, the uncapped live config, the winner from $26, ablation (each cap off),
side policies, redeem 1 h.

    PYTHONPATH=. python3 -m research.bankroll.search.report -> data/out/bankroll/report.csv"""
from __future__ import annotations

import json
from dataclasses import replace

import pandas as pd

from .. import OUT
from ..sim import Caps, Pool_
from ..sim.caps import INF
from .evaluate import evaluate
from .final import caps_of

POOLS = [("v1_frozen", "old", "selection"), ("v1_frozen", "old", "test"), ("G_h250+x", "old", "test"),
         ("G_h250+x", "new", "test"), ("G_h250+x", "fast50", "test"), ("v1_frozen", "new", "test"),
         ("G_h250+x", "old", "selection"), ("G_h250+x", "old", "all")]
CORE = POOLS[:3] + [POOLS[3], POOLS[7]]
LIVE = Caps(size=60.0, fit=0)


def ablation(w: Caps) -> list[tuple[str, Caps]]:
    out = [("winner", w), ("sizing: 5 sh fixed", replace(w, size_mode=0, size=5.0)),
           ("sizing: 60 sh fixed", replace(w, size_mode=0, size=60.0)),
           ("sizing: fraction x2", replace(w, size=w.size * 2)),
           ("no market cap", replace(w, market_frac=INF)), ("no open cap", replace(w, open_frac=INF)),
           ("no side rule", replace(w, side_policy=0)), ("no fills cap", replace(w, max_fills=INF)),
           ("no day drawdown stop", replace(w, dd_stop=INF)), ("no floor halt", replace(w, floor=INF)),
           ("no min edge", replace(w, min_edge=0.0)), ("all caps off, same sizing",
            replace(w, market_frac=INF, open_frac=INF, side_policy=0, max_fills=INF, dd_stop=INF, floor=INF)),
           ("redeem 1 h (manual claim)", replace(w, redeem_s=3600.0))]
    out += [(f"side policy {p}", replace(w, side_policy=p)) for p in range(4)]
    return out


def main():
    f2 = pd.read_csv(OUT / "final2.csv")
    pick = json.loads((OUT / "final2.json").read_text())
    feas = f2[f2["feasible"]]
    comp = feas[feas["size_mode"] > 0]
    win = caps_of(comp.iloc[0])
    runners = [caps_of(r) for _, r in comp.iloc[1:5].iterrows()]
    fixed = [caps_of(r) for _, r in feas[feas["size_mode"] == 0].head(1).iterrows()]
    pools = {p: Pool_(*p) for p in POOLS}
    rows = []

    def run(tag, c, pl, start=100.0):
        r = evaluate(pools[pl], c, start=start)
        rows.append({"tag": tag, "label": c.label(), "pool": "/".join(pl), "start": start, **c.dict(), **r})

    for tag, c in [("winner", win)] + [(f"runner-up {i + 1}", c) for i, c in enumerate(runners)] \
            + [("best fixed size", c) for c in fixed] + [("live config (60 sh, no caps)", LIVE)]:
        for pl in POOLS:
            run(tag, c, pl)
    for pl in CORE:
        run("winner from $26", win, pl, start=26.0)
    for tag, c in ablation(win):
        for pl in (POOLS[0], POOLS[2]):
            run("abl: " + tag, c, pl)
    for pl in (POOLS[0], POOLS[2]):
        run("natural: 5 sh, no caps", Caps(size=5.0), pl)
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "report.csv", index=False)
    print(pick, win.label())


if __name__ == "__main__":
    main()
