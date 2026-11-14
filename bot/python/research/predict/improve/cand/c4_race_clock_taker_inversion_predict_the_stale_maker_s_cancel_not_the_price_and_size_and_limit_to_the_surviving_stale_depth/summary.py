"""One compact table over every C4 round (r1 pre-declared, r2 / r3 after diagnosis): per arm at
L = 0 (and L = -40 for the CV pick), the 10 s markout on all 395 markets and the paired gains
vs the family's frozen arm per fold, busy sets and the comp fill variant, plus the gain vs the
round's first race-free control (ctl0).

    python3 -m research.predict.improve.cand.<c4 package>.summary r1 r2 r3"""
from __future__ import annotations

import sys

import pandas as pd

from ....report.md import md
from . import OUT

COLS = [("CV:all", "base"), ("A:eval", "base"), ("B:eval", "base"), ("CV:busyQ", "base"), ("A:ext", "base"),
        ("A:busy15", "base"), ("CV:all", "comp"), ("A:ext", "comp")]


def _g(r, k) -> str:
    return f"{r[f'g_{k}']:+,.0f} [{r[f'g_{k}_lo']:+,.0f}, {r[f'g_{k}_hi']:+,.0f}]"


def table(tags, L: int = 0) -> pd.DataFrame:
    rows = []
    for tag in tags:
        t = pd.read_csv(OUT / tag / "table.csv").rename(columns=lambda c: c.replace("g_vt_v1_m0.02_trigger", "g_veto"))
        t = t[t["L"] == L]
        for fam in ("taker", "veto"):
            k = "vt" if fam == "taker" else "veto"
            arms = t.loc[t["family"] == fam, "arm"].unique()
            if tag == tags[0]:
                arms = list(arms) + ["vt_v1_m0.03_any" if fam == "taker" else "vt_v1_m0.02_trigger"]
            for a in arms:
                s = t[(t["arm"] == a) & (t["family"].isin([fam, "frozen"]))]
                base = s[(s["set"] == "CV:all") & (s["var"] == "base")].iloc[0]
                row = {"round": tag, "family": fam, "arm": a, "fills/day": f"{base['fills_day']:,.0f}",
                       "mk c/$": f"{base['mk10_c']:+.1f}", "mk $/day": f"{base['mk10_day']:+,.0f}"}
                for st, var in COLS:
                    r = s[(s["set"] == st) & (s["var"] == var)].iloc[0]
                    row[f"gain {st} {var}"] = _g(r, k)
                if "g_ctl0" in s and pd.notna(base.get("g_ctl0")):
                    row["vs ctl0 CV:all base"] = _g(base, "ctl0")
                rows.append(row)
    return pd.DataFrame(rows)


def main() -> None:
    tags = sys.argv[1:] or ["r1", "r2", "r3", "r4"]
    parts = ["# C4 race-clock taker: all rounds, paired 10 s markout gain $/day [95% market bootstrap]\n",
             "Gain vs the family's frozen arm (taker: vt_v1_m0.03_any, veto: vt_v1_m0.02_trigger); "
             "A:eval = test3r1 + ext (chosen on select + dev3), B:eval the reverse; comp = 50 ms race window, "
             "half of each level. ctl0 = the round's first race-free control (r2: C1 ek size, r3 / r4: vlw_ek).\n"]
    for L in (0, -40):
        parts.append(f"## L = {L} ms\n\n" + md(table(tags, L)))
    text = "\n".join(parts)
    (OUT / "summary.md").write_text(text)
    print(text)


if __name__ == "__main__":
    main()
