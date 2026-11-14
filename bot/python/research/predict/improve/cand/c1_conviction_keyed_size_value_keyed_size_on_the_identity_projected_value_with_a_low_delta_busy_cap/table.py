"""Markdown for C1 results: rows of score.py tables, gains vs the frozen arm the variant
replaces (vt_any for a taker, the veto for a veto-type arm) and vs micf, with CIs."""
from __future__ import annotations

import pandas as pd

KEY_SETS = ("A:eval", "B:eval", "CV:all", "CV:busyQ", "A:ext", "A:busy15", "unseen251")


def _ci(v, lo, hi) -> str:
    return f"{v:+,.0f} [{lo:+,.0f}, {hi:+,.0f}]"


def rows(t: pd.DataFrame, vs: str, sets=KEY_SETS, label=None) -> list[dict]:
    """vs: "vt" or "veto" (the frozen arm the candidate replaces)."""
    out = []
    t = t[t["set"].isin(sets)].copy()
    t["o"] = t["set"].map({s: k for k, s in enumerate(sets)})
    for r in t.sort_values(["o", "L", "var", "arm"], ascending=[True, False, True, True]).itertuples():
        g = getattr(r, f"g_{vs}"), getattr(r, f"g_{vs}_lo"), getattr(r, f"g_{vs}_hi")
        out.append({"set": r.set, "arm": label or r.arm, "L": r.L, "fill": r.var,
                    "fills/day": f"{r.fills_day:,.0f}", "mk c/$": f"{r.mk10_c:+.1f}",
                    "mk $/day [CI]": _ci(r.mk10_day, r.mk10_lo, r.mk10_hi),
                    f"gain vs {'vt_any' if vs == 'vt' else 'veto'} [CI]": "" if r.arm in (
                        "vt_v1_m0.03_any" if vs == "vt" else "vt_v1_m0.02_trigger",) else _ci(*g),
                    "gain vs micf [CI]": "" if r.arm == "micf" else _ci(r.g_micf, r.g_micf_lo, r.g_micf_hi),
                    "worst-5 $": f"{r.worst5:+,.0f}"})
    return out


def md(rs: list[dict]) -> str:
    if not rs:
        return ""
    cols = list(rs[0])
    lines = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    lines += ["| " + " | ".join(str(r.get(c, "")) for c in cols) + " |" for r in rs]
    return "\n".join(lines)


def compare(cand: pd.DataFrame, frozen: pd.DataFrame, frozen_arm: str, vs: str, sets=KEY_SETS,
            Ls=(0, -40), vars_=("base", "comp")) -> str:
    """Candidate rows interleaved with the frozen arm it replaces, per set x L x fill model."""
    c = cand[cand["L"].isin(Ls) & cand["var"].isin(vars_)]
    f = frozen[(frozen["arm"] == frozen_arm) & frozen["L"].isin(Ls) & frozen["var"].isin(vars_)]
    both = pd.concat([f, c], ignore_index=True)
    both["o"] = both["set"].map({s: k for k, s in enumerate(sets)})
    both = both[both["set"].isin(sets)].sort_values(["var", "L", "o"], ascending=[True, False, True], kind="stable")
    return md(rows(both, vs, sets))
