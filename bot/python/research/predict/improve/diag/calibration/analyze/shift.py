"""Covariate shift between run 2 train and the later windows.

    OMP_NUM_THREADS=2 nice -n 10 python3 -m research.predict.improve.diag.calibration.analyze.shift

On the random 6% row sample of each window (rows.build `rnd`): per feature the population
stability index (PSI, 10 train-quantile bins), the KS statistic and the standardised mean
shift; a domain classifier (GBDT, train vs window, 2-fold split by market) gives the AUC of
"which window is this row from" and, by grouped permutation on the held-out fold, which
feature groups carry the shift. Also the same PSI on the firing rows (v1_L0 pred >= 3 c).
Writes OUT/shift.md and OUT/shift_psi.csv."""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import ks_2samp
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score

from .. import CACHE, OUT
from ..safe import check, start_of
from .....model.store import load_model
from .....report.md import md
from .groups import GROUPS, group_cols

WINS = ("select", "dev3", "final", "ext")
REG = ["bn10", "bn60", "rv1", "rv10", "rv60", "pm10", "pmtop10", "pmtr60", "jump10"]


def feat(win: str) -> pd.DataFrame:
    d = pd.read_pickle(CACHE / f"feat-{win}.pkl")
    check(start_of(d["m"].unique()))
    return d


def psi(a: np.ndarray, b: np.ndarray, q: int = 10) -> float:
    a, b = a[np.isfinite(a)], b[np.isfinite(b)]
    e = np.unique(np.quantile(a, np.linspace(0, 1, q + 1)[1:-1]))
    pa = np.bincount(np.searchsorted(e, a, side="right"), minlength=len(e) + 1) / len(a)
    pb = np.bincount(np.searchsorted(e, b, side="right"), minlength=len(e) + 1) / len(b)
    pa, pb = np.maximum(pa, 1e-4), np.maximum(pb, 1e-4)
    return float(np.sum((pb - pa) * np.log(pb / pa)))


def per_feature(tr: pd.DataFrame, te: pd.DataFrame, cols) -> pd.DataFrame:
    out = []
    for c in cols:
        a, b = tr[c].to_numpy(float), te[c].to_numpy(float)
        sd = np.nanstd(a) or 1.0
        out.append({"feature": c, "psi": psi(a, b), "ks": ks_2samp(a[np.isfinite(a)], b[np.isfinite(b)]).statistic,
                    "smd": (np.nanmean(b) - np.nanmean(a)) / sd})
    return pd.DataFrame(out)


def domain(tr: pd.DataFrame, te: pd.DataFrame, vf: list[str], n: int = 60000, seed: int = 0):
    rng = np.random.default_rng(seed)
    a = tr.iloc[rng.permutation(len(tr))[:n]]
    b = te.iloc[rng.permutation(len(te))[:n]]
    X = np.nan_to_num(pd.concat([a[vf], b[vf]]).to_numpy(np.float32))
    y = np.r_[np.zeros(len(a)), np.ones(len(b))]
    m = np.r_[a["m"].to_numpy(), b["m"].to_numpy()]
    fold = (pd.util.hash_array(m.astype(np.int64)) % 2).astype(int)
    aucs, drops = [], {g: [] for g in GROUPS}
    for k in (0, 1):
        clf = HistGradientBoostingClassifier(max_iter=150, max_leaf_nodes=15, learning_rate=0.1,
                                             random_state=seed).fit(X[fold != k], y[fold != k])
        Xt, yt = X[fold == k], y[fold == k]
        base = roc_auc_score(yt, clf.predict_proba(Xt)[:, 1])
        aucs.append(base)
        for g in GROUPS:
            ix = group_cols(vf, g)
            if not ix:
                continue
            Xs = Xt.copy()
            Xs[:, ix] = Xt[rng.permutation(len(Xt))][:, ix]
            drops[g].append(base - roc_auc_score(yt, clf.predict_proba(Xs)[:, 1]))
    return float(np.mean(aucs)), {g: float(np.mean(v)) for g, v in drops.items() if v}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    vf = load_model("v1_L0")["vf"]
    tr = feat("train")
    trr = tr[tr["rnd"]]
    txt, allp, dom = ["# Covariate shift: run 2 train vs later windows\n"], [], []
    for w in WINS:
        te = feat(w)
        ter = te[te["rnd"]]
        p = per_feature(trr, ter, vf + REG).assign(win=w)
        f3 = per_feature(tr[tr["p_v1_L0"] >= 0.03], te[te["p_v1_L0"] >= 0.03], vf + REG)
        p["psi_fire"] = f3["psi"].to_numpy()
        p["smd_fire"] = f3["smd"].to_numpy()
        allp.append(p)
        auc, drops = domain(trr, ter, vf)
        dom.append({"win": w, "domain_auc": auc, **{f"drop:{g}": v for g, v in drops.items()}})
        print(w, "domain AUC", round(auc, 3), flush=True)
    P = pd.concat(allp, ignore_index=True)
    P.to_csv(OUT / "shift_psi.csv", index=False)
    D = pd.DataFrame(dom)
    D.to_csv(OUT / "shift_domain.csv", index=False)
    txt.append("\n## Domain classifier (train vs window, random rows; AUC 0.5 = no shift)\n")
    txt.append(md(D.T.reset_index(), 3))
    for w in WINS:
        s = P[P["win"] == w].sort_values("psi", ascending=False).head(15)
        txt.append(f"\n## Top-15 PSI features, train vs {w} (PSI > 0.25 = major shift)\n")
        txt.append(md(s[["feature", "psi", "ks", "smd", "psi_fire", "smd_fire"]], 3))
    (OUT / "shift.md").write_text("\n".join(txt))


if __name__ == "__main__":
    main()
