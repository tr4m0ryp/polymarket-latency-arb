"""The frozen references (vt_v1_m0.03_any, vt_v1_m0.02_trigger, micf) simulated once on every
allowed evaluation market and reused by every candidate run. The cache is keyed by the
harness simulation version, the frozen model hashes, L, variants and the market list; any
change re-simulates. Stored under data/cache/predict/improve/harness/ (gitignored)."""
from __future__ import annotations

import hashlib
import json
import pickle

import pandas as pd

from .... import CACHE
from .. import windows as W
from ..frozen import frozen_arms
from .pool import Sim

SIM_VERSION = 1
DIR = CACHE / "improve" / "harness"
PREFIX = "F|"


def _meta(hashes: dict, sim: Sim) -> dict:
    ids = W.all_eval_ids()
    return {"version": SIM_VERSION, "models": hashes, "L": sorted(sim.L), "variants": sorted(sim.variants),
            "ids_sha": hashlib.sha256(json.dumps(ids).encode()).hexdigest()[:16], "n_ids": len(ids)}


def ensure(sim: Sim, hashes: dict) -> list[str]:
    """Register the frozen arms in `sim` under keys F|<name> and fill their results for every
    allowed evaluation market from the cache or a fresh simulation. Returns the keys."""
    keys = []
    for a in frozen_arms():
        sim.add(PREFIX + a.name, a)
        keys.append(PREFIX + a.name)
    ids = W.all_eval_ids()
    meta, p = _meta(hashes, sim), DIR / "frozen.pkl"
    if p.exists():
        with open(p, "rb") as fh:
            c = pickle.load(fh)
        cm = c["meta"]
        if (cm["version"], cm["models"], cm["ids_sha"]) == (meta["version"], meta["models"], meta["ids_sha"]) \
                and set(meta["L"]) <= set(cm["L"]) and set(meta["variants"]) <= set(cm["variants"]):
            agg = c["agg"]
            agg = agg[agg["L"].isin(sim.L) & agg["var"].isin(sim.variants)]
            by = {k: g for k, g in agg.groupby(["arm", "m"])}
            for k in keys:
                for i in ids:
                    sim.done[(k, i)] = by.get((k, i), agg.iloc[:0])
            sim.activity.update({int(r["m"]): r for r in c["activity"].to_dict("records")})
            print(f"frozen references from cache ({len(ids)} markets)", flush=True)
            return keys
    sim.run({k: ids for k in keys})
    agg = pd.concat([sim.done[(k, i)] for k in keys for i in ids if len(sim.done[(k, i)])], ignore_index=True)
    act = pd.DataFrame([sim.activity[i] for i in ids])
    DIR.mkdir(parents=True, exist_ok=True)
    with open(p, "wb") as fh:
        pickle.dump({"meta": meta, "agg": agg, "activity": act}, fh)
    return keys
