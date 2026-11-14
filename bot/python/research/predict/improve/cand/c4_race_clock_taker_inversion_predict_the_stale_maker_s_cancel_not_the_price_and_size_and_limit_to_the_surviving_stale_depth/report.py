"""Markdown of a C4 drive result: per family the CV candidate, every variant and the frozen
references on the key sets, base and comp fills, L = 0 and -40; then the fold choices."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from ....report.md import md

SETS = ("A:eval", "B:eval", "CV:all", "CV:busyQ", "A:ext", "A:busy15", "unseen251")
REFCOL = {"taker": "vt", "veto": "vt_v1_m0.02_trigger"}


def _ci(v, lo, hi) -> str:
    return f"{v:+,.0f} [{lo:+,.0f}, {hi:+,.0f}]"


def rows(t: pd.DataFrame, fam: str, sets=SETS) -> pd.DataFrame:
    rc = REFCOL[fam]
    t = t[t["set"].isin(sets)].copy()
    t["o"] = t["set"].map({s: k for k, s in enumerate(sets)})
    out = []
    t = t.rename(columns=lambda c: c.replace("g_vt_v1_m0.02_trigger", "g_veto"))
    rc = "veto" if rc != "vt" else rc
    for r in t.sort_values(["var", "L", "o", "arm"], ascending=[True, False, True, True]).itertuples():
        g = getattr(r, f"g_{rc}"), getattr(r, f"g_{rc}_lo"), getattr(r, f"g_{rc}_hi")
        out.append({"var": r.var, "L": r.L, "set": r.set, "arm": r.arm, "fills/day": f"{r.fills_day:,.0f}",
                    "mk c/$": f"{r.mk10_c:+.1f}", "mk $/day [CI]": _ci(r.mk10_day, r.mk10_lo, r.mk10_hi),
                    f"gain vs {'vt_any' if fam == 'taker' else 'veto'} [CI]": _ci(*g),
                    "gain vs micf [CI]": _ci(r.g_micf, r.g_micf_lo, r.g_micf_hi), "worst-5 $": f"{r.worst5:+,.0f}",
                    **({"gain vs ctl0 [CI]": _ci(r.g_ctl0, r.g_ctl0_lo, r.g_ctl0_hi)}
                       if hasattr(r, "g_ctl0") and r.g_ctl0 == r.g_ctl0 else {})})
    return pd.DataFrame(out)


def write(tab: pd.DataFrame, folds: dict, d: Path) -> str:
    parts = ["# C4 race-clock taker: " + d.name + "\n"]
    for f, v in folds.items():
        parts.append(f"- fold {f}: chose `{v['chosen']}` (choose-window LCB {v['lcb']:+,.0f}, gain {v['gain']:+,.0f}, floor met {v['met_floor']})")
    for fam in ("taker", "veto"):
        t = tab[tab["family"].isin([fam])]
        if not len(t):
            continue
        ref = "vt_v1_m0.03_any" if fam == "taker" else "vt_v1_m0.02_trigger"
        fr = tab[(tab["family"] == "frozen") & tab["arm"].isin([ref, "micf"])]
        parts.append(f"\n## {fam}\n\n" + md(rows(pd.concat([t, fr]), fam)))
    text = "\n".join(parts)
    (d / "table.md").write_text(text)
    return text


if __name__ == "__main__":
    import json
    import sys
    from . import OUT
    d = OUT / sys.argv[1]
    print(write(pd.read_csv(d / "table.csv"), json.loads((d / "meta.json").read_text())["folds"], d))
