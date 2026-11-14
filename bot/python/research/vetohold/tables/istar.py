"""Needed offset i*: the smallest limit offset that would have filled each veto order.

i*1 = first side-frame ask with depth at the venue match instant minus the seen ask (c);
i*60 = offset where cumulative depth reaches the full 60 sh. Measured at the median hold
(`q50`, one value per order) and as the mean over the 16 live-hold draws (`real`).
The key question: does i* grow with the signal (model edge, realized move) so that the edge
left after paying i* stays <= 0?

    PYTHONPATH=. python3 -m research.vetohold.tables.istar -> data/out/vetohold/istar.md"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

from research.predict.report.md import md

from .. import OUT, VETO
from ..fixes.models import istar_target
from .common import rows

FEE = lambda p: 0.07 * p * (1 - p)  # noqa: E731


def dist(x: pd.Series) -> dict:
    x = x.to_numpy(float)
    f = np.isfinite(x)
    q = np.percentile(x[f], [10, 25, 50, 75, 90])
    return {"n": len(x), "p10": q[0], "p25": q[1], "p50": q[2], "p75": q[3], "p90": q[4],
            "<=0 %": np.mean(x[f] <= 0) * 100, "<=2 %": np.mean(x[f] <= 2) * 100,
            "<=5 %": np.mean(x[f] <= 5) * 100, "<=10 %": np.mean(x[f] <= 10) * 100,
            "none in +30 c %": np.mean(~f) * 100}


def by_bin(v: pd.DataFrame, col: str, lab: str) -> pd.DataFrame:
    v = v.assign(b=pd.qcut(v[col].rank(method="first"), 5, labels=False))
    out = []
    for b, g in v.groupby("b"):
        i = g["istar"] / 100
        net = g["mk"] - g["seen"] - i - FEE(g["seen"] + i)
        out.append({lab: f"Q{b + 1} ({g[col].median():+.3f})", "edge c": g["edge"].mean() * 100,
                    "hold-free value c": g["mk_inst"].mean() * 100, "i* c": g["istar"].mean(),
                    "i* p50 c": g["istar"].median(), "edge - i* c": (g["edge"] - i).mean() * 100,
                    "realized at seen + i* c": net.mean() * 100,
                    "edge > i* %": (g["edge"] > i).mean() * 100, "realized > 0 at i* %": (net > 0).mean() * 100})
    return pd.DataFrame(out)


def main():
    d = rows()
    v = d[(d["arm"] == VETO) & (d["scen"] == "real")].copy()
    q = d[(d["arm"] == VETO) & (d["scen"] == "q50")]
    v["istar"] = np.minimum(istar_target(v), 31)
    out = ["# Needed offset i* (veto orders)\n", "## Distribution (c)\n",
           md(pd.DataFrame([dict(measure=m, **dist(s)) for m, s in (
               ("i*1 at median hold", q["istar1"]), ("i*60 at median hold", q["istar60"]),
               ("i*1 mean over live-hold draws", v["istar1"]))]), 1)]
    fc = sorted(c for c in v.columns if c.startswith("f_"))
    sp = [{"feature": c, "spearman with i*": spearmanr(v[c], v["istar"], nan_policy="omit")[0]} for c in fc]
    sp = pd.DataFrame(sp).sort_values("spearman with i*", key=np.abs, ascending=False)
    out += ["\n## What i* moves with (Spearman, all veto orders, real hold)\n", md(sp.head(15), 3)]
    out += ["\n## By model edge quintile\n", md(by_bin(v, "edge", "edge bin"), 1),
            "\n## By realized hold-free value quintile (what the move turned out to be)\n",
            md(by_bin(v, "mk_inst", "value bin"), 1)]
    x, y = v["mk"] - v["seen"], v["istar"] / 100
    b = np.polyfit(x, y, 1)
    xe = np.polyfit(v["edge"], y, 1)
    out.append(f"\n- slope of i* on the realized move (mk - seen): {b[0]:+.2f} (intercept {b[1] * 100:+.1f} c)"
               f"\n- slope of i* on the model edge: {xe[0]:+.2f} (intercept {xe[1] * 100:+.1f} c)")
    (OUT / "istar.md").write_text("\n".join(out) + "\n")
    print("\n".join(out))


if __name__ == "__main__":
    main()
