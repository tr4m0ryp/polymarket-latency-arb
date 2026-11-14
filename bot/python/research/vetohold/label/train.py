"""Pre-register and freeze hold-aware veto models (selection hours only; test never read).

Variants (features = v1's 98 oriented features; `+x` adds the book-survival extras):
  A_real / A_h250 / A_h300   one regressor on the i = 0 value under that hold
  B_real                     P(survive at i = 0) x E[value | filled], two regressors
  A_real+x / B_real+x        the same with the extras
  v1_remargin                frozen v1, its margin re-chosen on the hold label (control)
Margin tau per variant: the best out-of-fold selection $/day (5 folds grouped by market,
0.2 s refractory, label value x 60 sh). Winner = best OOF selection $/day among new models.

    PYTHONPATH=. python3 -m research.vetohold.label.train -> data/out/vetohold/vmodels/"""
from __future__ import annotations

import hashlib
import json
import pickle
import time

import numpy as np
from sklearn.model_selection import GroupKFold

from research.predict.model.learners import gbdt_reg

from .. import OUT
from .data import EXTRA, Product, design, load, refractory, v1_pred

VM = OUT / "vmodels"
TAUS = np.round(np.arange(-0.03, 0.0801, 0.005), 3)
VARIANTS = ("A_real", "A_h250", "A_h300", "B_real", "A_real+x", "B_real+x",            # round 1
            "S_real", "S_h250", "S_real+x", "S_h250+x", "G_real+x", "G_h250+x")       # round 2
ROUND2 = "round 2 (S, G) added after round 1 lost to v1 on selection OOF; still before any test scoring"


def _reg(seed=0):
    return gbdt_reg(max_iter=300, leaves=15, lr=0.06, seed=seed, min_leaf=200)


def fit(name: str, X: np.ndarray, d) -> object:
    hold = name.split("_")[1].split("+")[0]
    if name[0] in "ASG":
        return _reg().fit(X, np.clip(d[f"y_{hold}"].to_numpy(), -0.3, 0.3))
    s = d[f"surv_{hold}"].to_numpy()
    ok = s > 0.02
    v = np.clip(d[f"y_{hold}"].to_numpy()[ok] / s[ok], -0.6, 0.6)
    return Product(_reg().fit(X, s), _reg().fit(X[ok], v, sample_weight=s[ok]))


def usd_day(d, pred, tau) -> tuple[float, float]:
    keep = refractory(d, pred >= tau)
    days = d["m"].nunique() / 288
    return (d["y_real"].to_numpy()[keep] * 60).sum() / days, keep.sum() / (days * 24)


def best_tau(d, pred) -> tuple[float, list]:
    grid = [(tau, *usd_day(d, pred, tau)) for tau in TAUS]
    return max(grid, key=lambda r: r[1])[0], grid


def main():
    t0 = time.time()
    d, X = load()
    sel = ~d["test"].to_numpy()
    ds, Xs = d[sel].reset_index(drop=True), X[sel]
    VM.mkdir(parents=True, exist_ok=True)
    meta = {"selection_rows": int(sel.sum()), "selection_markets": int(ds["m"].nunique()), "variants": {},
            "note": ROUND2}
    _, g = best_tau(ds, v1_pred(ds))
    meta["variants"]["v1_frozen"] = {"tau": 0.02, "sel_usd_day": usd_day(ds, v1_pred(ds), 0.02)[0]}
    tau, _ = best_tau(ds, v1_pred(ds))
    meta["variants"]["v1_remargin"] = {"tau": float(tau), "sel_usd_day": usd_day(ds, v1_pred(ds), tau)[0]}
    for name in VARIANTS:
        M, reg = design(name, Xs, ds)
        oof = np.full(len(ds), -np.inf)
        for tr, te in GroupKFold(5).split(M, groups=ds["m"]):
            tr, te = tr[reg[tr]], te[reg[te]]
            oof[te] = fit(name, M[tr], ds.iloc[tr]).predict(M[te])
        tau, grid = best_tau(ds, oof)
        u, oh = usd_day(ds, oof, tau)
        model = fit(name, M[reg], ds[reg])
        blob = pickle.dumps(model)
        (VM / f"{name}.pkl").write_bytes(blob)
        meta["variants"][name] = {"tau": float(tau), "oof_sel_usd_day": u, "oof_orders_h": oh,
                                  "sha256": hashlib.sha256(blob).hexdigest(),
                                  "grid": [[float(a), float(b), float(c)] for a, b, c in grid]}
        print(name, tau, round(u), round(oh), f"{time.time() - t0:.0f}s", flush=True)
    new = {k: v for k, v in meta["variants"].items() if "oof_sel_usd_day" in v}
    meta["winner"] = max(new, key=lambda k: new[k]["oof_sel_usd_day"])
    meta["frozen_utc"] = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
    meta["train_s"] = time.time() - t0
    meta["export"] = export(meta)
    (VM / "prereg.json").write_text(json.dumps(meta, indent=1))
    print("winner", meta["winner"], meta["export"])


def export(meta: dict) -> dict:
    """The winner in the predict model-store format ({model, vf, meta}) plus its trees JSON for
    the Rust bot (research/predict/infer/export.py). A product model (B) is written as two
    files, <name>.surv and <name>.value, whose predictions the bot multiplies."""
    from research.predict.infer.export import export as tree_export
    from research.predict.model.store import MODELS, load_model
    w = meta["winner"]
    vf = list(load_model("v1_L0")["vf"]) + (["v1_value"] if w[0] in "SG" else []) + (
        list(EXTRA) if w.endswith("+x") else [])
    name = "v1h_" + w.replace("+x", "x") + "_L0"
    v = meta["variants"][w]
    info = {"name": name, "base": "v1_L0 features, oriented to the trigger side", "label": w,
            "rule": f"trigger fires + gates, {'v1 value >= 0, ' if w[0] == 'S' else 'v1 keeps (>= 2 c), ' if w[0] == 'G' else ''}"
                    f"send iff pred(trigger side) >= {v['tau']}, 0.2 s refractory, limit = seen (i = 0)",
            "hold": "live decision -> match distribution (195 orders, 2026-10-13)" if "real" in w else w.split("_")[1],
            "train": "dublin-20261012 hours before 2026-10-13 00:00 UTC", "tau": v["tau"],
            "frozen_utc": meta["frozen_utc"]}
    model = pickle.loads((VM / f"{w}.pkl").read_bytes())
    parts = {name: model} if not w.startswith("B") else {f"{name}.surv": model.ps, f"{name}.value": model.vf}
    out = {}
    for nm, mdl in parts.items():
        blob = pickle.dumps({"model": mdl, "vf": vf, "meta": dict(info, part=nm)})
        path = MODELS / f"{nm}.pkl"
        path.write_bytes(blob)
        h = hashlib.sha256(blob).hexdigest()
        tj, th = tree_export(path, h)
        out[nm] = {"pkl": str(path), "pkl_sha256": h, "trees_json": str(tj), "trees_sha256": th}
    return {"name": name, **out}


if __name__ == "__main__":
    main()
