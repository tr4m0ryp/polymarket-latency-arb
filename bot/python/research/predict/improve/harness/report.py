"""Write a harness result: table.csv (every set x arm x L x variant), hours.csv, selection
per fold, meta.json and table.md (base fills per L, then the 50 ms competition variant)."""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from ...report.md import md

SHOW = ["A:test3r1", "A:ext", "A:eval", "A:busy15", "A:busyQ", "B:select", "B:dev3", "B:eval",
        "B:busyQ", "CV:all", "CV:busyQ", "unseen251"]


def _ci(v, lo, hi, d=0) -> str:
    return f"{v:+,.{d}f} [{lo:+,.{d}f}, {hi:+,.{d}f}]"


def _md(t: pd.DataFrame) -> str:
    rows = []
    for r in t.itertuples():
        rows.append({"set": r.set, "mkts": r.mkts, "arm": r.arm, "fills/day": f"{r.fills_day:,.0f}",
                     "10 s mk c/$": f"{r.mk10_c:+.1f}", "10 s mk $/day [CI]": _ci(r.mk10_day, r.mk10_lo, r.mk10_hi),
                     "gain vs vt_any [CI]": _ci(r.g_vt, r.g_vt_lo, r.g_vt_hi),
                     "gain vs micf [CI]": _ci(r.g_micf, r.g_micf_lo, r.g_micf_hi),
                     "worst-5 mkts $": f"{r.worst5:+,.0f}"})
    return md(pd.DataFrame(rows))


def write(res: dict, out: Path, spec: str) -> str:
    out.mkdir(parents=True, exist_ok=True)
    tab, hrs = res["table"], res["hours"]
    tab.to_csv(out / "table.csv", index=False)
    hrs.to_csv(out / "hours.csv", index=False)
    sel = {f: {k: v for k, v in d.items() if k != "selection"} for f, d in res["folds"].items()}
    for f, d in res["folds"].items():
        if d["selection"] is not None:
            d["selection"].to_csv(out / f"selection_{f}.csv", index=False)
    meta = {k: v for k, v in res.items() if k not in ("table", "hours", "folds")}
    (out / "meta.json").write_text(json.dumps({"arm": spec, "folds": sel, **meta}, indent=1, default=str))
    order = {s: k for k, s in enumerate(SHOW)}
    t = tab[tab["set"].isin(order)].copy()
    t["o"] = t["set"].map(order)
    parts = [f"# Harness: `{spec}`\n",
             "Chosen variant per fold: " + ", ".join(f"{f} = `{d['chosen']}`" for f, d in sel.items())
             + f". Markets: {res['n_markets']} allowed (max start {res['max_start']:.0f} < sealed 1791744900). "
             f"Runtime {res['secs_total']:.0f} s (simulation {res['secs_sim']:.0f} s).\n"]
    for var, title in (("base", "10 ms race window, full level"), ("comp", "competition sensitivity: 50 ms window, half of each level")):
        for L in sorted(t["L"].unique(), reverse=True):
            s = t[(t["L"] == L) & (t["var"] == var)].sort_values(["o", "arm"])
            if len(s):
                parts.append(f"## L = {L} ms, {title}\n\n" + _md(s))
    text = "\n".join(parts)
    (out / "table.md").write_text(text)
    return text
