"""Does depth behind the touch add to the top-of-book model? On the side-recorder hours
only (post-freeze diagnostic, cannot change the frozen arms): train on the first 2/3 of the
markets, score on the rest, with and without depth features (log queue 2nd level, 2-5 and
2-10 ticks behind, their bid-ask imbalances). Targets as in model/ftr_test.py.

    nice -n 10 python3 -m research.predict.depth.study"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

from .. import CACHE, OUT
from ..feats.decay import at
from ..model.data import features, load
from ..model.learners import clean, gbdt
from ..model.post_curve import target
from ..report.md import md


def add_depth(df: pd.DataFrame, d: dict) -> pd.DataFrame:
    q = df["t"].to_numpy()
    for k in ("2", "2_5", "2_10"):
        b, a = at(d["t"], d[f"b{k}"], q, np.nan), at(d["t"], d[f"a{k}"], q, np.nan)
        df[f"d_lb{k}"], df[f"d_la{k}"] = np.log1p(b), np.log1p(a)
        df[f"d_imb{k}"] = (b - a) / np.maximum(b + a, 1e-9)
    return df


def main() -> None:
    with np.load(CACHE / "depth.npz") as z:
        d = {k: z[k] for k in z.files}
    df = load("test3", frac=0.8, seed=9)
    df = df[(df["t"] > d["t"][0] + 60) & (df["t"] < d["t"][-1])]
    df = add_depth(df, d)
    cut = np.quantile(df["t"], 2 / 3)
    tr, te = df[df["t"] < cut], df[df["t"] >= cut + 300]
    rows = []
    for dep in (False, True):
        feats = [c for c in features(df) if dep or not c.startswith("d_")]
        Xtr, Xte = clean(tr[feats].to_numpy()), clean(te[feats].to_numpy())
        r = {"depth": dep, "n_feat": len(feats), "rows_test": len(te)}
        for h in (150, 300):
            ytr, yte = tr[f"y_pm{h}"].to_numpy(float), te[f"y_pm{h}"].to_numpy(float)
            ttr, tte = (tr["p_spr"] == 1).to_numpy(), (te["p_spr"] == 1).to_numpy()
            mtr, mte = ttr & (np.abs(ytr) >= 0.01), tte & (np.abs(yte) >= 0.01)
            g = gbdt(150).fit(Xtr[ttr], mtr[ttr])
            r[f"perp_timing_auc_{h}"] = roc_auc_score(mte[tte], g.predict_proba(Xte[tte])[:, 1])
        gt = lambda x: (x["pm_mid"].between(0.05, 0.95) & (x["secs_left"] >= 20)).to_numpy()  # noqa: E731
        ytr, yte = target(tr, 0, 1), target(te, 0, 1)
        mtr, mte = gt(tr) & (np.abs(ytr) >= 1), gt(te) & (np.abs(yte) >= 1)
        g = gbdt(200).fit(Xtr[mtr], ytr[mtr] > 0)
        r["post150_1s_auc"] = roc_auc_score(yte[mte] > 0, g.predict_proba(Xte[mte])[:, 1])
        print(r, flush=True)
        rows.append(r)
    out = pd.DataFrame(rows)
    (OUT / "depth_study.md").write_text(md(out))
    print(md(out))


if __name__ == "__main__":
    main()
