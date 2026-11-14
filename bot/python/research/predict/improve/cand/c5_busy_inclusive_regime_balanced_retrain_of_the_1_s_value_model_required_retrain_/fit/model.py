"""Refit the 1 s value model per fold on run 2 train + the fold's choose windows (the harness's
only training path, Fold.load_rows, which asserts max(start) < 1791744900), with optional
busy-regime weights. Same features (model.stack.stacked), target (v1_0 clipped to +/- 0.3 on
finite, bad0 == 0 rows) and learner (200 trees x 15 leaves, lr 0.05, min leaf 200) as the
frozen v1_L0; only the rows and their weights change.

A scheme is a dict {"alpha", "tilt", "feat"}: alpha / tilt as in busy.weights; feat = True
adds the busy index as an input feature (the model can condition on the regime instead of
averaging over it). Fitted models are cached on disk by (fold, frac, seed, scheme), so the
harness CLI and the multi-view driver share fits."""
from __future__ import annotations

import pickle
import time

import numpy as np

from ..... import CACHE
from .....model.learners import clean, gbdt_reg
from .....model.stack import gate, stacked
from ....harness import windows as W
from ....harness.guard import assert_allowed
from .busy import busy_rows, tertile, tertile_cuts, weights

DIR = CACHE / "improve" / "c5" / "models"
SCHEMES = {"plain": {"alpha": 0.0, "tilt": 1.0, "feat": False},       # pre-registered
           "bal": {"alpha": 1.0, "tilt": 1.0, "feat": False},         # pre-registered
           "tilt2": {"alpha": 0.0, "tilt": 2.0, "feat": False},       # variant: busy tertile x2
           "tilt4": {"alpha": 0.0, "tilt": 4.0, "feat": False},       # variant: busy tertile x4
           "feat": {"alpha": 0.0, "tilt": 1.0, "feat": True},         # variant: regime as an input
           "bal_feat": {"alpha": 1.0, "tilt": 1.0, "feat": True},
           # control: run 2 train only (no choose windows), to separate refit variance from the rows
           "tronly": {"alpha": 0.0, "tilt": 1.0, "feat": False, "train_only": True}}
BUSY_FEAT = "c5_busy"


def _path(fold: str, name: str, frac: float, seed: int):
    sc = SCHEMES[name]
    tag = f"a{sc['alpha']}_t{sc['tilt']}_f{int(sc['feat'])}" + ("_tr" if sc.get("train_only") else "")
    return DIR / f"{fold}_{tag}_frac{frac}_s{seed}.pkl"


def fit_fold(fold, names=("plain", "bal"), frac: float = 0.25, seed: int = 1) -> dict:
    """{scheme name: {"model", "vf", "meta"}} for this fold, fitting only the missing ones."""
    fold.touched = True            # per-fold model: the harness must never reuse results across folds
    out, need = {}, []
    for n in names:
        p = _path(fold.name, n, frac, seed)
        if p.exists():
            with open(p, "rb") as fh:
                out[n] = pickle.load(fh)
        else:
            need.append(n)
    for wins in sorted({("train",) if SCHEMES[n].get("train_only") else fold.train_windows for n in need}):
        out |= _fit(fold, [n for n in need if (("train",) if SCHEMES[n].get("train_only") else fold.train_windows)
                           == wins], wins, frac, seed)
    return out


def _fit(fold, need, wins, frac, seed) -> dict:
    out, t0 = {}, time.time()
    rows = fold.load_rows(windows=wins, frac=frac, seed=seed)
    assert_allowed(W._markets().start[rows["m"].unique()], "c5 training rows")
    gate_b = busy_rows(rows)
    g = gate(rows).to_numpy()
    tr, vf = stacked(rows)
    del rows
    b = gate_b[g][tr["row"].to_numpy()]
    w_ok = np.isfinite(tr["v1_0"].to_numpy()) & (tr["bad0"] == 0).to_numpy()
    is_train = np.isin(tr["m"].to_numpy(), W.train_ids())
    cuts = tertile_cuts(b[w_ok & is_train])
    ter = tertile(b[w_ok], cuts)
    y = np.clip(tr.loc[w_ok, "v1_0"].to_numpy(float), -0.3, 0.3)
    X0 = clean(tr.loc[w_ok, vf].to_numpy())
    del tr
    print(f"c5 fold {fold.name}: {w_ok.sum()} rows, load+features {time.time() - t0:.0f}s", flush=True)
    for n in need:
        sc = SCHEMES[n]
        t1 = time.time()
        w, info = weights(ter, sc["alpha"], sc["tilt"])
        X, vfn = (np.c_[X0, clean(b[w_ok])], vf + [BUSY_FEAT]) if sc["feat"] else (X0, list(vf))
        m = gbdt_reg(max_iter=200, leaves=15, lr=0.05, min_leaf=200).fit(
            X, y, sample_weight=None if sc["alpha"] == 0 and sc["tilt"] == 1 else w)
        meta = {"fold": fold.name, "scheme": n, **sc, "frac": frac, "seed": seed, "rows": int(w_ok.sum()),
                "cuts": cuts, **info, "n_iter": int(m.n_iter_), "secs": round(time.time() - t1),
                "windows": list(wins)}
        out[n] = {"model": m, "vf": vfn, "meta": meta}
        DIR.mkdir(parents=True, exist_ok=True)
        p = _path(fold.name, n, frac, seed)
        with open(p.with_suffix(".tmp"), "wb") as fh:
            pickle.dump(out[n], fh)
        p.with_suffix(".tmp").replace(p)
        print(f"c5 fold {fold.name} {n}: {meta}", flush=True)
    return out
