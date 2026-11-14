"""One harness pass for C4: every variant of both families on every allowed market (they are
fold-invariant), the fold choice per family, and the per-variant tables the kill tests need.

Same simulator, frozen references, sets and estimators as research/predict/improve/harness
(run.evaluate); the differences: (1) two families in one pass, (2) the veto family chooses
on its gain over the frozen veto (the taker family on vt_any), (3) every fixed variant is
also scored on all markets (no parameter is fitted per fold, so its all-market score is its
CV score), with controls `frz` (must equal the frozen arm) and `ek` (C1's ek_vstar_2000).

    OMP_NUM_THREADS=1 nice -n 10 python3 -m research.predict.improve.cand.<c4 package>.drive --tag r1"""
from __future__ import annotations

import argparse
import json
import time

import pandas as pd
from threadpoolctl import threadpool_limits

from ...harness import windows as W
from ...harness.api import Arm
from ...harness.guard import assert_allowed, check_env, check_models
from ...harness.score import metrics, sets
from ...harness.sim import frozen_cache
from ...harness.sim.pool import Sim
from . import OUT
from . import arms as A

REF = {"taker": "vt_v1_m0.03_any", "veto": "vt_v1_m0.02_trigger"}
TAG = {"vt_v1_m0.03_any": "vt", "vt_v1_m0.02_trigger": "vt_v1_m0.02_trigger", "micf": "micf"}


def families(spec: str) -> dict[str, tuple[list[Arm], list[Arm]]]:
    """family -> (selection variants, controls). spec picks the variant set (r1 = pre-declared)."""
    from . import variants
    return variants.SETS[spec]()


def choose(tab: pd.DataFrame, ref: str) -> tuple[str, dict]:
    col = f"g_{TAG[ref]}_lo"
    ok = (tab["mk10_c"] > 0) & (tab["fills_day"] >= 100)
    pool = tab[ok] if ok.any() else tab
    best = pool.sort_values([col, "arm"], ascending=[False, True]).iloc[0]
    return str(best["arm"]), {"lcb": float(best[col]), "gain": float(best[f"g_{TAG[ref]}"]), "met_floor": bool(ok.any())}


def run(spec: str, workers: int = 2) -> dict:
    threadpool_limits(limits=2)
    check_env()
    hashes = check_models()
    t0 = time.time()
    sim = Sim((0, -40), ("base", "comp"), workers, 1)
    fkeys = frozen_cache.ensure(sim, hashes)
    every = W.all_eval_ids()
    refs = {k[len(frozen_cache.PREFIX):]: sim.agg(k, every) for k in fkeys}
    fam = families(spec)
    keys = {}
    for sel, ctl in fam.values():
        for a in sel + ctl:
            keys[a.name] = f"*|{a.name}"
            sim.add(keys[a.name], a)
    sim.run({k: every for k in keys.values()})
    act = pd.DataFrame([sim.activity[i] for i in every])
    assert_allowed(act["start"], "evaluated markets")
    S = sets.build(act)
    out, folds, per_m = [], {}, dict(refs)
    for fname, (sel, ctl) in fam.items():
        cv = []
        for f, (ch, ev) in W.FOLDS.items():
            cid = sorted(i for w in ch for i in W.ids(w))
            eid = sorted(i for w in ev for i in W.ids(w))
            st = metrics.table({a.name: sim.agg(keys[a.name], cid, a.name) for a in sel}, refs,
                               {f"{f}:choose": cid}, Ls=(0,), variants=("base",))
            pick, info = choose(st, REF[fname])
            folds[f"{fname}:{f}"] = {"chosen": pick, **info, "selection": st.to_dict("records")}
            cv.append(sim.agg(keys[pick], eid, f"C4_{fname}"))
        arms_tab = {f"C4_{fname}": pd.concat(cv, ignore_index=True),
                    **{a.name: sim.agg(keys[a.name], every, a.name) for a in sel + ctl}}
        prefs = {**refs, **{f"ctl{k}": arms_tab[a.name] for k, a in enumerate(ctl)}}   # paired vs controls too
        t = metrics.table(arms_tab, prefs, S, Ls=(0, -40), variants=("base", "comp"))
        per_m.update(arms_tab)
        out.append(t.assign(family=fname))
    refs_t = metrics.table(refs, refs, S, Ls=(0, -40), variants=("base", "comp")).assign(family="frozen")
    tab = pd.concat(out + [refs_t], ignore_index=True)
    ctl = {f: [a.name for a in c] for f, (_, c) in fam.items()}
    return {"table": tab, "folds": folds, "per_market": per_m, "controls": ctl, "secs": time.time() - t0, "models": hashes,
            "max_start": float(act["start"].max()), "n_markets": len(act)}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="r1")
    ap.add_argument("--workers", type=int, default=2)
    a = ap.parse_args()
    assert a.workers <= 2
    res = run(a.tag, a.workers)
    d = OUT / a.tag
    d.mkdir(parents=True, exist_ok=True)
    res["table"].to_csv(d / "table.csv", index=False)
    pd.to_pickle(res.pop("per_market"), d / "per_market.pkl")
    (d / "meta.json").write_text(json.dumps({k: v for k, v in res.items() if k != "table"}, indent=1, default=str))
    from .report import write
    print(write(res["table"], res["folds"], d))
    print(f"done in {res['secs']:.0f}s", flush=True)


if __name__ == "__main__":
    main()
