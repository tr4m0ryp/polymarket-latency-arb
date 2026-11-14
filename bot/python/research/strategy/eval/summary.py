"""The report tables: every held-out arm (eval/arms/final.py and final2.py) and the leaders'
actual fills on the test markets, with paired differences against the rebuilt baseline
(theirs_micro, the leaders' microprice trigger) at the same L.

    python3 -m research.strategy.eval.summary [--split test] [--suffix _h25|_comp|_x0]

Writes data/out/strategy/heldout-<split><suffix>.csv and .md (suffix = a sensitivity run)."""
from __future__ import annotations

import argparse

import pandas as pd

from .. import OUT
from .metrics import paired, table
from .report import leaders, markdown
from .score import load

LABEL = {"theirs_micro": "(a) their rule, rebuilt: perp+spot microprice trigger",
         "theirs_spot": "(a') their rule, first read: last 3 s spot move",
         "theirs_perp": "(b) their rule on the perp mid",
         "leaderA_all": "(c) leader A actual fills", "leaderB_all": "(c) leader B actual fills",
         "leaderA_taker": "(c) leader A actual taker fills",
         "leaderB_taker": "(c) leader B actual taker fills"}
COLS = ["arm", "L", "fills_day", "usd_day", "net_day", "net_lo", "net_hi", "c_per_usd", "mk10_c",
        "win", "max_dd"]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", default="test")
    ap.add_argument("--suffix", default="")
    a = ap.parse_args()
    a1, mk = load(f"final{a.suffix}", a.split)
    a2, mk2 = load(f"final2{a.suffix}", a.split)
    a2 = a2[~a2["arm"].isin(["theirs_spot", "theirs_perp"])]  # kept from the v1 run
    agg = pd.concat([a1, a2], ignore_index=True)
    t = pd.concat([table(agg, mk), leaders(mk)], ignore_index=True)
    rows = []
    for L, g in agg.groupby("L"):
        base = g[g["arm"] == "theirs_micro"]
        if not len(base):
            continue
        for arm, x in g.groupby("arm"):
            rows.append({"arm": arm, "L": L,
                         **{f"vs_a_{k}": v for k, v in paired(x, base, mk).items()},
                         **{f"vs_a_mk10_{k}": v for k, v in paired(x, base, mk, col="mk10v").items()}})
    t = t.merge(pd.DataFrame(rows), on=["arm", "L"], how="left")
    t["label"] = t["arm"].map(LABEL).fillna("")
    t["hours"] = len(mk) / 12
    name = f"heldout-{a.split}{a.suffix}"
    t.to_csv(OUT / f"{name}.csv", index=False)
    md = t[COLS + ["vs_a_diff_day", "vs_a_lo", "vs_a_hi", "vs_a_mk10_diff_day", "vs_a_mk10_lo",
                   "vs_a_mk10_hi"]].round(1)
    (OUT / f"{name}.md").write_text(f"{a.split}: {len(mk)} markets ({len(mk) / 12:.1f} h), "
                                               f"same markets in both runs: {set(mk) == set(mk2)}\n\n"
                                               + markdown(md))
    pd.set_option("display.width", 260)
    print(f"{a.split}: {len(mk)} markets")
    print(md.to_string(index=False))


if __name__ == "__main__":
    main()
