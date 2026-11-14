"""Which features drive the prediction inflation and the miscalibration in busy regimes.

    OMP_NUM_THREADS=2 nice -n 10 python3 -m research.predict.improve.diag.calibration.analyze.attrib

1. Shift attribution (quantile mapping): on a window's random rows, map one feature group's
   values onto the train marginal (window ECDF -> train quantile, per column) and re-predict;
   the change in the firing share (pred >= 3 c) and in the mean prediction of the window's
   firing rows is that group's contribution to the drift. All groups mapped = total.
2. Importance by regime: within quiet / busy rows (busy index tertiles, train cutpoints) of
   the pooled unseen windows, shuffle one group and measure the drop of the realised 10 s
   value of the top-2% rows by prediction (as model/importance.py) and the change of the
   mean gap (realised 10 s - pred) on rows with pred >= 3 c.
3. Residual drivers: a small GBDT predicts the residual (realised 1 s - pred) on rows with
   pred >= 2 c of the pooled unseen windows from the model features plus the regime columns
   (2-fold split by market); grouped permutation on the held-out fold gives the drop in its
   R^2 per group, i.e. which inputs carry the miscalibration.
Writes OUT/attrib.md."""
from __future__ import annotations

import numpy as np
import pandas as pd

from .. import OUT
from .....model.learners import clean
from .....model.store import load_model
from .....report.md import md
from .common import busy_index, cuts, rows
from .groups import GROUPS, group_cols
from .shift import REG, feat

MODEL = "v1_L0"


def qmap(x: np.ndarray, ref: np.ndarray, src: np.ndarray) -> np.ndarray:
    """Map x (distributed like src) onto ref's marginal."""
    if not len(ref):
        return x
    u = np.searchsorted(np.sort(src), x, side="right") / max(len(src), 1)
    r = np.sort(ref)
    return r[np.clip(np.ceil(u * len(r)).astype(np.int64) - 1, 0, len(r) - 1)]   # inverted CDF


def shift_attr(tr: pd.DataFrame, te: pd.DataFrame, mdl: dict) -> pd.DataFrame:
    vf, m = mdl["vf"], mdl["model"]
    ref = clean(tr.loc[tr["rnd"], vf].to_numpy())
    src = clean(te.loc[te["rnd"], vf].to_numpy())
    X = clean(te[vf].to_numpy())
    rnd = te["rnd"].to_numpy()
    p0 = m.predict(X)
    fire0 = p0 >= 0.03
    out = [{"group": "(as observed)", "fire_share_pct": 100 * fire0[rnd].mean(), "mean_pred_fire_c": 100 * p0[fire0].mean()}]
    ptr = m.predict(ref)
    out.append({"group": "(train reference)", "fire_share_pct": 100 * (ptr >= 0.03).mean(),
                "mean_pred_fire_c": 100 * ptr[ptr >= 0.03].mean()})
    for g in list(GROUPS) + ["ALL"]:
        ix = list(range(len(vf))) if g == "ALL" else group_cols(vf, g)
        if not ix:
            continue
        Xs = X.copy()
        for j in ix:
            Xs[:, j] = qmap(X[:, j], ref[:, j], src[:, j])
        p = m.predict(Xs)
        out.append({"group": g, "fire_share_pct": 100 * (p[rnd] >= 0.03).mean(),
                    "mean_pred_fire_c": 100 * p[fire0].mean()})
    o = pd.DataFrame(out)
    o["d_fire_share_pct"] = o["fire_share_pct"] - o["fire_share_pct"].iloc[0]
    o["d_pred_fire_c"] = o["mean_pred_fire_c"] - o["mean_pred_fire_c"].iloc[0]
    return o


