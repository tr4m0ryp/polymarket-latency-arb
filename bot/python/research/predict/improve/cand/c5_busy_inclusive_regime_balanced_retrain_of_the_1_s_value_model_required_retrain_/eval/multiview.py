"""Several harness views of one set of per-fold arms from a single simulation pass.

The harness CLI evaluates one candidate per run and re-simulates its arms each time. C5 needs
each pre-registered variant alone (the kill tests compare them) and the three-variant
selection, so this driver simulates every fold's arms once on every allowed market (memoised
on disk, eval/memo.py) and then builds each view exactly as harness/run.py does: per fold,
a view with several arms picks one on that fold's choose windows (score/select.py, at L = 0,
base fills), and only the pick is scored on the fold's evaluate windows. Same metrics, sets,
frozen references, guards and report writer as the harness."""
from __future__ import annotations

import time
from pathlib import Path

import pandas as pd
from threadpoolctl import threadpool_limits

from ....harness import report, windows as W
from ....harness.fold import Fold
from ....harness.frozen import FROZEN
from ....harness.guard import assert_allowed, check_env, check_models
from ....harness.run import CAND, _hour_table
from ....harness.score import metrics, select, sets
from ....harness.sim import frozen_cache
from ....harness.sim.pool import Sim
from . import memo


def simulate(arm_fn, L=(0,), variants=("base", "comp"), workers: int = 2):
    """Simulate every fold's arms on every allowed market. Returns (sim, keys, refs, act)."""
    threadpool_limits(limits=2)
    check_env()
    hashes = check_models()
    sim = Sim(L, variants, workers, 1)
    fkeys = frozen_cache.ensure(sim, hashes)
    ids = W.all_eval_ids()
    refs = {k[len(frozen_cache.PREFIX):]: sim.agg(k, ids) for k in fkeys}
    keys, todo = {}, {}
    for f in W.FOLDS:
        for a in arm_fn(Fold(f)):
            key, sg = f"{f}|{a.name}", memo.sig(f, a, L, variants)
            sim.add(key, a)
            keys[(f, a.name)] = key
            if not memo.load(sim, key, sg, ids):
                todo[key] = (sg, a.name)
    if todo:
        sim.run({k: ids for k in todo})
        for k, (sg, name) in todo.items():
            memo.save(sim, k, sg, ids, name)
    act = pd.DataFrame([sim.activity[i] for i in ids])
    assert_allowed(act["start"], "evaluated markets")
    return sim, keys, refs, act, hashes


def view(sim, keys, refs, act, hashes, names, crit: str, L, variants, out: Path, spec: str) -> dict:
    t0 = time.time()
    pair = {n: refs[n] for n in metrics.REFS}
    folds, parts = {}, []
    for f, (choose, evaluate) in W.FOLDS.items():
        ch = sorted(i for w in choose for i in W.ids(w))
        ev = sorted(i for w in evaluate for i in W.ids(w))
        k = {n: keys[(f, n)] for n in names}
        chosen, info, sel = names[0], {"criterion": None, "variants": 1}, None
        if len(names) > 1:
            sel = metrics.table({n: sim.agg(x, ch, n) for n, x in k.items()}, pair, {f"{f}:choose": ch},
                                Ls=(0,), variants=("base",))
            chosen, info = select.choose(sel, crit)
        parts.append(sim.agg(k[chosen], ev, CAND))
        folds[f] = {"chosen": chosen, "key": k[chosen], "retrained": True, **info, "choose": list(choose),
                    "evaluate": list(evaluate), "selection": sel}
    S = sets.build(act)
    arms_tab = {CAND: pd.concat(parts, ignore_index=True), **{n: refs[n] for n in FROZEN}}
    tab = metrics.table(arms_tab, pair, S, Ls=L, variants=variants)
    hrs = _hour_table(arms_tab, pair, act, L)
    res = {"table": tab, "hours": hrs, "folds": folds, "sets": {k: len(v) for k, v in S.items()},
           "secs_total": time.time() - t0, "secs_refs": 0.0, "secs_sim": sim.secs, "models": hashes,
           "max_start": float(act["start"].max()), "n_markets": len(act), "fold_invariant": False}
    report.write(res, out, spec)
    return res
