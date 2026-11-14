"""Score a simulated sweep: metrics per arm x L on one split (run-2 markets only, so spot
and perp arms share the same market denominator).

    python3 -m research.strategy.eval.score --tag s1 [--split train] [--sort net_day]
        [--L 100] [--top 30] [--like fair_]

Writes data/out/strategy/score-<tag>-<split>.csv."""
from __future__ import annotations

import argparse

import pandas as pd

from .. import OUT
from .metrics import table
from .prep import RUN2


def load(tag: str, split: str):
    agg = pd.read_pickle(OUT / f"agg-{tag}.pkl")
    mk = pd.read_csv(OUT / f"markets-{tag}.csv")
    mk = mk[(mk["split"] == split) & (mk["start"] >= RUN2)]
    return agg[agg["m"].isin(mk["m"])], mk["m"].to_numpy()


def scored(tag: str, split: str) -> pd.DataFrame:
    agg, markets = load(tag, split)
    t = table(agg, markets)
    t.to_csv(OUT / f"score-{tag}-{split}.csv", index=False)
    return t


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", required=True)
    ap.add_argument("--split", default="train")
    ap.add_argument("--sort", default="net_day")
    ap.add_argument("--L", type=int, default=None)
    ap.add_argument("--top", type=int, default=30)
    ap.add_argument("--like", default=None)
    a = ap.parse_args()
    t = scored(a.tag, a.split)
    if a.L is not None:
        t = t[t["L"] == a.L]
    if a.like:
        t = t[t["arm"].str.contains(a.like)]
    cols = ["arm", "L", "fills_day", "usd_day", "net_day", "net_lo", "net_hi", "c_per_usd",
            "mk3_c", "win", "max_dd", "mkts"]
    pd.set_option("display.width", 250)
    print(t.sort_values(a.sort, ascending=False)[cols].head(a.top).round(2).to_string(index=False))
    base = t[t["arm"].str.startswith("theirs")]
    print("\nbaselines\n" + base[cols].round(2).to_string(index=False))


if __name__ == "__main__":
    main()
