"""C1 summary tables from the run.py dumps (taker, veto, sweep) -> data/out/predict/improve/c1-size/.

    python3 -m research.predict.improve.cand.<c1 pkg>.summary

1. Pre-declared families, harness fold choice (lcb of the gain vs vt_any, = harness CV),
   next to the frozen arm they replace, key sets x L x fill model.
2. Every variant fixed (no fold choice: a diagnostic), one line each.
3. Fold-chosen sweeps (the slope K, the cap, the key) with the gain vs the replaced arm."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from .... import OUT
from . import score as S
from .table import compare, md

D = OUT / "improve" / "c1-size"
FAM = {"taker": ("vt", S.VT, "ek_"), "veto": ("veto", S.VETO, "vk_")}
ONE = [("A:eval", 0, "base"), ("B:eval", 0, "base"), ("CV:all", 0, "base"), ("CV:all", 0, "comp"),
       ("CV:busyQ", 0, "base"), ("A:ext", 0, "base"), ("A:busy15", 0, "base"),
       ("CV:all", -40, "base"), ("CV:all", -40, "comp"), ("A:ext", -40, "comp")]


def shfill(pm: pd.DataFrame) -> pd.Series:
    g = pm[(pm["L"] == 0) & (pm["var"] == "base")].groupby("arm")[["shares", "n"]].sum()
    return (g["shares"] / g["n"]).rename(lambda k: k.split("|", 1)[-1])


def one_line(t: pd.DataFrame, vs: str, sh: pd.Series) -> str:
    rows = []
    for arm, g in t.groupby("arm", sort=False):
        r = {"variant": arm, "sh/fill": f"{sh.get(arm, float('nan')):.0f}"}
        for s, L, v in ONE:
            x = g[(g["set"] == s) & (g["L"] == L) & (g["var"] == v)]
            if len(x):
                x = x.iloc[0]
                txt = f"{x[f'g_{vs}']:+,.0f}"
                if s == "CV:all":
                    txt += f" [{x[f'g_{vs}_lo']:+,.0f}, {x[f'g_{vs}_hi']:+,.0f}]"
                r[f"{s} L{L} {v}"] = txt
        a = g[(g["set"] == "CV:all") & (g["L"] == 0) & (g["var"] == "base")].iloc[0]
        r["CV:all L0 c/$"], r["worst-5"] = f"{a['mk10_c']:+.1f}", f"{a['worst5']:+,.0f}"
        rows.append(r)
    return md(rows)


def main() -> None:
    parts = ["# C1 conviction-keyed size: results\n",
             "Gains are paired 10 s markout $/day vs the frozen arm the variant replaces (vt_any for "
             "takers, the frozen veto for veto-type arms), 95% market bootstrap. Harness estimators, "
             "allowed markets only (max start 1791744600 < 1791744900).\n"]
    dumps = {k: S.load(D / k) for k in ("taker", "veto", "sweep", "round3", "round4") if (D / k / "per_market.pkl").exists()}
    act = next(iter(dumps.values()))[1]
    pm = pd.concat([p for p, _ in dumps.values()], ignore_index=True).drop_duplicates(["arm", "L", "var", "m"])
    fz = S.frozen_rows(pm, act)
    sh = shfill(pm)
    for fam, (vs, fz_arm, pre) in FAM.items():
        decl = S.names(dumps[fam][0])
        t, picks = S.cv(pm, act, decl, col="g_vt_lo")
        parts.append(f"## {fam}: pre-declared family, harness choice {picks}\n")
        parts.append(compare(t, fz, fz_arm, vs) + "\n")
        allv = [n for n in S.names(pm) if n.startswith(pre)]
        parts.append(f"## {fam}: every variant fixed (diagnostic, no fold choice)\n")
        parts.append(one_line(S.variants(pm, act, allv, only={s for s, _, _ in ONE}), vs, sh) + "\n")
        sweeps = _sweeps(allv, pre)
        rows = []
        for name, which in sweeps.items():
            if all(w in allv for w in which):
                ct, p = S.cv(pm, act, which, col="g_vt_lo")
                ct["arm"] = f"{name}: A={p['A']}, B={p['B']}"
                rows.append(ct)
        if rows:
            parts.append(f"## {fam}: fold-chosen sweeps (choice by lcb of gain vs vt_any on the choose windows)\n")
            parts.append(one_line(pd.concat(rows, ignore_index=True), vs, sh) + "\n")
    (D / "summary.md").write_text("\n".join(parts))
    print("\n".join(parts))


def _sweeps(allv: list[str], pre: str) -> dict[str, list[str]]:
    k = "vstar"
    if pre == "ek_":
        return {"K (v*)": [f"ek_vstar_{K}" for K in (1000, 1500, 2000, 3000, 4000)],
                "K (pred)": [f"ek_pred_{K}" for K in (1500, 2000, 3000)],
                "cap (v* 2000)": ["ek_vstar_2000"] + [f"ek_vstar_2000_d{c}" for c in (6, 8, 10, 12)],
                "flat size": [f"ek_flat_{s}" for s in (75, 100, 150)],
                "K x cap (final)": [f"ek_vstar_{K}{c}" for K in (2000, 3000, 4000) for c in ("", "_d6", "_d8")],
                "key x K": [v for v in allv if v.startswith(("ek_pred", "ek_vstar", "ek_vmin"))
                            and "_d" not in v and "_h" not in v],
                "all": allv}
    return {"K (v*)": [f"vk_{k}_{K}" for K in (2000, 3000, 4000)],
            "K (pred)": [f"vk_pred_{K}" for K in (2000, 3000, 4000)],
            "cap (v* 3000)": ["vk_vstar_3000"] + [f"vk_vstar_3000_d{c}" for c in (6, 8, 10)],
            "flat size": ["vk_flat_100", "vk_flat_150"],
            "K x cap (final)": [f"vk_vstar_{K}{c}" for K in (3000, 4000) for c in ("", "_d6", "_d8")],
            "K past the edge (v* d6, round 4)": [f"vk_vstar_{K}_d6" for K in (3000, 4000, 5000, 6000)],
            "all": allv}


if __name__ == "__main__":
    main()
