"""Run a C1 family through the shared harness unchanged, and keep every variant's per-market
aggregates (the harness reports only the picked variant) for score.py.

    nice -n 10 python3 -m research.predict.improve.cand.<c1 pkg>.run --family size_taker \
        --out data/out/predict/improve/c1-size/taker [--workers 2 --threads 1] [--L 0,-40]

Writes the harness outputs (table.md/csv, hours.csv, selection_*.csv, meta.json) plus
per_market.pkl (arm key x L x variant x market aggregates, frozen references included) and
activity.pkl (label-free market activity, the busy-set input)."""
from __future__ import annotations

import argparse
import importlib
from pathlib import Path

import pandas as pd

from ...harness import report, run as hr
from ...harness import windows as W
from ...harness.guard import SEALED, assert_allowed

_SIMS: list = []


class _KeepSim(hr.Sim):
    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        _SIMS.append(self)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--family", required=True, help="callable in arms.py (or module:callable)")
    ap.add_argument("--out", required=True)
    ap.add_argument("--L", default="0,-40")
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--threads", type=int, default=1)
    ap.add_argument("--no-comp", action="store_true")
    a = ap.parse_args()
    assert a.workers <= 2 and a.workers * a.threads <= 4
    mod, _, fn = a.family.rpartition(":")
    mod = mod or f"{__package__}.arms"
    cand = getattr(importlib.import_module(mod), fn)
    hr.Sim = _KeepSim
    res = hr.evaluate(cand, L=tuple(int(x) for x in a.L.split(",")),
                      variants=("base",) if a.no_comp else ("base", "comp"),
                      workers=a.workers, threads=a.threads)
    out = Path(a.out)
    print(report.write(res, out, f"{mod}:{fn}"))
    sim = _SIMS[-1]
    act = pd.DataFrame([sim.activity[i] for i in W.all_eval_ids()])
    assert_allowed(act["start"], "c1 per-market dump")
    assert act["start"].max() < SEALED
    parts = [v for v in sim.done.values() if len(v)]
    pm = pd.concat(parts, ignore_index=True)
    assert set(pm["m"].astype(int)) <= set(act["m"].astype(int))
    pm.to_pickle(out / "per_market.pkl")
    act.to_pickle(out / "activity.pkl")
    print(f"per-market rows {len(pm)}, arms {sorted(pm['arm'].unique())}, max start {act['start'].max():.0f}")


if __name__ == "__main__":
    main()
