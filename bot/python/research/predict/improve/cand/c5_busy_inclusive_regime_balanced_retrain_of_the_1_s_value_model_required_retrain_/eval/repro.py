"""Pipeline check: the C5 fit path (Fold.load_rows + stacked + the v1 learner) on v1's own rows
(run 2 train, frac 0.5, seed 1) must reproduce the frozen v1_L0 predictions; any C5 loss vs
the frozen arm is then due to the rows / weights, not the code path. Scores a few allowed
markets of each window and prints the max absolute prediction difference.

    OMP_NUM_THREADS=2 nice -n 10 python3 -m <this package>.eval.repro"""
from __future__ import annotations

import numpy as np

from .....model.learners import clean, gbdt_reg
from .....model.stack import stacked
from .....model.store import load_model, predict_sides
from ....harness import windows as W
from ....harness.api import Market
from ....harness.fold import Fold


def main() -> None:
    rows = Fold("A").load_rows(windows=("train",), frac=0.5, seed=1)
    tr, vf = stacked(rows)
    del rows
    w = np.isfinite(tr["v1_0"].to_numpy()) & (tr["bad0"] == 0).to_numpy()
    print("rows", int(w.sum()), "(v1 meta: 538266)", flush=True)
    m = gbdt_reg(max_iter=200, leaves=15, lr=0.05, min_leaf=200).fit(
        clean(tr.loc[w, vf].to_numpy()), np.clip(tr.loc[w, "v1_0"].to_numpy(float), -0.3, 0.3))
    v1, mine = load_model("v1_L0"), {"model": m, "vf": vf}
    worst = 0.0
    for win in ("select", "dev3", "test3r1", "ext"):
        for i in W.ids(win)[:3]:
            mk = Market(i, {"start": W.starts(win)[i], "end": W.starts(win)[i] + 300})
            a, b = predict_sides(mk.tab, v1), predict_sides(mk.tab, mine)
            worst = max(worst, float(np.abs(a[0] - b[0]).max()), float(np.abs(a[1] - b[1]).max()))
    print(f"max |v1_L0 - refit on v1 rows| over 12 markets: {worst:.2e}")


if __name__ == "__main__":
    main()
