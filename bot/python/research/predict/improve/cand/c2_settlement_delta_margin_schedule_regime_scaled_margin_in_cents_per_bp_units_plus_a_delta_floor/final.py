"""Assemble the C2 result tables from the run outputs: each cross-validated candidate next to the
frozen arm it is compared with (same markets, same L and fill variant), then every family's CV
summary. Writes data/out/predict/improve/cand-dmargin-summary.md.

    python3 -m research.predict.improve.cand.<c2>.final"""
from __future__ import annotations

import json

import pandas as pd

from .... import OUT
from ....report.md import md
from .delta import assert_unsealed

D = OUT / "improve"
ROWS = [("A:test3r1", 0, "base"), ("A:ext", 0, "base"), ("A:busy15", 0, "base"), ("A:eval", 0, "base"),
        ("B:select", 0, "base"), ("B:dev3", 0, "base"), ("B:eval", 0, "base"), ("CV:busyQ", 0, "base"),
        ("CV:all", 0, "base"), ("unseen251", 0, "base"), ("A:ext", -40, "base"), ("CV:busyQ", -40, "base"),
        ("CV:all", -40, "base"), ("A:ext", 0, "comp"), ("CV:all", 0, "comp"), ("A:ext", -40, "comp"),
        ("CV:all", -40, "comp")]


def _ci(v, lo, hi) -> str:
    return f"{v:+,.0f} [{lo:+,.0f}, {hi:+,.0f}]"


def paired_table(run: str, frozen: str, g: str) -> pd.DataFrame:
    assert_unsealed([json.loads((D / run / "meta.json").read_text())["max_start"]], run)
    cv = pd.read_csv(D / run / "extra_cv.csv")
    fz = pd.read_csv(D / run / "table.csv")
    fz = fz[fz["arm"] == frozen]
    out = []
    for s, L, v in ROWS:
        c = cv[(cv["set"] == s) & (cv["L"] == L) & (cv["var"] == v)].iloc[0]
        f = fz[(fz["set"] == s) & (fz["L"] == L) & (fz["var"] == v)].iloc[0]
        out.append({"set": s, "L": L, "fills": v, "cand fills/day": f"{c.fills_day:,.0f}",
                    "cand mk c/$": f"{c.mk10_c:+.1f}", "cand mk $/day": _ci(c.mk10_day, c.mk10_lo, c.mk10_hi),
                    "frozen fills/day": f"{f.fills_day:,.0f}", "frozen mk c/$": f"{f.mk10_c:+.1f}",
                    "frozen mk $/day": _ci(f.mk10_day, f.mk10_lo, f.mk10_hi),
                    "paired gain $/day [CI]": _ci(c[g], c[g + "_lo"], c[g + "_hi"]),
                    "gain vs micf": _ci(c.g_micf, c.g_micf_lo, c.g_micf_hi),
                    "worst5 cand / frozen": f"{c.worst5:+,.0f} / {f.worst5:+,.0f}"})
    return pd.DataFrame(out)


def main() -> None:
    parts = ["# C2 settlement-delta margin schedule: results\n"]
    parts.append("## Taker, pre-registered family dm_taker (pick dm25_f3 in both folds) vs frozen vt_v1_m0.03_any\n\n"
                 + md(paired_table("cand-dmargin-taker", "vt_v1_m0.03_any", "g_vt")))
    parts.append("## Veto, pre-registered family dm_veto (pick dmv_f3 in both folds) vs frozen vt_v1_m0.02_trigger\n\n"
                 + md(paired_table("cand-dmargin-veto", "vt_v1_m0.02_trigger", "g_veto")))
    for run, title in (("cand-dmargin-taker", "taker, pre-registered (gain vs vt_any)"),
                       ("cand-dmargin-more", "taker follow-ups (gain vs vt_any)"),
                       ("cand-dmargin-veto-more", "veto follow-ups (gain vs frozen veto)"),
                       ("cand-dmargin-veto-lower", "veto lowering sweep (gain vs frozen veto)")):
        for tag in ("cvsub_check", "cvsub"):
            p = D / run / f"{tag}.md"
            if p.exists():
                parts.append(f"## CV summary, {title} ({run}/{tag})\n\n" + p.read_text())
    text = "\n".join(parts)
    (D / "cand-dmargin-summary.md").write_text(text)
    print(text)


if __name__ == "__main__":
    main()
