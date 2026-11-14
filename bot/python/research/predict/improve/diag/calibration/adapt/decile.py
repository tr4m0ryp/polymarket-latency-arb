"""Calibration by prediction bin and activity regime, frozen v1 vs the adaptive-gain refit.

    python3 -m research.predict.improve.diag.calibration.adapt.decile

On the side each model would buy (adapt/rowstats.chosen), per L x window x regime (busy index
< 1 / >= 1, the extreme-activity regime of the regime-margin arms): fixed prediction bins
(c/share; train deciles put the whole firing region inside the top decile, so the bins zoom
on it), mean pred, realised 1 s and 10 s value (c/share) and rows. Writes OUT/adapt_decile.csv
and adapt_decile.md (bins from 1 c up, the rows that can fire)."""
from __future__ import annotations

import numpy as np
import pandas as pd

from .....report.md import md
from .. import OUT
from .rowstats import chosen, table

WINS = ("train", "select", "dev3", "final", "ext")
MODELS = ("v1", "agc")
BINS = np.array([0.0, 1.0, 2.0, 3.0, 4.0, 6.0, 10.0]) / 100
LABEL = ["<0", "0-1", "1-2", "2-3", "3-4", "4-6", "6-10", ">=10"]


def main() -> None:
    tabs = {w: table(w) for w in WINS}
    out = []
    for L in (0, -40):
        for name in MODELS:
            col = f"p_{name}_L{L}"
            cs = {w: chosen(tabs[w], col, L) for w in WINS}
            for w, c in cs.items():
                c = c.assign(dec=np.searchsorted(BINS, c["pred"].to_numpy(), side="right"),
                             reg=np.where(c["busy"] >= 1.0, "busy", "quiet"))
                g = c.groupby(["reg", "dec"]).agg(rows=("pred", "size"), pred=("pred", "mean"), r1=("r1", "mean"),
                                                  r10=("r10", "mean")).reset_index()
                g[["pred", "r1", "r10"]] *= 100
                g["gap1"] = g["r1"] - g["pred"]
                out.append(g.assign(model=name, L=L, win=w))
    t = pd.concat(out, ignore_index=True)
    t.to_csv(OUT / "adapt_decile.csv", index=False)
    t["bin"] = [LABEL[k] for k in t["dec"]]
    s = t[t["dec"] >= 2].copy()
    s["cell"] = [f"{p:.1f} / {r:.1f} ({n:,})" for p, r, n in zip(s["pred"], s["r1"], s["rows"])]
    p = s.pivot_table(index=["L", "reg", "dec", "bin", "model"], columns="win", values="cell", aggfunc="first")
    txt = ["# Calibration by prediction bin and regime: pred / realised 1 s c/share (rows), v1 vs agc\n",
           "Fixed bins of the prediction (c/share); regime = busy index >= 1.0.\n",
           md(p[list(WINS)].reset_index().drop(columns="dec"))]
    (OUT / "adapt_decile.md").write_text("\n".join(txt))


if __name__ == "__main__":
    main()
