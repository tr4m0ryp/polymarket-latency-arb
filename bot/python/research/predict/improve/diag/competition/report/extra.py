"""Second-round tables: latency-jitter fill models (jitter.py), anatomy of the losing fills
(losers.py), realized markout by predicted value (why edge-keyed size works) ->
data/out/predict/improve/diag-competition-extra.md.

    python3 -m research.predict.improve.diag.competition.report.extra"""
from __future__ import annotations

import pandas as pd

from .....report.md import md
from .. import OUT
from .analyze import _fmt
from .boot import load, markets
from .jitter import table as jitter_table
from .losers import anatomy

DEPLOYED = (("vt_v1_m0.03_any", 0), ("vt_v1_m0.02_trigger", 0), ("vt_v1_m0.02_trigger", -40), ("micf", 0))
BINS = [0, 0.03, 0.04, 0.05, 0.07, 0.10, 1.0]


def by_edge(o: pd.DataFrame, ids: dict, groups=("unseen", "busy")) -> pd.DataFrame:
    rows = []
    for g in groups:
        mk = markets(ids, g)
        for arm, L in DEPLOYED[:3]:
            a = o[(o["arm"] == arm) & (o["L"] == L) & o["m"].isin(mk) & (o["base_got"] > 0)]
            for b, s in a.groupby(pd.cut(a["edge"], BINS), observed=True):
                rows.append({"group": g, "arm": arm, "L": L, "predicted c/sh": str(b), "fills": len(s),
                             "sh/fill": s["base_got"].mean(),
                             "mk10 c/sh": 100 * s["base_mk10v"].sum() / s["base_got"].sum(),
                             "comp mk10 c/sh": 100 * s["comp_mk10v"].sum() / max(s["comp_got"].sum(), 1e-9),
                             "taken <= 50 ms": s["tr50"].sum() / s["base_got"].sum()})
    return pd.DataFrame(rows)


def main() -> None:
    o, ids = load()
    arms = ("micf", "vt_v1_m0.03_any", "vt_v1_m0.02_trigger")
    jt = pd.concat([jitter_table(o, ids, arms, L) for L in (0, -40)], ignore_index=True)
    an = anatomy(o, ids, DEPLOYED + (("vt_v3p_m0.02_any", 0),))
    be = by_edge(o, ids)
    an.to_csv(OUT / "diag-competition-losers.csv", index=False)
    txt = ("# Competition diagnostic, second round\n\n## Latency-jitter fill models\n\n" + md(_fmt(jt).fillna(""), 1)
           + "\n\n## Losing vs winning fills (base fills)\n\n" + md(an, 2)
           + "\n\n## Realized markout by predicted value (base fills)\n\n" + md(be, 2))
    (OUT / "diag-competition-extra.md").write_text(txt)
    print("wrote", OUT / "diag-competition-extra.md")


if __name__ == "__main__":
    main()
