"""Pick the regime-margin arm on select hours only, before the unseen windows are simulated,
and record the pick (OUT/rm_choice.json, with the UTC time it was made).

Rule: per L, among the rm_* arms and the frozen m3, the highest 10 s markout $/day on select
with markout c/$ > 0. Reads OUT/sim/agg-rm-select.pkl only.

    python3 -m research.predict.improve.diag.calibration.recal.choose"""
from __future__ import annotations

import json
import sys
import time

import pandas as pd

from ...... import predict
from ......strategy.eval.metrics import table
from .. import OUT
from ..safe import check, start_of


def main() -> None:
    dst = OUT / "rm_choice.json"
    if dst.exists() and "--force" not in sys.argv:
        print("rm_choice.json exists; the pick is a provenance record (pass --force to remake)")
        return
    agg = pd.read_pickle(OUT / "sim" / "agg-rm-select.pkl")
    mk = pd.read_csv(predict.OUT / "markets-sel1.csv")["m"].to_numpy()
    check(start_of(mk))
    t = table(agg, mk)
    t["mk10_day"] = [agg[(agg["arm"] == a) & (agg["L"] == L)]["mk10v"].sum() / (len(mk) / 288)
                     for a, L in zip(t["arm"], t["L"])]
    t = t[t["arm"].str.match(r"vt_v1_(rm_|m3$)")]
    pick = {}
    for L, g in t.groupby("L"):
        g = g[g["mk10_c"] > 0].sort_values("mk10_day", ascending=False)
        pick[int(L)] = {"arm": g["arm"].iloc[0], "select_mk10_day": float(g["mk10_day"].iloc[0]),
                        "table": g[["arm", "fills_day", "mk10_c", "mk10_day"]].round(2).to_dict("records")}
    out = {"made_utc": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()), "rule": __doc__.split("\n\n")[1],
           "pick": pick}
    dst.write_text(json.dumps(out, indent=1))
    print(json.dumps({L: v["arm"] for L, v in pick.items()}))


if __name__ == "__main__":
    main()
