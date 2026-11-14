"""CLI: evaluate one candidate with the two-fold window cross-validation.

    nice -n 10 python3 -m research.predict.improve.harness --arm <module:callable> \
        --out data/out/predict/improve/<name>/ [--L=0,-40] [--workers 2] [--threads 1] [--no-comp]

`module:callable` = an importable module path and a candidate callable in it, e.g.
research.predict.improve.harness.frozen:vt_any (see harness/__init__.py for the interface)."""
from __future__ import annotations

import argparse
import importlib
from pathlib import Path

from . import evaluate, report


def main() -> None:
    ap = argparse.ArgumentParser(prog="python3 -m research.predict.improve.harness")
    ap.add_argument("--arm", required=True, help="module:callable returning Arm(s) for a Fold")
    ap.add_argument("--out", required=True)
    ap.add_argument("--L", default="0,-40")
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--threads", type=int, default=1, help="BLAS/OpenMP threads per worker")
    ap.add_argument("--no-comp", action="store_true", help="skip the 50 ms competition variant")
    a = ap.parse_args()
    assert a.workers * a.threads <= 4 and a.workers <= 2, "shared box: at most 2 workers"
    mod, _, fn = a.arm.partition(":")
    cand = getattr(importlib.import_module(mod), fn)
    res = evaluate(cand, L=tuple(int(x) for x in a.L.split(",")),
                   variants=("base",) if a.no_comp else ("base", "comp"), workers=a.workers, threads=a.threads)
    print(report.write(res, Path(a.out), a.arm))


if __name__ == "__main__":
    main()
