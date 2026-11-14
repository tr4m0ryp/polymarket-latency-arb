"""One comparison table of every C5 view against the frozen 1 s taker, the veto and micf on the
same markets (L = 0; base fills, then the 50 ms competition variant), from each view's
harness table.csv."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from .....report.md import md

SETS = ["A:test3r1", "A:ext", "A:eval", "A:busy15", "B:select", "B:dev3", "B:eval", "CV:all", "CV:busyQ"]
NICK = {"vt_v1_m0.03_any": "frozen vt_any", "vt_v1_m0.02_trigger": "frozen veto", "micf": "micf"}


def _ci(v, lo, hi) -> str:
    return f"{v:+,.0f} [{lo:+,.0f}, {hi:+,.0f}]"


def rows(out: Path, views: list[str], var: str = "base") -> pd.DataFrame:
    recs = []
    for k, v in enumerate(views):
        t = pd.read_csv(out / v / "table.csv")
        t = t[(t["L"] == 0) & (t["var"] == var) & t["set"].isin(SETS)]
        for r in t.itertuples():
            if r.arm != "candidate" and k > 0:
                continue                      # frozen rows once (identical in every view)
            recs.append({"o": SETS.index(r.set), "v": 0 if r.arm != "candidate" else k + 1, "set": r.set,
                         "arm": NICK.get(r.arm, f"C5 {v}"), "fills/day": f"{r.fills_day:,.0f}",
                         "mk c/$": f"{r.mk10_c:+.1f}", "mk $/day [CI]": _ci(r.mk10_day, r.mk10_lo, r.mk10_hi),
                         "gain vs vt_any [CI]": "" if r.arm == "vt_v1_m0.03_any" else _ci(r.g_vt, r.g_vt_lo, r.g_vt_hi),
                         "gain vs micf [CI]": "" if r.arm == "micf" else _ci(r.g_micf, r.g_micf_lo, r.g_micf_hi),
                         "worst-5 $": f"{r.worst5:+,.0f}"})
    d = pd.DataFrame(recs).sort_values(["o", "v", "arm"])
    return d.drop(columns=["o", "v"])


def write(out: Path, views: list[str]) -> str:
    parts = ["# C5 busy-inclusive retrain: every view vs the frozen arms (L = 0)\n"]
    for var, title in (("base", "base fills (10 ms race window)"), ("comp", "50 ms competition, half level")):
        try:
            parts.append(f"## {title}\n\n" + md(rows(out, views, var)))
        except (KeyError, ValueError):
            continue
    picks = []
    for v in views:
        import json
        m = json.loads((out / v / "meta.json").read_text())
        picks.append(f"- {v}: " + ", ".join(f"{f} = {d['chosen']}" for f, d in m["folds"].items()))
    text = "\n".join(parts + ["## Variant picked per fold\n", *picks])
    (out / "summary.md").write_text(text)
    return text
