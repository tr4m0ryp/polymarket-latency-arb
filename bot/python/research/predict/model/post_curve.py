"""Exploitable-part decay: how predictable is the Polymarket mid move AFTER the match time
(t + L + 150 ms, i.e. 110 / 150 / 200 ms after the decision) over the next 1 / 3 / 10 s,
from features at t. This is the move a taker held 150 ms can still capture.

    nice -n 10 python3 -m research.predict.model.post_curve"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

from .. import HOLD, L_MS, OUT
from ..report.md import md
from .data import features, load
from .learners import clean, gbdt, leader_score


def target(df: pd.DataFrame, L: int, k: int) -> np.ndarray:
    mid_tm = (df[f"x_ba{L}"].to_numpy(float) + df[f"x_bb{L}"].to_numpy(float)) / 200
    ok = (df[f"x_ba{L}"] < 100) & (df[f"x_bb{L}"] > 0) & (df[f"x_bad{L}"] == 0)
    return np.where(ok, 100 * (df[f"x_m{k}_{L}"].to_numpy(float) - mid_tm), np.nan)


def main() -> None:
    tr, te = load("train", frac=0.3, seed=1), load("select", frac=0.5, seed=2)
    g = lambda d: (d["pm_mid"].between(0.05, 0.95) & (d["secs_left"] >= 20)).to_numpy()  # noqa: E731
    tr, te = tr[g(tr)], te[g(te)]
    feats = features(tr)
    Xtr, Xte = clean(tr[feats].to_numpy()), clean(te[feats].to_numpy())
    rows = []
    for L in L_MS:
        for k in (1, 3, 10):
            ytr, yte = target(tr, L, k), target(te, L, k)
            mtr, mte = np.abs(ytr) >= 1, np.abs(yte) >= 1
            m = gbdt(200).fit(Xtr[mtr], ytr[mtr] > 0)
            p = m.predict_proba(Xte[mte])[:, 1]
            d = yte[mte] > 0
            conf = np.abs(p - 0.5)
            top = conf >= np.quantile(conf, 0.9)
            r = {"offset_ms": int(L + 1000 * HOLD), "window_s": k, "p_move_1c": float(mte.mean()),
                 "auc_gbdt": roc_auc_score(d, p), "auc_leader": roc_auc_score(d, leader_score(te[mte])),
                 "acc_top10": float(((p[top] > 0.5) == d[top]).mean()),
                 "mean_abs_move_c": float(np.nanmean(np.abs(yte[mte])))}
            print(r, flush=True)
            rows.append(r)
    out = pd.DataFrame(rows)
    (OUT / "post_curve.md").write_text(md(out))
    print(md(out))


if __name__ == "__main__":
    main()
