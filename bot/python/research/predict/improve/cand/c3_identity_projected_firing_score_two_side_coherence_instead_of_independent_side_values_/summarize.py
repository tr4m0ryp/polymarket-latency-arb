"""Markdown tables of the C3 runs: the picked candidate next to its frozen arm (paired gain vs
vt_any for taker families, vs the veto for veto families) and the every-variant sweep.

    python3 -m research.predict.improve.cand.<pkg>.summarize coh_taker coh_veto ...
Writes data/out/predict/improve/c3_coherence/summary.md."""
from __future__ import annotations

import json
import sys

import pandas as pd

from research.predict import OUT
from research.predict.improve.harness.guard import SEALED

DST = OUT / "improve" / "c3_coherence"
SETS = ["A:eval", "B:eval", "CV:all", "CV:busyQ", "A:busy15", "A:ext", "unseen251"]
REF = {"vt": "vt_v1_m0.03_any", "veto": "vt_v1_m0.02_trigger"}


def _ci(v, lo, hi) -> str:
    return f"{v:+,.0f} [{lo:+,.0f}, {hi:+,.0f}]"


def _rows(t: pd.DataFrame, arm: str, ref: str, label: str) -> list[dict]:
    out = []
    for (L, var), s in [((0, "base"), SETS), ((-40, "base"), ["A:eval", "B:eval", "CV:all", "CV:busyQ"]),
                        ((0, "comp"), ["CV:all", "CV:busyQ", "A:ext"])]:
        for st in s:
            r = t[(t["set"] == st) & (t["arm"] == arm) & (t["L"] == L) & (t["var"] == var)]
            if not len(r):
                continue
            r = r.iloc[0]
            g = "g_vt" if ref == "vt" else "g_veto"
            out.append({"arm": label, "L": L, "var": var, "set": st, "fills/day": f"{r.fills_day:,.0f}",
                        "mk c/$": f"{r.mk10_c:+.1f}", "mk $/day [CI]": _ci(r.mk10_day, r.mk10_lo, r.mk10_hi),
                        f"gain vs {ref} [CI]": _ci(r[g], r[g + "_lo"], r[g + "_hi"]) if arm != REF[ref] else "",
                        "gain vs micf [CI]": _ci(r.g_micf, r.g_micf_lo, r.g_micf_hi),
                        "worst-5 $": f"{r.worst5:+,.0f}"})
    return out


def _md(rows: list[dict]) -> str:
    if not rows:
        return ""
    cols = list(rows[0])
    s = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    s += ["| " + " | ".join(str(r.get(c, "")) for c in cols) + " |" for r in rows]
    return "\n".join(s)


def family(name: str) -> str:
    d = DST / name
    c = pd.read_csv(d / "cand_veto.csv")
    ch = json.loads((d / "chosen.json").read_text())
    ref = "veto" if "veto" in name else "vt"
    rows = _rows(c, "candidate", ref, f"{name} (A={ch['A']}, B={ch['B']})") + _rows(c, REF[ref], ref, REF[ref])
    rows.sort(key=lambda r: (r["var"] != "base", -r["L"], SETS.index(r["set"]) if r["set"] in SETS else 9))
    v = pd.read_csv(d / "variants.csv")
    sw = []
    g = "g_vt" if ref == "vt" else "g_veto"
    for st in ("CV:all", "CV:busyQ", "A:busy15"):
        for r in v[(v["set"] == st) & (v["L"] == 0) & (v["var"] == "base")].itertuples():
            rr = r._asdict()
            sw.append({"set": st, "variant": r.arm, "fills/day": f"{r.fills_day:,.0f}", "mk c/$": f"{r.mk10_c:+.1f}",
                       "mk $/day": f"{r.mk10_day:+,.0f}", f"gain vs {ref} [CI]": _ci(rr[g], rr[g + "_lo"], rr[g + "_hi"]),
                       "worst-5 $": f"{r.worst5:+,.0f}"})
    return (f"## {name}\n\nPicked: A = `{ch['A']}`, B = `{ch['B']}` (lcb criterion, L = 0, choose windows only).\n\n"
            + _md(rows) + "\n\nEvery variant, L = 0 base (in-sample for the choice; sweep and kill test 3 only):\n\n"
            + _md(sw) + "\n")


