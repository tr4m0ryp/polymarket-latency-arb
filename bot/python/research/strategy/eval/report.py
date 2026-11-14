"""Held-out results table: every final arm x L on the test markets, the leaders' actual
fills on the same markets (arm c), and paired differences against their rule.

    python3 -m research.strategy.eval.report --tag final [--split test] [--L 0,50,100,150]

Writes data/out/strategy/heldout-<tag>-<split>.csv and .md."""
from __future__ import annotations

import argparse

import numpy as np
import pandas as pd

from .. import OUT
from .metrics import paired, table
from .score import load

COLS = ["arm", "L", "fills_day", "usd_day", "net_day", "net_lo", "net_hi", "c_per_usd",
        "mk10_c", "win", "max_dd", "net_total"]


def markdown(df: pd.DataFrame) -> str:
    head = "| " + " | ".join(df.columns) + " |\n|" + "---|" * len(df.columns) + "\n"
    return head + "".join("| " + " | ".join(str(v) for v in r) + " |\n" for r in df.itertuples(index=False))


def leaders(markets: np.ndarray) -> pd.DataFrame:
    f = pd.read_pickle(OUT / "fills-leaders.pkl")
    f = f[f["m"].isin(markets)].assign(n=1, mk3v=np.nan)
    if "mk10v" not in f:
        f["mk10v"] = np.nan
    a = f.groupby(["arm", "L", "m"]).agg(
        n=("n", "sum"), won_n=("won", "sum"), cost=("cost", "sum"), fee=("fee", "sum"),
        pnl=("pnl", "sum"), end=("end", "first"), mk3v=("mk3v", "sum"),
        mk10v=("mk10v", lambda x: x.sum(min_count=1))).reset_index()
    t = table(a, markets).assign(mk3_c=np.nan)
    if a["mk10v"].isna().all():
        t["mk10_c"] = np.nan
    return t


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="final")
    ap.add_argument("--split", default="test")
    ap.add_argument("--L", default="0,50,100,150")
    a = ap.parse_args()
    agg, markets = load(a.tag, a.split)
    Ls = [int(x) for x in a.L.split(",")]
    t = table(agg[agg["L"].isin(Ls)], markets)
    t = pd.concat([t, leaders(markets)], ignore_index=True)
    rows = []
    for L in Ls:
        base = agg[(agg["arm"] == "theirs_spot") & (agg["L"] == L)]
        for arm, g in agg[agg["L"] == L].groupby("arm"):
            rows.append({"arm": arm, "L": L, **{f"vs_theirs_{k}": v for k, v in
                                                 paired(g, base, markets).items()}})
    t = t.merge(pd.DataFrame(rows), on=["arm", "L"], how="left")
    t["hours"] = len(markets) / 12
    t.to_csv(OUT / f"heldout-{a.tag}-{a.split}.csv", index=False)
    md = t[COLS + ["vs_theirs_diff_day", "vs_theirs_lo", "vs_theirs_hi"]].round(1)
    (OUT / f"heldout-{a.tag}-{a.split}.md").write_text(markdown(md))
    pd.set_option("display.width", 250)
    print(f"{a.split}: {len(markets)} markets ({len(markets) / 12:.1f} h)")
    print(md.to_string(index=False))


if __name__ == "__main__":
    main()
