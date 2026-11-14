"""Harness-format result for a C1 family from the run.py dumps, without re-simulating.

Every C1 variant is fold-invariant and simulated on every allowed market once, so the
harness's fold choice and tables can be recomputed from the per-market aggregates exactly
(checked: score.cv reproduces the harness CV rows of size_taker and size_veto to the cent).
Writes table.md/csv, hours.csv, selection_{A,B}.csv, meta.json (report.write) plus
gain_vs_veto.csv (paired vs the frozen veto) under data/out/predict/improve/c1-size/<name>/.

    python3 -m research.predict.improve.cand.<c1 pkg>.final"""
from __future__ import annotations

import pandas as pd

from .... import OUT
from ...harness import report, run as hr
from ...harness.guard import SEALED
from ...harness.score import metrics, sets
from ...harness import windows as W
from . import score as S

D = OUT / "improve" / "c1-size"
TAKER = [f"ek_vstar_{K}" + c for K in (2000, 3000, 4000) for c in ("", "_d6", "_d8")]
VETO = [f"vk_vstar_{K}" + c for K in (3000, 4000) for c in ("", "_d6", "_d8")]
FINAL = {"final-taker": TAKER, "final-veto": VETO}


def harness_like(pm, act, which, col="g_vt_lo", Ls=(0, -40), vars_=("base", "comp")) -> dict:
    R = S.refs(pm)
    pair_refs = {n: R[n] for n in metrics.REFS}
    cand, folds = [], {}
    for f, (ch, ev) in W.FOLDS.items():
        cid = sorted(i for w in ch for i in W.ids(w))
        eid = sorted(i for w in ev for i in W.ids(w))
        sel = metrics.table({n: S.arm(pm, n, cid) for n in which}, R, {f"{f}:choose": cid},
                            Ls=(0,), variants=("base",))
        pick = S.choose(sel, col)
        cand.append(S.arm(pm, pick, eid).assign(arm=hr.CAND))
        folds[f] = {"chosen": pick, "key": f"*|{pick}", "retrained": False, "criterion": col,
                    "variants": len(which), "choose": list(ch), "evaluate": list(ev), "selection": sel}
    arms = {hr.CAND: pd.concat(cand, ignore_index=True),
            **{n: pm[pm["arm"] == S.F + n].assign(arm=n) for n in (S.VT, S.VETO, S.MICF)}}
    St = sets.build(act)
    tab = metrics.table(arms, pair_refs, St, Ls=Ls, variants=vars_)
    gv = metrics.table({hr.CAND: arms[hr.CAND]}, {"veto": R["veto"]}, St, Ls=Ls, variants=vars_)
    hrs = hr._hour_table(arms, pair_refs, act, Ls)
    return {"table": tab, "hours": hrs, "folds": folds, "sets": {k: len(v) for k, v in St.items()},
            "secs_total": 0.0, "secs_refs": 0.0, "secs_sim": 0.0, "models": "v1_L0 570a9c1015c555c5, v1_L-40",
            "max_start": float(act["start"].max()), "n_markets": len(act), "fold_invariant": True,
            "gain_vs_veto": gv}


def main() -> None:
    dumps = [D / k for k in ("taker", "veto", "sweep", "round3") if (D / k / "per_market.pkl").exists()]
    pm, act = S.merge(dumps)
    assert act["start"].max() < SEALED
    for name, which in FINAL.items():
        res = harness_like(pm, act, which)
        gv = res.pop("gain_vs_veto")
        out = D / name
        report.write(res, out, f"c1 {name}: {which} (choice: lcb of gain vs vt_any)")
        gv.to_csv(out / "gain_vs_veto.csv", index=False)
        print(name, {f: d["chosen"] for f, d in res["folds"].items()})


if __name__ == "__main__":
    main()
