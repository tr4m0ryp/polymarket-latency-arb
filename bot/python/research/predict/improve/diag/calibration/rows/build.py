"""Per-window row caches: every gated (decision, side) row of the allowed markets with the
frozen models' predictions, the realised taker values (1 / 3 / 10 s marks at L = 0 and -40),
the activity-regime columns, and (on a sample) every model feature.

    nice -n 10 python3 -m research.predict.improve.diag.calibration.rows.build [--win dev3]

Writes data/cache/predict/improve/calibration/rows-<win>.pkl (compact, all rows) and
feat-<win>.pkl (all model features on rows with a top prediction >= 1 c plus a 6% random
sample, flagged `rnd`)."""
from __future__ import annotations

import argparse
import time

import numpy as np
import pandas as pd

from ......predict.model.learners import clean
from ......predict.model.stack import gate, stacked
from ......predict.model.store import load_model
from ... import calibration as C
from ..safe import SafeStore, check, market_ids
from .regime import regime

KEEP = ["m", "t", "side", "row", "seen", "tok_mid", "secs_left", "sigma", "p_lam", "s_lam", "delta",
        "pm_spr", "pm_tsc", "half_spread"]
REAL = [f"v{k}_{L}" for k in (1, 3, 10) for L in (0, -40)] + ["bad0", "bad-40"]
RND = 0.06


def _models() -> dict:
    return {n: load_model(n) for n in C.MODELS}


def one(i: int, st: SafeStore, mdl: dict, rng) -> tuple[pd.DataFrame, pd.DataFrame] | None:
    m = st.market(i)
    p = C.predict.CACHE / "tab" / f"{i}.npz"
    if m is None or not p.exists():
        return None
    with np.load(p) as z:
        df = pd.DataFrame({k: z[k] for k in z.files})
    df["m"] = i
    rg = regime(m, df)
    g = gate(df).to_numpy()
    rows, vf = stacked(df)
    if not len(rows):
        return None
    add, ri = {}, rows["row"].to_numpy()
    for name, md in mdl.items():
        X = rows.reindex(columns=md["vf"], fill_value=0.0)
        add[f"p_{name}"] = md["model"].predict(clean(X.to_numpy())).astype(np.float32)
    add.update({k: v[g][ri] for k, v in rg.items()})
    rows = pd.concat([rows, pd.DataFrame(add, index=rows.index)], axis=1)
    pc = [f"p_{n}" for n in mdl]
    comp = rows[KEEP + REAL + pc + list(rg)].copy()
    top = rows[pc].max(axis=1).to_numpy() >= 0.01
    rnd = rng.random(len(rows)) < RND
    feat = rows.loc[top | rnd, list(dict.fromkeys(vf + KEEP + REAL + pc + list(rg)))].copy()
    feat["rnd"] = rnd[top | rnd]
    return comp, feat


def build(win: str, st: SafeStore, mdl: dict) -> None:
    ids = market_ids(win)
    check(st.mk.start[ids])
    rng = np.random.default_rng(11)
    comps, feats, t0 = [], [], time.time()
    for j, i in enumerate(ids):
        r = one(i, st, mdl, rng)
        if r is not None:
            comps.append(r[0])
            feats.append(r[1])
        if j % 20 == 0:
            print(win, j, len(ids), f"{time.time() - t0:.0f}s", flush=True)
    C.CACHE.mkdir(parents=True, exist_ok=True)
    f32 = lambda d: d.astype({c: np.float32 for c in d.columns if d[c].dtype == np.float64 and c != "t"})  # noqa: E731
    f32(pd.concat(comps, ignore_index=True)).to_pickle(C.CACHE / f"rows-{win}.pkl")
    f32(pd.concat(feats, ignore_index=True)).to_pickle(C.CACHE / f"feat-{win}.pkl")
    print(win, "done", len(ids), f"{time.time() - t0:.0f}s", flush=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--win", default=",".join(C.WINDOWS))
    a = ap.parse_args()
    st, mdl = SafeStore(), _models()
    for w in a.win.split(","):
        assert w in C.WINDOWS, w
        build(w, st, mdl)


if __name__ == "__main__":
    main()
