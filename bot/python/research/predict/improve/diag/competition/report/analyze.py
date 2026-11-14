"""Tables of the competition diagnostic -> data/out/predict/improve/diag-competition-tables.md
(+ CSVs). Reads data/cache/predict/improve/competition/orders-<win>.pkl (run.py).

    python3 -m research.predict.improve.diag.competition.report.analyze"""
from __future__ import annotations

import pandas as pd

from .....report.md import md
from .. import OUT
from .boot import fmt, load
from .expo import bad_markets, by_split, exposure
from .whatif import fill_models, race_curve, size_rules

DEPLOYED = ("vt_v1_m0.03_any", "vt_v1_m0.02_trigger")
ALL = ("micf",) + DEPLOYED + ("vt_v3p_m0.02_any",)
RULES = ("s20", "s40", "s100", "dk0.5", "dk1", "dk2", "rv1_30", "rv1_0", "rv3_30", "rv3_0", "dk1_rv1",
         "sl0", "sl1")
FILLS = ("base", "comp", "e+10", "e+25", "e+50", "e-25")


def _fmt(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for c in df.columns:
        if df[c].map(lambda v: isinstance(v, tuple)).any():
            nd = 1 if "c/$" in c else 0
            df[c] = df[c].map(lambda v: fmt(v[:3], nd) + (f" P<=0 {v[3]:.2f}" if len(v) > 3 else "")
                              if isinstance(v, tuple) else "")
    return df


def main() -> None:
    o, ids = load()
    OUT.mkdir(parents=True, exist_ok=True)
    out = ["# Competition diagnostic: tables\n",
           f"Orders: {len(o):,}; markets: " + ", ".join(f"{k} {len(v)}" for k, v in ids.items()) + "\n"]
    for L in (0, -40):
        arms = ALL if L == 0 else ALL[:3]
        e = exposure(o, ids, arms, L, ("select", "quiet", "busy"))
        e.to_csv(OUT / f"diag-competition-exposure-L{L}.csv", index=False)
        out += [f"\n## Exposure to rivals, L = {L} (base fills)\n", md(e.T.reset_index(), 3)]
    sp = pd.concat([by_split(o, ids, a, 0) for a in ALL], ignore_index=True)
    sp.to_csv(OUT / "diag-competition-splits.csv", index=False)
    out += ["\n## Markout by exposure, L = 0\n", md(sp, 2)]
    rc = pd.concat([race_curve(o, ids, ALL, 0), race_curve(o, ids, ALL[:3], -40).assign(L=-40)], ignore_index=True)
    rc.to_csv(OUT / "diag-competition-race.csv", index=False)
    out += ["\n## Race curve: match e ms later than the simulator assumes (decisions fixed)\n", md(rc, 2)]
    for L in (0, -40):
        fm = fill_models(o, ids, ALL if L == 0 else ALL[:3], L, FILLS)
        fm.to_pickle(OUT / f"diag-competition-fillmodels-L{L}.pkl")
        out += [f"\n## Fill models, L = {L}\n", md(_fmt(fm), 2)]
    bm = pd.concat([bad_markets(o, ids, a, 0) for a in ALL], ignore_index=True)
    out += ["\n## Bottom / top 5 markets (unseen windows, L = 0)\n", md(bm, 2)]
    for arm, L in (("vt_v1_m0.03_any", 0), ("vt_v1_m0.02_trigger", 0), ("vt_v1_m0.02_trigger", -40),
                   ("micf", 0), ("vt_v3p_m0.02_any", 0)):
        sr = size_rules(o, ids, arm, L, RULES)
        sr.to_pickle(OUT / f"diag-competition-size-{arm}-L{L}.pkl")
        out += [f"\n## Size rules: {arm}, L = {L}\n", md(_fmt(sr), 2)]
    (OUT / "diag-competition-tables.md").write_text("".join(x if x.endswith("\n") else x + "\n" for x in out))
    print("wrote", OUT / "diag-competition-tables.md")


if __name__ == "__main__":
    main()
