"""Pool earlier simulation tags into one tag (same arms, disjoint markets), for the pooled
read of a pre-registered test. Score the result with sim.score as any other tag.

    python3 -m research.predict.sim.pool --tags dev1,final,ext,prereg2 --arms prereg2 --out pooled_pre2"""
from __future__ import annotations

import argparse
import importlib

import pandas as pd

from .. import OUT


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tags", required=True)
    ap.add_argument("--arms", required=True, help="arms module; keeps only its arm names")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    names = {x["name"] for x in importlib.import_module(f"research.predict.sim.arms.{a.arms}").ARMS}
    tags = a.tags.split(",")
    mk = pd.concat([pd.read_csv(OUT / f"markets-{t}.csv") for t in tags], ignore_index=True)
    assert mk["m"].is_unique, "tags overlap"
    for kind in ("agg", "fills", "dec"):
        parts = [OUT / f"{kind}-{t}.pkl" for t in tags]
        if kind == "dec" and not all(f.exists() for f in parts):
            continue  # taker decision counts exist only for tags run after 2026-10-13
        d = pd.concat([pd.read_pickle(f) for f in parts], ignore_index=True)
        d[d["arm"].isin(names)].to_pickle(OUT / f"{kind}-{a.out}.pkl")
    mk.to_csv(OUT / f"markets-{a.out}.csv", index=False)
    print("markets", len(mk))


if __name__ == "__main__":
    main()
