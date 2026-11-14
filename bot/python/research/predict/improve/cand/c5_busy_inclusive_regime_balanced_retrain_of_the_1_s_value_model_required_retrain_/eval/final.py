"""Compact table of every C5 view written so far: paired 10 s markout gain vs the frozen
vt_v1_m0.03_any [95% market bootstrap CI], $/day, at L = 0, per fold evaluation, busy sets and
CV:all (base fills), plus CV:all and A:ext under the 50 ms competition variant; the frozen arm's
own row first. Reads <root>/**/table.csv (the harness format).

    python3 -m <this package>.eval.final [--root data/out/predict/improve/c5_busy_refit]"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from .....report.md import md
from . import OUT_DIR

COLS = [("A:eval", "base"), ("B:eval", "base"), ("CV:all", "base"), ("A:ext", "base"), ("A:busy15", "base"),
        ("CV:busyQ", "base"), ("CV:all", "comp"), ("A:ext", "comp")]


def _g(t, s, var, arm="candidate"):
    r = t[(t["set"] == s) & (t["var"] == var) & (t["arm"] == arm) & (t["L"] == 0)]
    if not len(r):
        return ""
    r = r.iloc[0]
    if arm != "candidate":
        return f"{r.mk10_day:+,.0f} ({r.mk10_c:+.1f} c/$)"
    return f"{r.g_vt:+,.0f} [{r.g_vt_lo:+,.0f}, {r.g_vt_hi:+,.0f}]"


def build(root: Path) -> pd.DataFrame:
    rows, ref = [], None
    for p in sorted(root.rglob("table.csv")):
        t = pd.read_csv(p)
        meta = json.loads((p.parent / "meta.json").read_text())
        picks = ", ".join(f"{f}={d['chosen']}" for f, d in meta["folds"].items())
        cv = t[(t["set"] == "CV:all") & (t["var"] == "base") & (t["arm"] == "candidate") & (t["L"] == 0)].iloc[0]
        rows.append({"view": str(p.parent.relative_to(root)), "picked": picks,
                     "CV fills/day": f"{cv.fills_day:,.0f}", "CV c/$": f"{cv.mk10_c:+.1f}",
                     **{f"{s} {v}": _g(t, s, v) for s, v in COLS}})
        if ref is None:
            fz = t[(t["set"] == "CV:all") & (t["var"] == "base") & (t["arm"] == "vt_v1_m0.03_any") & (t["L"] == 0)]
            ref = {"view": "frozen vt_v1_m0.03_any ($/day, c/$)", "picked": "",
                   "CV fills/day": f"{fz['fills_day'].iloc[0]:,.0f}",
                   "CV c/$": "", **{f"{s} {v}": _g(t, s, v, "vt_v1_m0.03_any") for s, v in COLS}}
    return pd.DataFrame([ref] + rows)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=str(OUT_DIR))
    a = ap.parse_args()
    root = Path(a.root)
    d = build(root)
    txt = ("# C5 views: paired 10 s markout gain vs frozen vt_v1_m0.03_any, $/day [95% CI], L = 0\n\n"
           "Columns: set and simulator variant (base = 10 ms race, full level; comp = 50 ms, half level).\n\n"
           + md(d))
    (root / "final.md").write_text(txt)
    print(txt)


if __name__ == "__main__":
    main()
