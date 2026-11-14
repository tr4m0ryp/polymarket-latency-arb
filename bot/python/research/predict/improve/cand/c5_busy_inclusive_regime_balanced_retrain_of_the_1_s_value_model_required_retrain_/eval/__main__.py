"""Run a C5 arm set through the harness once and write every view of it.

    OMP_NUM_THREADS=2 nice -n 10 python3 -m \
        research.predict.improve.cand.<this package>.eval --set main \
        --out data/out/predict/improve/c5_busy_refit/ [--no-comp]

Each view lands in <out>/<view>/ (harness table.md / table.csv / hours.csv / selection_*.csv /
meta.json); <out>/summary.md compares the views with the frozen arms."""
from __future__ import annotations

import argparse
from pathlib import Path

from ..plan import SETS
from . import multiview, summary


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--set", required=True, choices=sorted(SETS))
    ap.add_argument("--out", required=True)
    ap.add_argument("--no-comp", action="store_true")
    ap.add_argument("--workers", type=int, default=2)
    a = ap.parse_args()
    arm_fn, views = SETS[a.set]
    L, variants = (0,), ("base",) if a.no_comp else ("base", "comp")
    sim, keys, refs, act, hashes = multiview.simulate(arm_fn, L, variants, min(a.workers, 2))
    out = Path(a.out)
    for v, (names, crit) in views.items():
        multiview.view(sim, keys, refs, act, hashes, names, crit, L, variants, out / v,
                       f"c5:{a.set}:{v} {names}")
        print("view", v, "written", flush=True)
    print(summary.write(out, list(views)))


if __name__ == "__main__":
    main()