def regime_importance(d: pd.DataFrame, mdl: dict, seed: int = 0) -> pd.DataFrame:
    vf, m = mdl["vf"], mdl["model"]
    lo, hi = cuts()["busy"]
    b = busy_index(d, rows("train"))
    out, rng = [], np.random.default_rng(seed)
    for name, w in (("quiet", b < lo), ("busy", b >= hi)):
        s = d[w & (d["bad0"] == 0).to_numpy() & np.isfinite(d["v10_0"]).to_numpy()]
        X, real = clean(s[vf].to_numpy()), s["v10_0"].to_numpy(float)
        p = m.predict(X)
        n = max(int(0.02 * len(p)), 50)
        base = 100 * real[np.argsort(-p)[:n]].mean()
        f = p >= 0.03
        gap0 = 100 * (real[f] - p[f]).mean()
        out.append({"regime": name, "group": "(none)", "rows": len(s), "top2_c": base, "drop_c": 0.0,
                    "gap_fire_c": gap0, "d_gap_c": 0.0})
        for g in GROUPS:
            ix = group_cols(vf, g)
            Xs = X.copy()
            Xs[:, ix] = X[rng.permutation(len(X))][:, ix]
            ps = m.predict(Xs)
            v = 100 * real[np.argsort(-ps)[:n]].mean()
            fs = ps >= 0.03
            gp = 100 * (real[fs] - ps[fs]).mean() if fs.any() else np.nan
            out.append({"regime": name, "group": g, "rows": len(s), "top2_c": v, "drop_c": base - v,
                        "gap_fire_c": gp, "d_gap_c": gp - gap0})
    return pd.DataFrame(out)


def residual_drivers(d: pd.DataFrame, mdl: dict, seed: int = 0) -> pd.DataFrame:
    from sklearn.ensemble import HistGradientBoostingRegressor
    from sklearn.metrics import r2_score
    vf = mdl["vf"]
    d = d[(d["p_v1_L0"] >= 0.02) & (d["bad0"] == 0) & np.isfinite(d["v1_0"])]
    cols = vf + REG
    X = clean(d[cols].to_numpy())
    y = (d["v1_0"] - d["p_v1_L0"]).to_numpy(float)
    fold = (pd.util.hash_array(d["m"].to_numpy().astype(np.int64)) % 2).astype(int)
    groups = {g: group_cols(vf, g) for g in GROUPS} | {"regime (activity rates, vol)": list(range(len(vf), len(cols)))}
    rng, r2s, drops = np.random.default_rng(seed), [], {g: [] for g in groups}
    for k in (0, 1):
        m = HistGradientBoostingRegressor(max_iter=150, max_leaf_nodes=15, min_samples_leaf=200, learning_rate=0.05,
                                          random_state=seed).fit(X[fold != k], y[fold != k])
        Xt, yt = X[fold == k], y[fold == k]
        base = r2_score(yt, m.predict(Xt))
        r2s.append(base)
        for g, ix in groups.items():
            Xs = Xt.copy()
            Xs[:, ix] = Xt[rng.permutation(len(Xt))][:, ix]
            drops[g].append(base - r2_score(yt, m.predict(Xs)))
    out = pd.DataFrame({"group": list(groups), "r2_drop": [np.mean(v) for v in drops.values()]})
    return pd.concat([pd.DataFrame({"group": ["(held-out R2 of the residual model)"], "r2_drop": [np.mean(r2s)]}),
                      out.sort_values("r2_drop", ascending=False)], ignore_index=True)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    mdl = load_model(MODEL)
    tr = feat("train")
    txt = [f"# Over-prediction and drift attribution, {MODEL}\n"]
    pooled = []
    for w in ("select", "dev3", "final", "ext"):
        te = feat(w)
        txt.append(f"\n## Shift attribution, {w} mapped onto train marginals\n")
        txt.append(md(shift_attr(tr, te, mdl), 2))
        if w != "select":
            pooled.append(te)
        print(w, flush=True)
    txt.append("\n## Importance by regime (pooled dev3 + final + ext, both sides, sampled rows)\n")
    P = pd.concat(pooled, ignore_index=True)
    txt.append(md(regime_importance(P, mdl), 2))
    txt.append("\n## Residual drivers (realised 1 s - pred, rows with pred >= 2 c, pooled dev3 + final + ext)\n")
    txt.append(md(residual_drivers(P, mdl), 4))
    (OUT / "attrib.md").write_text("\n".join(txt))


if __name__ == "__main__":
    main()
