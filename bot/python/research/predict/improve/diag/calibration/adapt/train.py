"""Fit the adaptive-gain / delta-structural variants of the 1 s value model on run 2 train.

    OMP_NUM_THREADS=2 nice -n 10 python3 -m research.predict.improve.diag.calibration.adapt.train \
        [--var v1r,ctx,agc,agc_add,ds,ds_agc] [--L=0,-40]

Same learner, sample and settings as the frozen v1 (200 trees x 15 leaves, lr 0.05, min 200
rows per leaf, early stopping, target clipped to +/- 0.30 $/sh). ds variants: target
u = 100 (y + half spread + fee at the seen ask) / delta (bp), clipped to its train 0.5-99.5% range,
weight delta^2; prediction = delta * u_hat / 100 - half spread - fee; dsc: delta capped at DCAP.
q25 variants: the 25% quantile of the clipped target (a lower bound; pinball loss, in cents). The v1r control is checked
against the frozen v1 (max abs prediction difference on 20k train rows)."""
from __future__ import annotations

import argparse
import pickle
import time

import numpy as np

from ......predict.model.learners import clean, gbdt_reg
from ......predict.model.store import load_model
from . import MODELS, VARIANTS
from .data import load_train
from .feats import feature_set


DCAP = 30.0     # c/bp, about the train 70th percentile (dsc variants: value saturates at high delta)


def _delta(st, meta: dict) -> np.ndarray:
    d = st["delta"].to_numpy(float)
    return np.minimum(d, meta["dcap"]) if meta.get("dcap") else d


def fit(tr, vf_v1, gain, var: str, L: int) -> dict:
    vf = feature_set(var, vf_v1, gain)
    y = tr[f"v1_{L}"].to_numpy(float)
    w = np.isfinite(y) & (tr[f"bad{L}"] == 0).to_numpy()
    X = clean(tr.loc[w, vf].to_numpy())
    m = gbdt_reg(max_iter=200, leaves=15, lr=0.05, min_leaf=200)
    meta = {"var": var, "L": L, "rows": int(w.sum()), "ds": var.startswith("ds"),
            "dcap": DCAP if var.startswith("dsc") else None}
    if var.startswith("q25"):
        m = gbdt_reg(max_iter=200, leaves=15, lr=0.05, min_leaf=200, loss="quantile")
        m.set_params(quantile=0.25)
        m.fit(X, 100 * np.clip(y[w], -0.3, 0.3))              # cents: pinball loss in $ stalls early stopping
        meta["scale"] = 0.01
    elif meta["ds"]:
        d = _delta(tr.loc[w], meta)
        a = y[w] + tr.loc[w, "half_spread"].to_numpy(float) + tr.loc[w, "fee_seen"].to_numpy(float)
        u = 100 * a / np.maximum(d, 1e-3)          # bp of BTC; $ scale stalls early stopping (tol 1e-7)
        lo, hi = np.percentile(u, [0.5, 99.5])
        meta["u_clip"] = (float(lo), float(hi))
        m.fit(X, np.clip(u, lo, hi), sample_weight=d ** 2 / np.mean(d ** 2))
    else:
        m.fit(X, np.clip(y[w], -0.3, 0.3))
    meta["iters"] = int(m.n_iter_)
    return {"model": m, "vf": vf, "meta": meta}


def predict_rows(mdl: dict, st) -> np.ndarray:
    """Per-share value predictions for stacked rows (adapt/data.frame output)."""
    p = mdl["model"].predict(clean(st.reindex(columns=mdl["vf"], fill_value=0.0).to_numpy()))
    p = p * mdl["meta"].get("scale", 1.0)
    if mdl["meta"]["ds"]:
        p = _delta(st, mdl["meta"]) * p / 100 - st["half_spread"].to_numpy(float) - st["fee_seen"].to_numpy(float)
    return p


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--var", default=",".join(VARIANTS))
    ap.add_argument("--L", default="0,-40")
    a = ap.parse_args()
    t0 = time.time()
    tr, vf_v1, gain = load_train()
    print("rows", len(tr), "gain cols", len(gain), f"{time.time() - t0:.0f}s", flush=True)
    MODELS.mkdir(parents=True, exist_ok=True)
    for var in a.var.split(","):
        assert var in VARIANTS, var
        for L in (int(x) for x in a.L.split(",")):
            t1 = time.time()
            mdl = fit(tr, vf_v1, gain, var, L)
            if var == "v1r":
                s = tr.sample(20000, random_state=0)
                fz = load_model(f"v1_L{L}")
                d = np.abs(predict_rows(mdl, s) - fz["model"].predict(clean(s[fz["vf"]].to_numpy())))
                mdl["meta"]["max_diff_vs_frozen"] = float(d.max())
            with open(MODELS / f"{var}_L{L}.pkl", "wb") as fh:
                pickle.dump(mdl, fh)
            print(var, L, mdl["meta"], f"{time.time() - t1:.0f}s", flush=True)


if __name__ == "__main__":
    main()
