"""Read a run.py output (aggs.pkl + meta.json): the cross-validated candidate against all three
frozen arms (gain vs vt_any, vs the frozen veto, vs micf), the per-window sweep of every
variant (diagnostic: each variant on every window, NOT cross-validated), and the C2 kill
criteria.

    python3 -m research.predict.improve.cand.<c2>.extra --out <dir> --family taker|veto"""
from __future__ import annotations

import argparse
import json
import pickle
import re
from pathlib import Path

import pandas as pd

from ...harness import windows as W
from ...harness.score import metrics, sets
from ....report.md import md
from .delta import assert_unsealed

REFS = {"vt_v1_m0.03_any": "F|vt_v1_m0.03_any", "veto": "F|vt_v1_m0.02_trigger", "micf": "F|micf"}
CV_SETS = ["A:test3r1", "A:ext", "A:eval", "A:busy15", "A:busyQ", "B:select", "B:dev3", "B:eval",
           "B:busyQ", "CV:all", "CV:busyQ", "unseen251"]
SWEEP_SETS = ["select", "dev3", "test3r1", "ext", "busy15", "busyQ", "all"]


def load(out: Path) -> dict:
    with open(out / "aggs.pkl", "rb") as fh:
        d = pickle.load(fh)
    assert_unsealed(d["activity"]["start"], "aggs activity")
    assert_unsealed(W._markets().start[d["agg"]["m"].unique()], "aggs markets")
    return d


def all_sets(act: pd.DataFrame) -> dict[str, list[int]]:
    S = sets.build(act)
    for w in ("select", "dev3", "test3r1", "ext"):
        S[w] = W.ids(w)
    S["busy15"] = sorted(S.get("A:busy15", []) + S.get("B:busy15", []))
    S["busyQ"], S["all"] = S["CV:busyQ"], S["CV:all"]
    return S


def _rows(arms: dict[str, pd.DataFrame], agg: pd.DataFrame, S: dict, names, Ls, vars_) -> pd.DataFrame:
    rows = []
    for s in names:
        ids = set(S[s])
        for L in Ls:
            for v in vars_:
                f = lambda x: x[(x["L"] == L) & (x["var"] == v) & x["m"].isin(ids)]  # noqa: E731
                refs = {n: f(agg[agg["key"] == k]) for n, k in REFS.items()}
                for name, a in arms.items():
                    rows.append({"set": s, "arm": name, "L": L, "var": v, **metrics.row(f(a), refs, S[s])})
    return pd.DataFrame(rows)


def cv_frame(agg: pd.DataFrame, folds: dict) -> pd.DataFrame:
    parts = []
    for f, d in folds.items():
        ev = {i for w in W.FOLDS[f][1] for i in W.ids(w)}
        parts.append(agg[(agg["key"] == d["key"]) & agg["m"].isin(ev)])
    return pd.concat(parts, ignore_index=True)


def _ci(v, lo, hi) -> str:
    return f"{v:+,.0f} [{lo:+,.0f}, {hi:+,.0f}]"


