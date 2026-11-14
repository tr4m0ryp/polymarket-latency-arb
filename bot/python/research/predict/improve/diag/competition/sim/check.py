"""Check that the instrumented base fill reproduces the frozen simulator's fills (same arm, L,
market, decision time: shares, cost, 10 s markout), per window.

    python3 -m research.predict.improve.diag.competition.sim.check --win ext"""
from __future__ import annotations

import argparse

import numpy as np
import pandas as pd

from ...... import predict
from .. import CACHE, WINDOWS


def compare(win: str, sfx: str = "") -> pd.DataFrame:
    o = pd.read_pickle(CACHE / f"orders-{win}{sfx}.pkl")
    o = o[o["base_got"] > 0]
    ref = pd.read_pickle(predict.OUT / f"fills-{WINDOWS[win]}.pkl")
    ref = ref[ref["arm"].isin(o["arm"].unique()) & ref["m"].isin(o["m"].unique())]
    key = ["arm", "L", "m", "t"]
    o, ref = o.assign(t=o["t"].round(6)), ref.assign(t=ref["t"].round(6))
    j = o.merge(ref, on=key, how="outer", suffixes=("", "_ref"), indicator=True)
    rows = []
    for (arm, L), g in j.groupby(["arm", "L"]):
        both = g[g["_merge"] == "both"]
        rows.append({"arm": arm, "L": L, "ours": int((g["_merge"] != "right_only").sum()),
                     "frozen": int((g["_merge"] != "left_only").sum()), "matched": len(both),
                     "max_dshares": float(np.abs(both["base_got"] - both["shares"]).max()) if len(both) else np.nan,
                     "max_dmk10": float(np.abs(both["base_mk10v"] - both["mk10v"]).max()) if len(both) else np.nan,
                     "mk10_ours": float(g["base_mk10v"].sum()), "mk10_frozen": float(g["mk10v"].sum())})
    return pd.DataFrame(rows)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--win", default="ext")
    ap.add_argument("--sfx", default="")
    a = ap.parse_args()
    pd.set_option("display.width", 200)
    for w in a.win.split(","):
        print(w)
        print(compare(w, a.sfx).to_string(index=False))


if __name__ == "__main__":
    main()
