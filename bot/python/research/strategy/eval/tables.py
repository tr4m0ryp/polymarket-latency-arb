"""Markdown tables for reports/strategy-search.md from the held-out summaries (eval/summary.py).

    python3 -m research.strategy.eval.tables

Writes data/out/strategy/tables.md: main table (every arm at L = 50 / 100 / 150 ms, plus the
later looks at the winner's family: arms/ceiling.py, arms/final3.py), the
infrastructure points (L = -40 / 0 ms), and the sensitivity runs (250 ms hold, harsher
competition, pessimistic maker fills)."""
from __future__ import annotations

import pandas as pd

from .. import OUT

ARMS = [  # (arm, short name) in report order
    ("theirs_micro", "(a) their rule, rebuilt (microprice trigger)"),
    ("theirs_spot", "(a') their rule, first read (3 s spot move)"),
    ("theirs_perp", "(b) their rule on the perp mid"),
    ("micf_pzm_m0.01_t0.002", "**microprice trigger + fair filter (micf)**"),
    ("mic_w0.05_t0.5_b0.01-0.99_l30_r0.2", "microprice trigger, selective"),
    ("mom_smid_w0.2_t0.3_b0.99_r2", "momentum, tuned (spot mid 0.2 s)"),
    ("fair_pzx_m0.02_f0_r0.1_s60", "fair taker, 60 sh (inv. 1)"),
    ("fair_pz_m0.1_f0.02_r0.02_s300", "fair taker, depth-sized"),
    ("fair_pz2_m0.08_r0.25_s300", "fair taker refit on v2"),
    ("fair_pzm_m0.08_r0.25_s300", "fair taker + microprice buckets"),
    ("fair_pzxi_m0.03_f0_r0.1_s150", "fair taker + perp imbalance (inv. 3)"),
    ("mk_pz_h0.05_t30_p0.1_w1", "maker, fair quotes, perp pulls (inv. 2)"),
    ("mkm_h0.05_p0.01_w0.5", "maker, microprice pulls"),
    ("mkb_pz_p0_i0_t30_s60", "maker, book-anchored (inv. 2b)"),
    ("micf_pzm_m0.01_t0.002_w0.05_r0.2_s150", "micf, 150 sh, 50 ms window (ceiling, 2nd look)"),
    ("micfa_m0.01_t0.002_w0.05_s150", "micf + books agree, 150 sh (post-hoc, 3rd look)"),
    ("theirs_micro_agree", "(a+) their rule + books-agree filter (post-hoc)"),
    ("leaderA_all", "(c) leader A actual, all fills"),
    ("leaderB_all", "(c) leader B actual, all fills"),
]


def _md(rows: list[list], head: list[str]) -> str:
    out = "| " + " | ".join(head) + " |\n|" + "---|" * len(head) + "\n"
    return out + "".join("| " + " | ".join(str(v) for v in r) + " |\n" for r in rows)


def _fmt(r) -> list:
    ci = f"{r.net_lo:+,.0f} .. {r.net_hi:+,.0f}"
    mk = "" if pd.isna(r.mk10_c) else f"{r.mk10_c:+.1f}"
    return [f"{r.fills_day:,.0f}", f"{r.net_day:+,.0f}", ci, f"{r.c_per_usd:+.1f}", mk,
            f"{r.win:.2f}", f"{r.max_dd:,.0f}"]


def block(t: pd.DataFrame, Ls, arms=ARMS) -> str:
    head = ["arm", "L ms", "fills/day", "net $/day", "95% CI $/day", "net c/$", "10 s mk c/$",
            "win", "max DD $"]
    rows = []
    for arm, name in arms:
        for L in Ls:
            x = t[(t["arm"] == arm) & (t["L"] == (0 if arm.startswith("leader") else L))]
            if len(x):
                rows.append([name, "actual" if arm.startswith("leader") else L, *_fmt(x.iloc[0])])
            if arm.startswith("leader"):
                break
    return _md(rows, head)


def main() -> None:
    t = pd.read_csv(OUT / "heldout-test.csv")
    from .metrics import table
    from .score import load
    for tag in ("ceil", "final3"):  # later looks at the winner's family, run once each
        if (OUT / f"agg-{tag}.pkl").exists():
            agg, mk = load(tag, "test")
            t = pd.concat([t, table(agg, mk)], ignore_index=True)
    parts = [f"held-out: {int(t['hours'].dropna().iloc[0] * 12)} markets, "
             f"{t['hours'].dropna().iloc[0]:.1f} h\n", "## Main (hold 150 ms)\n", block(t, (50, 100, 150)),
             "\n## Infrastructure points (L = -40 split Tokyo build, 0 Dublin)\n",
             block(t, (-40, 0), [a for a in ARMS if not a[0].startswith("leader")])]
    takers = [a for a in ARMS[:11]]
    makers = [a for a in ARMS[11:14]]
    for suf, title, arms in (
            ("_comp", "50 ms race window, half of each level (takers only; makers unchanged)", takers),
            ("_h25", "250 ms hold (makers; for takers a 250 ms hold equals L + 100 ms in the main "
                     "table)", makers),
            ("_x0", "pessimistic maker fills (crossing orders fill at once, not after the hold)",
             makers)):
        p = OUT / f"heldout-test{suf}.csv"
        if p.exists():
            s = pd.read_csv(p)
            parts += [f"\n## Sensitivity: {title}\n", block(s, sorted(s["L"].unique()), arms)]
    (OUT / "tables.md").write_text("\n".join(parts))
    print("\n".join(parts))


if __name__ == "__main__":
    main()
