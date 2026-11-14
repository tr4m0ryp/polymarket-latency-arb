"""Does the run-3 perp trade stream add anything over the books? Run 3 dev hours only:
train on the first 6 h, score on the last 4 h, with and without the perp trade-flow
features (ft_*). Targets: perp mid direction (1-tick spread rows, full-tick moves) and
timing at 150 / 300 ms, the post-match Polymarket move direction (offset 150 ms, 1 s), and
the value model's realized 10 s value at a fixed budget.

    nice -n 10 python3 -m research.predict.model.ftr_test"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

from .. import OUT, RUN3
from ..report.md import md
from .data import features, load
from .learners import clean, gbdt, gbdt_reg
from .post_curve import target
from .stack import stacked
from .value_sweep import prefilter

CUT = RUN3 + 6 * 3600 + 300


def main() -> None:
    df = load("dev3", frac=0.6, seed=4)
    tr, te = df[df["t"] < CUT], df[df["t"] >= CUT + 300]
    rows = []
    for ft in (False, True):
        feats = features(df, perp_trades=ft)
        Xtr, Xte = clean(tr[feats].to_numpy()), clean(te[feats].to_numpy())
        r = {"perp_trades": ft, "n_feat": len(feats)}
        for h in (150, 300):
            ytr, yte = tr[f"y_pm{h}"].to_numpy(float), te[f"y_pm{h}"].to_numpy(float)
            ttr, tte = (tr["p_spr"] == 1).to_numpy(), (te["p_spr"] == 1).to_numpy()
            mtr, mte = ttr & (np.abs(ytr) >= 0.01), tte & (np.abs(yte) >= 0.01)
            g = gbdt(150).fit(Xtr[ttr], mtr[ttr])
            r[f"perp_timing_auc_{h}"] = roc_auc_score(mte[tte], g.predict_proba(Xte[tte])[:, 1])
            g = gbdt(150).fit(Xtr[mtr], ytr[mtr] > 0)
            r[f"perp_dir_auc_{h}"] = roc_auc_score(yte[mte] > 0, g.predict_proba(Xte[mte])[:, 1])
        gt = lambda d: (d["pm_mid"].between(0.05, 0.95) & (d["secs_left"] >= 20)).to_numpy()  # noqa: E731
        ytr, yte = target(tr, 0, 1), target(te, 0, 1)
        mtr, mte = gt(tr) & (np.abs(ytr) >= 1), gt(te) & (np.abs(yte) >= 1)
        g = gbdt(200).fit(Xtr[mtr], ytr[mtr] > 0)
        r["post150_1s_auc"] = roc_auc_score(yte[mte] > 0, g.predict_proba(Xte[mte])[:, 1])
        s_tr, vf = stacked(tr.copy(), ft)
        s_te, _ = stacked(te.copy(), ft)
        w = np.isfinite(s_tr["v3_0"].to_numpy()) & prefilter(s_tr) & (s_tr["bad0"] == 0).to_numpy()
        m = gbdt_reg(200, 15, 0.05, min_leaf=200).fit(clean(s_tr.loc[w, vf].to_numpy()),
                                                      np.clip(s_tr.loc[w, "v3_0"].to_numpy(float), -.3, .3))
        p = np.where(prefilter(s_te), m.predict(clean(s_te[vf].to_numpy())), -1)
        real = s_te["v10_0"].to_numpy(float)
        top = np.argsort(-p)[:2000]
        r["value_top2000_c_sh"] = 100 * np.nanmean(real[top])
        print(r, flush=True)
        rows.append(r)
    out = pd.DataFrame(rows)
    (OUT / "ftr_test.md").write_text(md(out))
    print(md(out))


if __name__ == "__main__":
    main()
