"""Disk memo of C5 arm simulations: per (fold, arm signature) the per-market aggregates of the
harness simulator, so later views (new selection sets, sweeps) reuse earlier passes. The
signature names the refit model (fold, scheme, frac, seed, rows, trees) and the rule (margin,
projection), plus L and the simulator variants; anything else changed re-simulates."""
from __future__ import annotations

import hashlib
import pickle

import pandas as pd

from ..... import CACHE

DIR = CACHE / "improve" / "c5" / "sim"


def sig(fold: str, a, L, variants) -> str:
    r = a.decide
    m = r.mdl["meta"]
    s = (f"{fold}|{m['scheme']}|a{m['alpha']}|t{m['tilt']}|f{int(m['feat'])}|frac{m['frac']}|s{m['seed']}"
         f"|r{m['rows']}|n{m['n_iter']}|mg{r.margin}|coh{int(r.coh)}|L{sorted(L)}|{sorted(variants)}")
    if getattr(r, "blend", 1.0) < 1:
        s += f"|bl{r.blend}"
    return hashlib.sha256(s.encode()).hexdigest()[:16]


def load(sim, key: str, sg: str, ids) -> bool:
    """Fill sim.done for (key, every id) from the memo; True when complete."""
    p = DIR / f"{sg}.pkl"
    if not p.exists():
        return False
    with open(p, "rb") as fh:
        c = pickle.load(fh)
    if not set(ids) <= set(c["done"]):
        return False
    for i in ids:
        sim.done[(key, i)] = c["done"][i]
    for i, a in c["activity"].items():
        sim.activity.setdefault(i, a)
    return True


def save(sim, key: str, sg: str, ids, label: str) -> None:
    DIR.mkdir(parents=True, exist_ok=True)
    done = {i: sim.done[(key, i)] for i in ids}
    act = {i: sim.activity[i] for i in ids if i in sim.activity}
    p = DIR / f"{sg}.pkl"
    with open(p.with_suffix(".tmp"), "wb") as fh:
        pickle.dump({"label": label, "done": done, "activity": act}, fh)
    p.with_suffix(".tmp").replace(p)


def frame(sim, key: str, ids) -> pd.DataFrame:
    parts = [sim.done[(key, i)] for i in ids if len(sim.done[(key, i)])]
    return pd.concat(parts, ignore_index=True) if parts else pd.DataFrame()