def fmt(t: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame({"set": t["set"], "arm": t["arm"], "L": t["L"], "var": t["var"],
                         "fills/day": t["fills_day"].map("{:,.0f}".format),
                         "mk c/$": t["mk10_c"].map("{:+.1f}".format),
                         "mk $/day [CI]": [_ci(*r) for r in zip(t.mk10_day, t.mk10_lo, t.mk10_hi)],
                         "gain vs vt_any": [_ci(*r) for r in zip(t.g_vt, t.g_vt_lo, t.g_vt_hi)],
                         "gain vs veto": [_ci(*r) for r in zip(t.g_veto, t.g_veto_lo, t.g_veto_hi)],
                         "gain vs micf": [_ci(*r) for r in zip(t.g_micf, t.g_micf_lo, t.g_micf_hi)],
                         "worst5 $": t["worst5"].map("{:+,.0f}".format)})


def _g(t, s, L, v, col):
    r = t[(t["set"] == s) & (t["L"] == L) & (t["var"] == v) & (t["arm"] == "candidate")]
    return float(r[col].iloc[0]) if len(r) else float("nan")


def verdict(cv: pd.DataFrame, family: str, picks: dict) -> list[str]:
    g = "g_vt" if family == "taker" else "g_veto"
    out = [f"picks: A = {picks['A']}, B = {picks['B']}"]
    if family == "taker":
        k1 = _g(cv, "CV:all", 0, "base", g) <= 0 or _g(cv, "CV:all", 0, "base", g + "_lo") < -100
        k2 = min(_g(cv, "A:ext", 0, "base", g), _g(cv, "CV:busyQ", 0, "base", g)) < -150
        thr = [float(x) for x in re.findall(r"(?:dm|_)(\d+(?:\.\d+)?)(?=@|_|$)", picks["A"])]
        k3 = bool(thr) and min(thr) < 25 and _g(cv, "A:ext", 0, "base", g) < 0
        k4 = _g(cv, "CV:all", 0, "comp", g) < 0
        out += [f"K1 CV:all L0 gain <= 0 or LCB < -100: {k1}", f"K2 A:ext or CV:busyQ L0 < -150: {k2}",
                f"K3 fold A thr < 25 and loses on A:ext: {k3}", f"K4 CV:all comp L0 gain < 0: {k4}",
                f"PASS (CV:all L0 LCB > 0 and A:ext >= 0): "
                f"{_g(cv, 'CV:all', 0, 'base', g + '_lo') > 0 and _g(cv, 'A:ext', 0, 'base', g) >= 0}"]
    else:
        kv = _g(cv, "CV:all", 0, "base", g) <= 0 and _g(cv, "CV:all", -40, "base", g) <= 0
        out.append(f"KILL veto floor (CV:all gain vs veto <= 0 at L0 and L-40): {kv}")
    both = _g(cv, "A:eval", 0, "base", g) > 0 and _g(cv, "B:eval", 0, "base", g) > 0
    busy = min(_g(cv, "A:ext", 0, "base", g), _g(cv, "CV:busyQ", 0, "base", g)) >= 0
    out.append(f"improves rule (both folds L0 gain > 0 and A:ext, CV:busyQ >= 0): {both and busy}")
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--family", choices=("taker", "veto"), required=True)
    a = ap.parse_args()
    out = Path(a.out)
    d = load(out)
    agg, S = d["agg"], all_sets(d["activity"])
    meta = json.loads((out / "meta.json").read_text())
    picks = {f: v["chosen"] for f, v in meta["folds"].items()}
    cv = _rows({"candidate": cv_frame(agg, d["folds"])}, agg, S, CV_SETS, (0, -40), ("base", "comp"))
    keys = sorted(k for k in agg["key"].unique() if not k.startswith("F|"))
    arms = {k.split("|", 1)[1]: agg[agg["key"] == k] for k in keys}
    arms.update({n: agg[agg["key"] == k] for n, k in REFS.items()})
    sw = _rows(arms, agg, S, SWEEP_SETS, (0, -40), ("base", "comp"))
    cv.to_csv(out / "extra_cv.csv", index=False)
    sw.to_csv(out / "extra_sweep.csv", index=False)
    v = verdict(cv, a.family, picks)
    txt = [f"# C2 extra tables: {out.name}\n", "\n".join(f"- {x}" for x in v) + "\n"]
    for L in (0, -40):
        for var in ("base", "comp"):
            txt.append(f"## CV candidate, L = {L}, {var}\n\n" + md(fmt(cv[(cv.L == L) & (cv["var"] == var)])))
    txt.append("## Sweep (diagnostic, every variant on every window, not cross-validated), L = 0 base\n\n"
               + md(fmt(sw[(sw.L == 0) & (sw["var"] == "base")].sort_values(["set", "arm"]))))
    (out / "extra.md").write_text("\n".join(txt))
    print("\n".join(v))


if __name__ == "__main__":
    main()
