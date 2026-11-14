"""Simulate every variant of a family on all 395 allowed markets with the harness simulator
(strategy replay, 150 ms hold, unchanged), and save per-market aggregates with the frozen
references beside them.

    OMP_NUM_THREADS=1 nice -n 10 python3 -m research.predict.improve.diag.calibration.cv.driver \
        --family taker_margin [--var base|comp] [--only m2.5,rm_2.5_3]

Writes OUT/cv/agg-<family>-<var>.pkl (columns of sim/fills.aggregate + var; arm = variant
name, frozen references under their own names)."""
from __future__ import annotations

import argparse

import pandas as pd

from ....harness import windows as W
from ....harness.guard import assert_allowed, check_env, check_models
from ....harness.sim import frozen_cache
from ....harness.sim.pool import Sim
from . import OUT
from .families import FAMILIES

REFS = ("vt_v1_m0.03_any", "vt_v1_m0.02_trigger", "micf")


def run(family: str, var: str, only: list[str] | None, workers: int = 2) -> pd.DataFrame:
    check_env()
    hashes = check_models()
    ref, arms, alias = FAMILIES[family]()
    sim = Sim((0, -40), (var,), workers, 1)
    frozen_cache.ensure(sim, hashes)
    ids = W.all_eval_ids()
    assert_allowed(W._markets().start[ids], "cv markets")
    keys = {}
    for a in arms:
        if only and a.name not in only:
            continue
        if a.name in alias:
            keys[a.name] = frozen_cache.PREFIX + alias[a.name]
        else:
            keys[a.name] = f"{family}|{a.name}"
            sim.add(keys[a.name], a)
    sim.run({k: ids for n, k in keys.items() if n not in alias})
    parts = [sim.agg(k, ids, n) for n, k in keys.items()]
    parts += [sim.agg(frozen_cache.PREFIX + r, ids, r) for r in REFS]
    out = pd.concat([p for p in parts if len(p)], ignore_index=True)
    OUT.mkdir(parents=True, exist_ok=True)
    dst = OUT / f"agg-{family}-{var}.pkl"
    if dst.exists() and only:
        old = pd.read_pickle(dst)
        out = pd.concat([old[~old["arm"].isin(out["arm"].unique())], out], ignore_index=True)
    out.to_pickle(dst)
    act = pd.DataFrame([sim.activity[i] for i in ids])
    act.to_pickle(OUT / "activity.pkl")
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--family", required=True, choices=sorted(FAMILIES))
    ap.add_argument("--var", default="base", choices=("base", "comp"))
    ap.add_argument("--only", default=None)
    ap.add_argument("--workers", type=int, default=2)
    a = ap.parse_args()
    out = run(a.family, a.var, a.only.split(",") if a.only else None, min(a.workers, 2))
    print(out.groupby(["arm", "L"])["mk10v"].sum().round(0).to_string())


if __name__ == "__main__":
    main()
