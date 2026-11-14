"""Offline two-fold CV of a sub-family of fold-invariant variants already simulated by run.py
(aggs.pkl), with the harness's own choice rule (score/select.choose on the fold's choose
windows, L = 0 base, criterion lcb) and the same metrics. Lets one simulation pass serve
several pre-declared families. Checked against the harness: the full dm_taker family
reproduces its picks and CV rows exactly.

    python3 -m research.predict.improve.cand.<c2>.cvsub --out <dir> \
        --fam "sweep=dm25_f3,dm20_f3,dm30_f3" --fam "floor=dmnone_f3,dmnone_f5" """
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from ...harness import windows as W
from ...harness.score import metrics, select
from ....report.md import md
from .extra import REFS, _rows, all_sets, load

KEY_SETS = ["A:eval", "B:eval", "A:test3r1", "A:ext", "A:busy15", "CV:busyQ", "CV:all"]


def picks(agg: pd.DataFrame, names, crit: str = "lcb", scope: str = "*") -> dict:
    pair = {"vt_v1_m0.03_any": agg[agg["key"] == REFS["vt_v1_m0.03_any"]], "micf": agg[agg["key"] == REFS["micf"]]}
    out = {}
    for f, (choose, _) in W.FOLDS.items():
        ids = sorted(i for w in choose for i in W.ids(w))
        arms = {n: agg[(agg["key"] == f"{scope}|{n}") & agg["m"].isin(ids)] for n in names}
        tab = metrics.table(arms, pair, {f"{f}:choose": ids}, Ls=(0,), variants=("base",))
        out[f] = select.choose(tab, crit)[0] if len(names) > 1 else names[0]
    return out


def cv(agg: pd.DataFrame, S: dict, names, scope: str = "*", sets=KEY_SETS, Ls=(0, -40),
       vars_=("base", "comp")) -> tuple[dict, pd.DataFrame]:
    p = picks(agg, names, scope=scope)
    parts = []
    for f, (_, ev) in W.FOLDS.items():
        ids = {i for w in ev for i in W.ids(w)}
        parts.append(agg[(agg["key"] == f"{scope}|{p[f]}") & agg["m"].isin(ids)])
    return p, _rows({"candidate": pd.concat(parts, ignore_index=True)}, agg, S, sets, Ls, vars_)


def _c(r, g) -> str:
    return f"{r[g]:+,.0f} [{r[g + '_lo']:+,.0f}, {r[g + '_hi']:+,.0f}]"


def summary(fam: str, p: dict, t: pd.DataFrame, g: str = "g_vt") -> dict:
    row = {"family": fam, "pick A": p["A"], "pick B": p["B"]}
    for s in KEY_SETS:
        r = t[(t["set"] == s) & (t["L"] == 0) & (t["var"] == "base")].iloc[0]
        row[f"{s} L0"] = _c(r, g)
    for L, v in ((-40, "base"), (0, "comp"), (-40, "comp")):
        r = t[(t["set"] == "CV:all") & (t["L"] == L) & (t["var"] == v)].iloc[0]
        row[f"CV:all L{L} {v}"] = _c(r, g)
    return row


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--fam", action="append", required=True, help="name=v1,v2,...")
    ap.add_argument("--gain", default="g_vt", help="g_vt (vs vt_any) or g_veto (vs the frozen veto)")
    ap.add_argument("--tag", default="cvsub")
    a = ap.parse_args()
    out = Path(a.out)
    d = load(out)
    S = all_sets(d["activity"])
    rows, full = [], []
    for spec in a.fam:
        name, _, vs = spec.partition("=")
        p, t = cv(d["agg"], S, vs.split(","))
        rows.append(summary(name, p, t, a.gain))
        full.append(t.assign(family=name, pick_A=p["A"], pick_B=p["B"]))
        print(name, p, flush=True)
    s = pd.DataFrame(rows)
    pd.concat(full).to_csv(out / f"{a.tag}.csv", index=False)
    (out / f"{a.tag}.md").write_text(md(s))
    print(md(s))


if __name__ == "__main__":
    main()
