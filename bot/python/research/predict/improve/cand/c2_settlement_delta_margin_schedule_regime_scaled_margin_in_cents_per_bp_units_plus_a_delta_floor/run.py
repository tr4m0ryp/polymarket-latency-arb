"""Harness runner that also keeps the per-market aggregates of every simulated arm.

The harness (research/predict/improve/harness) is called unchanged; its Sim class is
subclassed only to remember the instance, so after `evaluate` every (arm key, market)
aggregate (candidate variants on every allowed market, the frozen references) is written to
<out>/aggs.pkl for extra.py (gains vs the frozen veto, the per-window variant sweep).

    nice -n 10 python3 -m research.predict.improve.cand.<c2>.run --arm dm_taker --out <dir>"""
from __future__ import annotations

import argparse
import os
import pickle
from pathlib import Path

for _k in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_k, "2")

import pandas as pd  # noqa: E402

from ...harness import report, run as R  # noqa: E402
from . import arms  # noqa: E402
from .delta import assert_unsealed  # noqa: E402

_SIMS: list = []


class _KeepSim(R.Sim):
    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        _SIMS.append(self)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", required=True, help="family name in arms.py")
    ap.add_argument("--out", required=True)
    ap.add_argument("--L", default="0,-40")
    a = ap.parse_args()
    cand = getattr(arms, a.arm)
    R.Sim = _KeepSim
    res = R.evaluate(cand, L=tuple(int(x) for x in a.L.split(",")), variants=("base", "comp"),
                     workers=2, threads=1)
    assert_unsealed([res["max_start"]], "evaluated markets")
    out = Path(a.out)
    print(report.write(res, out, f"{__package__}.arms:{a.arm}"))
    sim = _SIMS[-1]
    parts = []
    for (key, i), g in sim.done.items():
        if len(g):
            parts.append(g.assign(key=key))
    agg = pd.concat(parts, ignore_index=True)
    act = pd.DataFrame([sim.activity[i] for i in sorted(sim.activity)])
    assert_unsealed(act["start"], "saved activity")
    folds = {f: {"chosen": d["chosen"], "key": d["key"]} for f, d in res["folds"].items()}
    with open(out / "aggs.pkl", "wb") as fh:
        pickle.dump({"agg": agg, "activity": act, "folds": folds}, fh)
    print(f"saved {len(agg)} aggregate rows, {agg['key'].nunique()} arm keys -> {out / 'aggs.pkl'}")


if __name__ == "__main__":
    main()
