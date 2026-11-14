"""Cross-validated scoring of a simulated family (cv/driver.py output).

Per L and fold: among the family's variants with 10 s markout > 0 and >= 100 fills/day on the
fold's choose windows (base fills), take the highest paired 10 s markout gain over the
family's frozen reference ("gain"; "lcb" = its 2.5% bound, reported as a robustness read).
The chosen variant is scored on the fold's evaluate windows; the CV arm stitches both folds,
so every market is scored by a variant chosen without it. Same estimators and seeds as the
harness (score/metrics.py). Writes OUT/cv/<family>-<var>.md / .csv and the per-variant grid.

    python3 -m research.predict.improve.diag.calibration.cv.score --family taker_margin [--var base]"""
from __future__ import annotations

import argparse
import json

import pandas as pd

from .....report.md import md
from ....harness import windows as W
from ....harness.guard import assert_allowed
from ....harness.score import metrics, sets
from . import OUT
from .driver import REFS
from .families import FAMILIES

SHOW = ["A:test3r1", "A:ext", "A:busyQ", "A:eval", "B:select", "B:dev3", "B:eval", "unseen251", "CV:busyQ", "CV:all"]


def _sel(a, L, ids):
    s = set(ids)
    return a[(a["L"] == L) & a["m"].isin(s)]


def choose(agg, variants, ref, L, ids, crit) -> tuple[str, pd.DataFrame]:
    refs = {r: _sel(agg[agg["arm"] == r], L, ids) for r in REFS}
    rows = []
    for v in variants:
        r = metrics.row(_sel(agg[agg["arm"] == v], L, ids), refs, ids)
        tag = "vt" if ref == "vt_v1_m0.03_any" else ref
        rows.append({"arm": v, "fills_day": r["fills_day"], "mk10_c": r["mk10_c"], "mk10_day": r["mk10_day"],
                     "gain": r[f"g_{tag}"], "lcb": r[f"g_{tag}_lo"], "hi": r[f"g_{tag}_hi"]})
    t = pd.DataFrame(rows)
    ok = (t["mk10_c"] > 0) & (t["fills_day"] >= 100)
    pool = t[ok] if ok.any() else t
    return str(pool.sort_values([crit, "arm"], ascending=[False, True]).iloc[0]["arm"]), t


def score(family: str, var: str = "base", crit: str = "gain"):
    agg = pd.read_pickle(OUT / f"agg-{family}-{var}.pkl")
    act = pd.read_pickle(OUT / "activity.pkl")
    assert_allowed(act["start"], "cv markets")
    ref = FAMILIES[family]()[0]
    variants = [v for v in agg["arm"].unique() if v not in REFS]
    S = sets.build(act)
    picks, grid, out = {}, [], []
    for L in (0, -40):
        cv = []
        for f, (ch, ev) in W.FOLDS.items():
            cids = sorted(i for w in ch for i in W.ids(w))
            eids = sorted(i for w in ev for i in W.ids(w))
            pick, t = choose(agg, variants, ref, L, cids, crit)
            picks[f"{f}@{L}"] = pick
            grid.append(t.assign(fold=f, L=L))
            cv.append(_sel(agg[agg["arm"] == pick], L, eids).assign(arm="cv"))
        arms = {"cv": pd.concat(cv, ignore_index=True)}
        arms.update({r: agg[(agg["arm"] == r) & (agg["L"] == L)] for r in REFS})
        refs = {r: arms[r] for r in REFS}
        for s in SHOW:
            if s in S:
                for name, a in arms.items():
                    out.append({"set": s, "L": L, "arm": name, **metrics.row(_sel(a, L, S[s]), refs, S[s])})
    return pd.DataFrame(out), pd.concat(grid, ignore_index=True), picks


def by_window(agg: pd.DataFrame, ref: str) -> pd.DataFrame:
    """Every variant's paired gain over the frozen reference per window (no choice made)."""
    tag = "vt" if ref == "vt_v1_m0.03_any" else ref
    out = []
    for L in (0, -40):
        for w in W.WINDOWS:
            ids = W.ids(w)
            refs = {r: _sel(agg[agg["arm"] == r], L, ids) for r in REFS}
            for v in agg["arm"].unique():
                if v not in REFS:
                    r = metrics.row(_sel(agg[agg["arm"] == v], L, ids), refs, ids)
                    out.append({"L": L, "win": w, "arm": v,
                                "gain": _ci(r[f"g_{tag}"], r[f"g_{tag}_lo"], r[f"g_{tag}_hi"])})
    t = pd.DataFrame(out).pivot_table(index=["L", "arm"], columns="win", values="gain", aggfunc="first")
    return t[list(W.WINDOWS)].reset_index()


def _ci(v, lo, hi) -> str:
    return f"{v:+,.0f} [{lo:+,.0f}, {hi:+,.0f}]"


def render(t: pd.DataFrame, ref: str) -> str:
    tag = "vt" if ref == "vt_v1_m0.03_any" else ref
    rows = [{"set": r["set"], "L": r["L"], "arm": r["arm"], "fills/day": f"{r['fills_day']:,.0f}",
             "mk c/$": f"{r['mk10_c']:+.1f}", "mk $/day": f"{r['mk10_day']:+,.0f}",
             "gain vs frozen": _ci(r[f"g_{tag}"], r[f"g_{tag}_lo"], r[f"g_{tag}_hi"]),
             "P<=0": f"{r[f'g_{tag}_p0']:.2f}", "gain vs micf": _ci(r["g_micf"], r["g_micf_lo"], r["g_micf_hi"]),
             "worst5": f"{r['worst5']:+,.0f}"} for _, r in t.iterrows()]
    return md(pd.DataFrame(rows))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--family", required=True, choices=sorted(FAMILIES))
    ap.add_argument("--var", default="base")
    ap.add_argument("--crit", default="gain", choices=("gain", "lcb"))
    a = ap.parse_args()
    ref = FAMILIES[a.family]()[0]
    t, g, picks = score(a.family, a.var, a.crit)
    tag = f"{a.family}-{a.var}-{a.crit}"
    t.to_csv(OUT / f"{tag}.csv", index=False)
    g.to_csv(OUT / f"{tag}-grid.csv", index=False)
    keep = t[t["arm"].isin(["cv", ref, "micf"])]
    txt = [f"# CV of `{a.family}` ({a.var} fills, criterion {a.crit})\n", f"Picks: {json.dumps(picks)}\n"]
    for L in (0, -40):
        txt.append(f"\n## L = {L}\n\n" + render(keep[keep["L"] == L], ref))
    txt.append("\n## Choice grid (choose windows of each fold)\n\n" + md(g.round(1)))
    txt.append("\n## Every variant, gain over the frozen arm per window (no choice)\n\n" + md(by_window(
        pd.read_pickle(OUT / f"agg-{a.family}-{a.var}.pkl"), ref)))
    (OUT / f"{tag}.md").write_text("\n".join(txt))
    print("\n".join(txt[:4]))


if __name__ == "__main__":
    main()
