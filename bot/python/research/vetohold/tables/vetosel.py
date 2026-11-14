"""(d) Does the veto pick the signals whose depth makers pull? Every trigger row of the 48 h
(label files), split by v1's verdict, at i = 0 and 60 sh: survival, fill, value per intended
share under each hold, and the book state at decision.

    PYTHONPATH=. python3 -m research.vetohold.tables.vetosel -> data/out/vetohold/vetosel.md"""
from __future__ import annotations

import numpy as np
import pandas as pd

from research.predict.report.md import md

from .. import OUT
from ..label.data import load, v1_pred


def main():
    d, _ = load()
    v = v1_pred(d)
    bins = [("vetoed: v1 prefers other side", ~np.isfinite(v)), ("vetoed: v1 value < 0", np.isfinite(v) & (v < 0)),
            ("vetoed: 0 <= v1 < 2 c", (v >= 0) & (v < 0.02)), ("kept: 2-3 c", (v >= 0.02) & (v < 0.03)),
            ("kept: 3-5 c", (v >= 0.03) & (v < 0.05)), ("kept: >= 5 c", v >= 0.05)]
    t = []
    for name, m in bins:
        g = d[m]
        t.append({"trigger rows": name, "n": len(g), "share %": m.mean() * 100,
                  "surv i=0 % (real)": g["surv_real"].mean() * 100, "fill % (real)": g["fill_real"].mean() * 100,
                  "value c/sh real": g["y_real"].mean() * 100, "value c/sh 250 ms": g["y_h250"].mean() * 100,
                  "value if filled c/sh": (g["y_real"].sum() / max(g["surv_real"].sum(), 1e-9)) * 100,
                  "dep0 med": g["x_dep0"].median(), "age med s": g["x_age"].median(),
                  "feed lag med ms": g["x_rlag"].median() * 1e3})
    out = ["# Veto selection vs depth survival (all trigger rows, i = 0, 60 sh)\n", md(pd.DataFrame(t), 2)]
    (OUT / "vetosel.md").write_text("\n".join(out) + "\n")
    print("\n".join(out))


if __name__ == "__main__":
    main()
