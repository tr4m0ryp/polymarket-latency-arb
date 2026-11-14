"""Build per-market label files (spot-safe: each market is its own file, done ones skipped).

Holds: `real` = mean over 16 equal-mass quantiles of the 195 live decision -> match holds;
`h250`, `h300` = fixed. Per row and hold: shares filled at i = 0 (60 sh sweep of side-frame
asks <= seen), cost, fee, side-frame mid at match + 10 s (capped end + 2 s; outcome if none).

    PYTHONPATH=. python3 -m research.vetohold.label.build --workers 30
    -> data/out/vetohold/label/<market>.npz"""
from __future__ import annotations

import argparse
from multiprocessing import Pool

import numpy as np
import pandas as pd

from research.predict.model.data import TAB, features
from research.predict.model.derive import add_derived
from research.predict.model.orient import orient
from research.predict.model.store import load_model
from research.predict.model.learners import clean
from research.predict.sim.rules import _gates
from research.strategy import DT
from research.strategy.sim.grid import Book, _replay

from ..data.orders import live_hold
from . import LAB
from .extras import extras

SIZE = 60.0
_st = _v1 = _H = None


def holds() -> dict:
    h = live_hold()
    return {"real": np.percentile(h, np.arange(16) * 6.25 + 3.125), "h250": np.array([0.250]),
            "h300": np.array([0.300])}


def fill_i0(book: Book, t, side, s_tick, h, end, won):
    """Per row: (filled share fraction, value per intended share) at hold h, limit = seen."""
    g = book.g_ceil(t + h)
    up = book.size[g, 101:200]                  # Up asks, ticks 1..99
    dn = book.size[g, 99:0:-1]                  # Up bids at 1 - q: Down asks, ticks 1..99
    a = np.where((side > 0)[:, None], up, dn).astype(float)
    a[np.arange(99)[None, :] >= s_tick[:, None]] = 0.0     # only ticks <= seen
    cum = np.cumsum(a, axis=1)
    take = np.clip(SIZE - (cum - a), 0, a)
    px = np.arange(1, 100) / 100.0
    sh, cost, fee = take.sum(1), take @ px, take @ (0.07 * px * (1 - px))
    mid = book.mid(book.g_ceil(np.minimum(t + h + 10, end + 2)))
    mk = np.where(np.isfinite(mid), np.where(side > 0, mid, 1 - mid), won)
    return sh / SIZE, (sh * mk - cost - fee) / SIZE


def one(i: int) -> str:
    global _st, _v1, _H
    out = LAB / f"{i}.npz"
    if out.exists():
        return "skip"
    from research.strategy.ingest.load import Store
    _st = _st or Store(keep=2)
    _v1 = _v1 or load_model("v1_L0")
    _H = _H or holds()
    m = _st.market(i)
    if m is None or m["outcome"] is None or not (TAB / f"{i}.npz").exists():
        return "none"
    with np.load(TAB / f"{i}.npz") as z:
        d = pd.DataFrame({k: z[k] for k in z.files})
    pm, sm = d["p_dmic0.1"].to_numpy(float), d["s_dmic0.1"].to_numpy(float)
    side = np.sign(pm + sm)
    seen = np.where(side > 0, d["pm_ba"].to_numpy(float) / 100, 1 - d["pm_bb"].to_numpy(float) / 100)
    trig = (np.abs(pm) >= 0.002) & (side != 0) & _gates(d, seen, (0.05, 0.95), 20.0, 0.97)
    t = d["t"].to_numpy(float)
    bad = np.zeros(len(t), bool)
    for g0, g1 in m["gaps"]:
        bad |= (t >= g0) & (t <= g1 + 0.2)
    trig &= ~bad
    if not trig.any():
        np.savez_compressed(out, n=np.array(0))
        return "empty"
    dd = add_derived(d.copy())
    fe = features(dd)
    X = {}
    for s in (1, -1):
        o = orient(dd, fe, s)
        for c in _v1["vf"]:
            if c not in o:
                o[c] = 0.0
        X[s] = clean(o[_v1["vf"]].to_numpy())
    pu, pdn = _v1["model"].predict(X[1]), _v1["model"].predict(X[-1])
    r = np.flatnonzero(trig)
    sd, st = side[r], seen[r]
    Xt = np.where((sd > 0)[:, None], X[1][r], X[-1][r]).astype(np.float32)
    meta = m["meta"]
    won = np.where(sd > 0, float(m["outcome"]), 1 - float(m["outcome"]))
    book = Book(m["ev"], meta["start"] - 2, meta["end"] + 2, m["gaps"])
    ev = m["ev"]
    rsz = _replay(ev["t"], ev["side"], ev["tick"].astype(np.int64), ev["size"], meta["start"] - 2, book.n)
    s_tick = np.rint(st * 100).astype(int)
    lab = {}
    for name, hs in _H.items():
        fr, val = zip(*(fill_i0(book, t[r], sd, s_tick, h, meta["end"], won) for h in hs))
        lab[f"surv_{name}"], lab[f"y_{name}"] = np.mean(fr, 0), np.mean(val, 0)
        lab[f"fill_{name}"] = np.mean([f > 0 for f in fr], 0)
    ex = extras(m, rsz, book, t[r], sd, s_tick)
    np.savez_compressed(out, n=np.array(len(r)), m=np.full(len(r), i), t=t[r], side=sd, seen=st, won=won,
                        X=Xt, pu=pu[r], pd=pdn[r], fair_p=d["fair_p"].to_numpy(float)[r],
                        **lab, **{f"x_{k}": v for k, v in ex.items()})
    return "ok"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=3)
    a = ap.parse_args()
    LAB.mkdir(parents=True, exist_ok=True)
    ids = sorted(int(p.stem) for p in TAB.glob("*.npz") if "tmp" not in p.name)
    with Pool(a.workers) as p:
        res = list(p.imap_unordered(one, ids, chunksize=2))
    print(pd.Series(res).value_counts().to_dict())


if __name__ == "__main__":
    main()
