"""Two-fold window cross-validation of one candidate against the frozen arms.

Per fold: build the candidate's arms for that fold; if it offers several variants, simulate
them on the choose windows and pick one with the declared rule (score/select.py); simulate
the pick on the evaluate windows. Every allowed market is then scored by a variant chosen
without it ("CV" sets), next to the frozen references on the same markets. Fold-invariant
variants are simulated in one pass over every market (faster); results of a variant on a
fold's evaluate windows are only ever reported when that fold chose it.

Candidate attributes (optional, read before anything runs):
    FOLD_INVARIANT = True   arms do not depend on the fold (results reused across folds)
    CRITERION = "gain"      variant choice: gain | lcb | mk (score/select.py)
    SELECT_L = 0            L at which variants are chosen"""
from __future__ import annotations

import time

import pandas as pd
from threadpoolctl import threadpool_limits

from . import windows as W
from .api import Arm
from .fold import Fold
from .frozen import FROZEN, from_spec
from .guard import assert_allowed, check_env, check_models
from .score import metrics, select, sets
from .sim import frozen_cache
from .sim.pool import Sim

CAND = "candidate"


def _arms(candidate, fold: Fold) -> list[Arm]:
    out = candidate(fold)
    out = out if isinstance(out, (list, tuple)) else [out]
    out = [from_spec(a) if isinstance(a, dict) else a for a in out]
    names = [a.name for a in out]
    assert out and len(set(names)) == len(names), f"fold {fold.name}: arm names must be unique"
    return out


def evaluate(candidate, L=(0, -40), variants=("base", "comp"), workers: int = 2, threads: int = 1) -> dict:
    threadpool_limits(limits=2)     # the parent too (retraining candidates fit here)
    check_env()
    hashes = check_models()
    t0 = time.time()
    sim = Sim(L, variants, workers, threads)
    fkeys = frozen_cache.ensure(sim, hashes)
    t_ref = time.time() - t0
    invariant = bool(getattr(candidate, "FOLD_INVARIANT", False))
    crit, sel_L = getattr(candidate, "CRITERION", "gain"), getattr(candidate, "SELECT_L", 0)
    assert crit in select.CRITERIA and sel_L in L
    refs_all = {k[len(frozen_cache.PREFIX):]: sim.agg(k, W.all_eval_ids()) for k in fkeys}
    pair_refs = {n: refs_all[n] for n in metrics.REFS}
    folds, cand_parts = {}, []
    for name in W.FOLDS:
        fold = Fold(name)
        arms = _arms(candidate, fold)
        scope = "*" if invariant and not fold.touched else name
        keys = {a.name: frozen_cache.PREFIX + a.ref if a.ref in FROZEN else f"{scope}|{a.name}" for a in arms}
        for a in arms:
            sim.add(keys[a.name], a)
        choose_ids = sorted(i for w in fold.choose for i in W.ids(w))
        eval_ids = sorted(i for w in fold.evaluate for i in W.ids(w))
        info, sel_tab = {"criterion": None, "variants": 1}, None
        chosen = arms[0].name
        if len(arms) > 1:
            if scope == "*":   # fold-invariant variants: one pass over every market serves both folds
                sim.run({k: W.all_eval_ids() for k in keys.values()})
            sim.run({k: choose_ids for k in keys.values()})
            sel_tab = metrics.table({n: sim.agg(k, choose_ids, n) for n, k in keys.items()}, pair_refs,
                                    {f"{name}:choose": choose_ids}, Ls=(sel_L,), variants=("base",))
            chosen, info = select.choose(sel_tab, crit)
        sim.run({keys[chosen]: eval_ids})
        cand_parts.append(sim.agg(keys[chosen], eval_ids, CAND))
        folds[name] = {"chosen": chosen, "key": keys[chosen], "retrained": fold.touched, **info,
                       "choose": list(fold.choose), "evaluate": list(fold.evaluate), "selection": sel_tab}
    act = pd.DataFrame([sim.activity[i] for i in W.all_eval_ids()])
    assert_allowed(act["start"], "evaluated markets")
    S = sets.build(act)
    arms_tab = {CAND: pd.concat(cand_parts, ignore_index=True), **{n: refs_all[n] for n in FROZEN}}
    tab = metrics.table(arms_tab, pair_refs, S, Ls=L, variants=variants)
    hrs = _hour_table(arms_tab, pair_refs, act, L)
    return {"table": tab, "hours": hrs, "folds": folds, "sets": {k: len(v) for k, v in S.items()},
            "secs_total": time.time() - t0, "secs_refs": t_ref, "secs_sim": sim.secs, "models": hashes,
            "max_start": float(act["start"].max()), "n_markets": len(act), "fold_invariant": invariant}


def _hour_table(arms_tab, pair_refs, act, L) -> pd.DataFrame:
    h = sets.hours(act)
    by = {f"h{int(r.hour)}": act.loc[(act["start"] // 3600).astype(int) == r.hour, "m"].astype(int).tolist()
          for r in h.itertuples()}
    t = metrics.table(arms_tab, pair_refs, by, Ls=L, variants=("base",))
    t["hour_utc"] = pd.to_datetime(t["set"].str[1:].astype(int) * 3600, unit="s")
    t["window"] = t["set"].map({k: W.window_of(v[0]) for k, v in by.items()})
    return t.merge(h.assign(set="h" + h["hour"].astype(str))[["set", "trig"]], on="set")
