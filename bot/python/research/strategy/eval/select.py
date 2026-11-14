"""Pre-registered selection on TRAINING markets only: per family, the arm with the highest
10 s-markout net $ per day at L = 0 ms (the cheap Dublin host, reports/infra-plan.md; hold
150 ms), among arms whose resolution net is positive on train. The 10 s markout values each
fill at the venue mid 10 s later: far less noisy than resolution over 12 h, and it already
includes the post-burst drift.

    python3 -m research.strategy.eval.select [--v2 | --v3]

Writes data/out/strategy/selection.json (v2 / v3: selection2 / 3.json, family -> arm), .csv."""
from __future__ import annotations

import argparse
import importlib
import json
import re

import pandas as pd

from .. import OUT
from .score import scored


def _size(arm: str) -> float:
    m = re.search(r"_s(\d+)$", arm)
    return float(m.group(1)) if m else 60.0


def _fair(arm: str, imb: bool) -> bool:
    m = re.match(r"fair[kb]?_(pzxi|pzi|pzx|pz|s)_", arm)
    return bool(m) and (m.group(1) in ("pzi", "pzxi")) == imb


FAMILIES = {
    "momentum, tuned known rule (60 sh)": lambda a: a.startswith(("mom_", "zmom_")),
    "fair taker, 60-share clip (invention 1)":
        lambda a: _fair(a, False) and not a.startswith(("fairk", "fairb")) and _size(a) == 60,
    "fair taker, depth-sized (invention 1 + sizing)": lambda a: _fair(a, False),
    "fair taker + perp imbalance (invention 3)": lambda a: _fair(a, True),
    "maker, fair-value quotes (invention 2)": lambda a: a.startswith("mk_"),
    "maker, book-anchored with perp pulls (invention 2b)": lambda a: a.startswith("mkb_"),
}
FAMILIES2 = {  # v2 tables (microprice candidates), selected separately into selection2.json
    "microprice taker, selective (60 sh)": lambda a: a.startswith("mic_"),
    "microprice trigger + fair-value filter": lambda a: a.startswith("micf_"),
    "fair taker refit on v2 candidates": lambda a: a.startswith("fair_pz2_"),
    "fair taker + microprice lag buckets": lambda a: a.startswith("fair_pzm_"),
    "maker, fair quotes pulled on microprice moves": lambda a: a.startswith("mkm_"),
}
FAMILIES3 = {"books-agree micf (post-hoc)": lambda a: a.startswith("micfa_")}
MODULES = {"h1": "sweep1", "h2": "sweep2", "h3": "sweep3", "h4": "sweep4", "mkh": "maker1",
           "mkb": "maker2", "mk3": "maker3", "mk4": "maker4", "m1": "micro1", "mm": "makerm",
           "m3": "micro3"}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tags", default="h1,h2,h3,h4,mkh,mkb,mk3,mk4")
    ap.add_argument("--v2", action="store_true", help="tags m1,mm -> selection2.json")
    ap.add_argument("--v3", action="store_true", help="tag m3 -> selection3.json")
    a = ap.parse_args()
    fams, out_name = FAMILIES, "selection"
    if a.v2:
        a.tags, fams, out_name = "m1,mm", FAMILIES2, "selection2"
    if a.v3:
        a.tags, fams, out_name = "m3", FAMILIES3, "selection3"
    parts, arms = [], {}
    for tag in a.tags.split(","):
        t = scored(tag, "train")
        t["tag"] = tag
        parts.append(t)
        for arm in importlib.import_module(f"research.strategy.eval.arms.{MODULES[tag]}").ARMS:
            arms[arm["name"]] = arm
    t = pd.concat(parts).drop_duplicates(["arm", "L"])
    t["mk10_day"] = t["mk10_c"] * t["usd_day"] / 100
    s = t[t["L"] == 0].groupby("arm").agg(
        obj=("mk10_day", "mean"), net=("net_day", "mean"), c=("c_per_usd", "mean"),
        mk10_c=("mk10_c", "mean"), fills=("fills_day", "mean")).reset_index()
    rows, sel = [], {}
    for fam, pred in fams.items():
        inf = s[s["arm"].map(pred)]
        x = inf[inf["net"] > 0].sort_values("obj", ascending=False)
        if not len(x):
            x = inf.sort_values("obj", ascending=False)
        best = x.iloc[0]
        rows.append({"family": fam, **best.to_dict()})
        sel[fam] = arms[best["arm"]]
    out = pd.DataFrame(rows)
    out.to_csv(OUT / f"{out_name}.csv", index=False)
    (OUT / f"{out_name}.json").write_text(json.dumps(sel, indent=1, default=list))
    pd.set_option("display.width", 250)
    print(out.round(2).to_string(index=False))


if __name__ == "__main__":
    main()
