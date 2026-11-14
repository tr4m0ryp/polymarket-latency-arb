"""Run one C3 family through the shared harness (research/predict/improve/harness, unchanged)
and keep the simulator's memo so every variant (not only the picked one) gets a table, with
the paired gain vs the frozen veto added (the harness pairs only vs vt_any and micf).

    nice -n 10 python3 -m research.predict.improve.cand.<this package>.run --arm coh_taker \
        --out data/out/predict/improve/c3_coherence/coh_taker/

Writes the harness outputs (table.md/csv, hours.csv, selection_*.csv, meta.json) plus
cand_veto.csv (the picked candidate with gain vs veto) and variants.csv (every variant on
every set; in-sample for the choice, used only for the sweep and kill test 3)."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

os.environ.setdefault("OMP_NUM_THREADS", "2")

import pandas as pd  # noqa: E402

from research.predict.improve.harness import report, run as R, windows as W  # noqa: E402
from research.predict.improve.harness.frozen import FROZEN, VETO, VT_ANY, MICF  # noqa: E402
from research.predict.improve.harness.guard import SEALED, assert_allowed  # noqa: E402
from research.predict.improve.harness.score import metrics, sets  # noqa: E402
from research.predict.improve.harness.sim import frozen_cache  # noqa: E402

from . import arms as A, split as SP  # noqa: E402


class _Keep(R.Sim):
    last = None

    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        _Keep.last = self


def _extra(sim, res, Ls, variants) -> tuple[pd.DataFrame, pd.DataFrame]:
    ids = W.all_eval_ids()
    act = pd.DataFrame([sim.activity[i] for i in ids])
    assert_allowed(act["start"], "c3 sets")
    assert act["start"].max() < SEALED
    S = sets.build(act)
    refs = {n: sim.agg(frozen_cache.PREFIX + n, ids) for n in FROZEN}
    pair = {VT_ANY: refs[VT_ANY], MICF: refs[MICF], VETO: refs[VETO]}
    cand = pd.concat([sim.agg(d["key"], sorted(i for w in d["evaluate"] for i in W.ids(w)), R.CAND)
                      for d in res["folds"].values()], ignore_index=True)
    ren = lambda t: t.rename(columns=lambda c: c.replace(f"g_{VETO}", "g_veto"))  # noqa: E731
    ctab = ren(metrics.table({R.CAND: cand, **refs}, pair, S, Ls=Ls, variants=variants))
    var = {k.split("|", 1)[1]: sim.agg(k, ids) for k in sim.arms if k.startswith("*|")}
    vtab = ren(metrics.table(var, pair, S, Ls=Ls, variants=variants)) if var else pd.DataFrame()
    return ctab, vtab


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", required=True, help="family name in arms.py (or split.py, diagnostic)")
    ap.add_argument("--out", required=True)
    ap.add_argument("--L", default="0,-40")
    ap.add_argument("--no-comp", action="store_true")
    a = ap.parse_args()
    cand = getattr(A, a.arm, None) or getattr(SP, a.arm)
    Ls = tuple(int(x) for x in a.L.split(","))
    variants = ("base",) if a.no_comp else ("base", "comp")
    R.Sim = _Keep
    res = R.evaluate(cand, L=Ls, variants=variants, workers=2, threads=1)
    assert res["max_start"] < SEALED
    out = Path(a.out)
    report.write(res, out, f"{__package__}.arms:{a.arm}")
    ctab, vtab = _extra(_Keep.last, res, Ls, variants)
    ctab.to_csv(out / "cand_veto.csv", index=False)
    vtab.to_csv(out / "variants.csv", index=False)
    (out / "chosen.json").write_text(json.dumps({f: d["chosen"] for f, d in res["folds"].items()}))
    print({f: d["chosen"] for f, d in res["folds"].items()}, f"{res['secs_total']:.0f}s", flush=True)


if __name__ == "__main__":
    main()
