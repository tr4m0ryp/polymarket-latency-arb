"""Score a predict simulation tag: metrics per arm x L (strategy eval/metrics.py: fills, $ /
day, market-bootstrap CI, c/$, 10 s markout, drawdown), the leaders' actual fills on the same
markets, and paired 10 s markout gains vs micf.

    python3 -m research.predict.sim.score --tag sel1 --seg select [--leaders]"""
from __future__ import annotations

import argparse

import pandas as pd

from .. import OUT
from ...strategy.eval.metrics import paired, table
from ..report.md import md

COLS = ["arm", "L", "fills_day", "net_day", "net_lo", "net_hi", "c_per_usd", "mk10_c", "mk10_day",
        "win", "max_dd"]


def scored(tag: str, leaders: str | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    agg = pd.read_pickle(OUT / f"agg-{tag}.pkl")
    mk = pd.read_csv(OUT / f"markets-{tag}.csv")["m"].to_numpy()
    if leaders:
        from .leaders import agg as lagg
        la = lagg(leaders)
        agg = pd.concat([agg, la[la["m"].isin(mk)]], ignore_index=True)
    t = table(agg, mk)
    days = len(mk) / 288
    mk10 = agg.groupby(["arm", "L"])["mk10v"].sum() / days
    t["mk10_day"] = [mk10.get((a, L)) for a, L in zip(t["arm"], t["L"])]
    t = t.rename(columns={"mk10_c": "mk10_c"})
    rows = []
    for (arm, L), g in agg.groupby(["arm", "L"]):
        base = agg[(agg["arm"] == "micf") & (agg["L"] == L)]
        if arm == "micf" or not len(base) or arm.startswith("leader"):
            continue
        p = paired(g, base, mk, col="mk10v")
        rows.append({"arm": arm, "L": L, "mk10_gain_day": p["diff_day"], "lo": p["lo"], "hi": p["hi"]})
    return t, pd.DataFrame(rows)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", required=True)
    ap.add_argument("--leaders", default=None, help="segment of the leaders' fills to add")
    ap.add_argument("--L", type=int, default=None)
    a = ap.parse_args()
    t, p = scored(a.tag, a.leaders)
    t.to_csv(OUT / f"score-{a.tag}.csv", index=False)
    p.to_csv(OUT / f"paired-{a.tag}.csv", index=False)
    if a.L is not None:
        t = t[t["L"] == a.L]
    pd.set_option("display.width", 250)
    print(md(t[COLS].sort_values(["L", "mk10_day"], ascending=[True, False]), 2))
    print(md(p.sort_values(["L", "mk10_gain_day"], ascending=[True, False]), 1))


if __name__ == "__main__":
    main()
