"""Paired comparisons between C5 arms (not vs the frozen arm): what the busy-inclusive rows, the
regime weights and the projection add at EQUAL refit variance. Each arm is scored CV-style (fold
A's model on A's evaluate windows, fold B's on B's), from the memoised simulations (no new
simulation when every arm ran before). Paired 10 s markout $/day difference, 95% market
bootstrap (research/strategy/eval/metrics.paired, 2000 draws, seed 2), L = 0.

    python3 -m <this package>.eval.control"""
from __future__ import annotations

import pandas as pd

from .....report.md import md
from ......strategy.eval.metrics import paired
from ....harness import windows as W
from ....harness.score import sets
from ..plan import VAR4, _spec, specs_fn
from . import OUT_DIR, multiview

Q = [_spec("tronly", 0.03), _spec("plain", 0.03), _spec("bal", 0.03), _spec("bal", 0.03, True)]
PAIRS = [("rf_plain_m3", "rf_tronly_m3", "added choose-window rows (unweighted)"),
         ("rf_bal_m3", "rf_tronly_m3", "added rows + regime-balanced weights"),
         ("rf_bal_coh_m3", "rf_tronly_m3", "added rows + weights + projection"),
         ("rf_bal_m3", "rf_plain_m3", "regime-balanced weights alone"),
         ("rf_bal_coh_m3", "rf_bal_m3", "identity projection alone (kill test 3)"),
         ("rf_bal_f50_m3", "rf_plain_f50_m3", "weights alone, v1's rows + choose rows (frac 0.5)"),
         ("rf_bal_coh_f50_m3", "rf_bal_f50_m3", "projection alone, frac 0.5")]
SETS = ["A:eval", "B:eval", "CV:all", "A:ext", "A:busy15", "CV:busyQ"]


def _both(fold):
    return specs_fn(Q)(fold) + specs_fn(VAR4, 0.5)(fold)


def main() -> None:
    sim, keys, _, act, _ = multiview.simulate(_both, (0,), ("base", "comp"))
    S = sets.build(act)

    def cv(name):
        parts = []
        for f, (_, ev) in W.FOLDS.items():
            parts.append(sim.agg(keys[(f, name)], sorted(i for w in ev for i in W.ids(w)), name))
        return pd.concat(parts, ignore_index=True)
    rows = []
    for a, b, what in PAIRS:
        A, B = cv(a), cv(b)
        for var in ("base", "comp"):
            r = {"candidate": a, "control": b, "isolates": what, "var": var}
            for s in SETS:
                ids = S[s]
                x = A[(A["var"] == var) & A["m"].isin(ids)]
                y = B[(B["var"] == var) & B["m"].isin(ids)]
                p = paired(x, y, sorted(ids), col="mk10v")
                r[s] = f"{p['diff_day']:+,.0f} [{p['lo']:+,.0f}, {p['hi']:+,.0f}]"
            rows.append(r)
    t = pd.DataFrame(rows)
    txt = ("# C5 paired comparisons between refits (10 s markout $/day, 95% market bootstrap, L = 0)\n\n"
           + md(t))
    (OUT_DIR / "control.md").write_text(txt)
    print(txt)


if __name__ == "__main__":
    main()