def _g(t, arm, st, L, var, g):
    r = t[(t["set"] == st) & (t["arm"] == arm) & (t["L"] == L) & (t["var"] == var)]
    return _ci(r[g].iloc[0], r[g + "_lo"].iloc[0], r[g + "_hi"].iloc[0]) if len(r) else ""


def compact(names) -> str:
    """One row per family: the picked candidate's paired gain vs its frozen arm, every read."""
    rows = []
    for n in names:
        d = DST / n
        if not (d / "cand_veto.csv").exists():
            continue
        c = pd.read_csv(d / "cand_veto.csv")
        ch = json.loads((d / "chosen.json").read_text())
        assert json.loads((d / "meta.json").read_text())["max_start"] < SEALED, f"{n}: sealed market in run"
        g = "g_veto" if "veto" in n else "g_vt"
        r0 = c[(c["set"] == "CV:all") & (c["arm"] == "candidate") & (c["L"] == 0) & (c["var"] == "base")].iloc[0]
        rows.append({"family": n, "vs": "veto" if g == "g_veto" else "vt_any", "picked A / B": f"{ch['A']} / {ch['B']}",
                     "CV:all fills/day, mk c/$": f"{r0.fills_day:,.0f}, {r0.mk10_c:+.1f}",
                     "A:eval L0": _g(c, "candidate", "A:eval", 0, "base", g),
                     "B:eval L0": _g(c, "candidate", "B:eval", 0, "base", g),
                     "CV:all L0": _g(c, "candidate", "CV:all", 0, "base", g),
                     "CV:busyQ L0": _g(c, "candidate", "CV:busyQ", 0, "base", g),
                     "A:busy15 L0": _g(c, "candidate", "A:busy15", 0, "base", g),
                     "CV:all L0 comp": _g(c, "candidate", "CV:all", 0, "comp", g),
                     "CV:all L-40": _g(c, "candidate", "CV:all", -40, "base", g)})
    return _md(rows)


def mechanism() -> str:
    """e decomposition at the frozen arms' firing rows (L = 0) and the promoted / dropped split."""
    out = []
    p = DST / "diag_e2_decomp.csv"
    if p.exists():
        d = pd.read_csv(p)
        d = d[(d["L"] == 0) & d["arm"].isin(["vt_any", "veto", "all_rows"])]
        out.append("Mechanism, L = 0, frozen firing rows (cents; err = pred_up + pred_dn + c_m at the match book, "
                   "dc = c_seen - c_m, y = best-level 1 s value, lo/hi = e tercile):\n\n" + _md(
            [{"arm": r.arm, "window": r.win, "rows": int(r.n), "e (seen)": f"{r.e_c:+.2f}", "err (true)": f"{r.err_c:+.2f}",
              "dc": f"{r.dc_c:+.2f}", "e_hat (c_hat)": f"{r.ehat_c:+.2f}", "y low-e": f"{r.y_loe_c:+.1f}",
              "y high-e": f"{r.y_hie_c:+.1f}"} for r in d.itertuples()]))
    p = DST / "split_taker" / "variants.csv"
    if p.exists():
        v = pd.read_csv(p)
        v = v[(v["L"] == 0) & (v["var"] == "base") & v["set"].isin(["CV:all", "CV:busyQ", "A:ext", "A:busy15"])]
        out.append("Orders the projection admits (promo) vs removes (drop) relative to the frozen rule, simulated alone, "
                   "L = 0 base:\n\n" + _md([{"set": r.set, "orders": r.arm, "fills/day": f"{r.fills_day:,.0f}",
                                               "mk c/$": f"{r.mk10_c:+.1f}", "mk $/day [CI]": _ci(r.mk10_day, r.mk10_lo, r.mk10_hi)}
                                              for r in v.itertuples()]))
    return "\n\n".join(out)


def main() -> None:
    text = ("# C3 identity-projected firing score: harness results\n\nPaired 10 s markout gain $/day vs the frozen arm "
            "[95% market bootstrap]:\n\n" + compact(sys.argv[1:]) + "\n\n" + mechanism() + "\n\n"
            + "\n".join(family(n) for n in sys.argv[1:]))
    (DST / "summary.md").write_text(text)
    print(text)


if __name__ == "__main__":
    main()
