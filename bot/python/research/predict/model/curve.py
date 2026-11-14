"""Horizon decay curve: how predictable are the Binance perp / spot mid and the Polymarket
5m mid at t + h from what we have received by t (receipt clock).

    nice -n 10 python3 -m research.predict.model.curve [--frac 0.3]

Per target and horizon: share of rows where it moves (perp / spot: any tick; Polymarket:
>= 1 c), a timing AUC (will it move at all, GBDT), and the direction AUC on the rows where it
moved for each learner (literature baselines, the leaders' rule, linear, GBDT), plus the
direction accuracy of the 20% most confident GBDT calls. Train = run 2 first 12 h, scored on
run 2 last 12 h (select). Writes data/out/predict/curve.csv and curve.md."""
from __future__ import annotations

import argparse

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

from .. import H_MS, OUT
from .data import features, load
from ..report.md import md
from .learners import BASE_COLS, clean, gbdt, leader_score, logit

TARGETS = {"perp": ("y_pm", 1e-6), "spot": ("y_sm", 1e-6), "poly": ("y_dm", 0.999)}


def _auc(y, s):
    return roc_auc_score(y, s) if len(np.unique(y)) == 2 else np.nan


TIGHT = {"perp": ("p_spr", 0.01), "spot": ("s_spr", 0.001)}  # 1-tick spread, >= ~1 full tick


def run(tr: pd.DataFrame, te: pd.DataFrame, feats: list[str], tight: bool = False) -> list[dict]:
    rows = []
    Xtr_all, Xte_all = clean(tr[feats].to_numpy()), clean(te[feats].to_numpy())
    for name, (pre, thr) in TARGETS.items():
        for h in H_MS:
            ytr, yte = tr[f"{pre}{h}"].to_numpy(float), te[f"{pre}{h}"].to_numpy(float)
            oktr, okte = np.isfinite(ytr), np.isfinite(yte)
            if tight and name in TIGHT:
                col, thr = TIGHT[name]
                oktr &= (tr[col] == 1).to_numpy()
                okte &= (te[col] == 1).to_numpy()
            if name == "poly":
                oktr &= tr["pm_mid"].between(0.05, 0.95).to_numpy()
                okte &= te["pm_mid"].between(0.05, 0.95).to_numpy()
            mtr, mte = oktr & (np.abs(ytr) >= thr), okte & (np.abs(yte) >= thr)
            r = {"target": name, "h_ms": h, "p_move": mte.sum() / okte.sum(), "n_dir": int(mte.sum())}
            tm = gbdt(150).fit(Xtr_all[oktr], mtr[oktr])
            r["auc_timing"] = _auc(mte[okte], tm.predict_proba(Xte_all[okte])[:, 1])
            d_tr, d_te = ytr[mtr] > 0, yte[mte] > 0
            r["auc_leader"] = _auc(d_te, leader_score(te[mte]))
            for b, cols in BASE_COLS.items():
                m = logit().fit(clean(tr.loc[mtr, cols].to_numpy()), d_tr)
                r[f"auc_{b}"] = _auc(d_te, m.predict_proba(clean(te.loc[mte, cols].to_numpy()))[:, 1])
            m = logit(0.3).fit(Xtr_all[mtr], d_tr)
            r["auc_linear"] = _auc(d_te, m.predict_proba(Xte_all[mte])[:, 1])
            g = gbdt().fit(Xtr_all[mtr], d_tr)
            p = g.predict_proba(Xte_all[mte])[:, 1]
            r["auc_gbdt"] = _auc(d_te, p)
            conf = np.abs(p - 0.5)
            top = conf >= np.quantile(conf, 0.8)
            r["acc_top20"] = float(((p[top] > 0.5) == d_te[top]).mean())
            r["acc_all"] = float(((p > 0.5) == d_te).mean())
            print({k: (round(v, 3) if isinstance(v, float) else v) for k, v in r.items()}, flush=True)
            rows.append(r)
    return rows


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--frac", type=float, default=0.3)
    ap.add_argument("--tag", default="")
    ap.add_argument("--train", default="train")
    ap.add_argument("--test", default="select")
    ap.add_argument("--tight", action="store_true",
                    help="only rows with a 1-tick spread, moves of >= 1 full tick (no refills)")
    a = ap.parse_args()
    tr = load(a.train, frac=a.frac, seed=1)
    te = load(a.test, frac=min(1.0, 2 * a.frac), seed=2)
    feats = features(tr)
    print("rows", len(tr), len(te), "features", len(feats), flush=True)
    out = pd.DataFrame(run(tr, te, feats, a.tight))
    OUT.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT / f"curve{a.tag}.csv", index=False)
    (OUT / f"curve{a.tag}.md").write_text(md(out))


if __name__ == "__main__":
    main()
