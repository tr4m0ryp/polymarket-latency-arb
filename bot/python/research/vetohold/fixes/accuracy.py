"""Out-of-sample accuracy of the frozen i* predictor (test hours) and what carries it.

Accuracy: MAE, R^2 and Spearman of predicted vs measured i* on test orders, against the
selection-hours median as a constant baseline. Importance: permutation importance on test
(MAE increase, 5 repeats). Partial dependence of the top 4 features on selection orders.

    PYTHONPATH=. python3 -m research.vetohold.fixes.accuracy -> data/out/vetohold/istar-model.md"""
from __future__ import annotations

import pickle

import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.inspection import partial_dependence, permutation_importance

from research.predict.report.md import md

from .. import OUT
from .models import istar_target
from .prereg import selection
from .score import test_rows


def main():
    fz = pickle.loads((OUT / "prereg.pkl").read_bytes())
    m, cols = fz["models"]["istar"], fz["cols"]
    se, te = selection(), test_rows()
    Xt, yt = te[cols].to_numpy(float), istar_target(te)
    p = m.predict(Xt)
    c = np.median(istar_target(se))
    acc = []
    for name, yh in (("model", p), ("selection median", np.full(len(yt), c))):
        acc.append({"predictor": name, "MAE c": np.mean(np.abs(yh - yt)),
                    "R2": 1 - np.sum((yt - yh) ** 2) / np.sum((yt - yt.mean()) ** 2),
                    "spearman": spearmanr(yh, yt)[0] if np.std(yh) > 0 else np.nan,
                    "share |err| <= 2 c %": np.mean(np.abs(yh - yt) <= 2) * 100})
    pi = permutation_importance(m, Xt, yt, scoring="neg_mean_absolute_error", n_repeats=5, random_state=0)
    imp = pd.DataFrame({"feature": cols, "MAE increase c": pi.importances_mean, "sd": pi.importances_std})
    imp = imp.sort_values("MAE increase c", ascending=False)
    out = ["# i* predictor: accuracy on test hours\n", md(pd.DataFrame(acc), 2),
           "\n## Permutation importance (test)\n", md(imp.head(12), 3), "\n## Partial dependence (selection)\n"]
    Xs = se[cols].to_numpy(float)
    for f in imp["feature"].head(4):
        r = partial_dependence(m, Xs, [cols.index(f)], grid_resolution=8, percentiles=(0.05, 0.95))
        g, a = r["grid_values"][0], r["average"][0]
        out.append(f"- {f}: " + ", ".join(f"{x:.3g} -> {y:.1f} c" for x, y in zip(g, a)))
    (OUT / "istar-model.md").write_text("\n".join(out) + "\n")
    print("\n".join(out))


if __name__ == "__main__":
    main()
