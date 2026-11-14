"""Report tables from the scored simulation tags (sim/score.py csvs) and the curves.

    python3 -m research.predict.report.tables   -> data/out/predict/tables.md"""
from __future__ import annotations

import pandas as pd

from .. import OUT
from .md import md

COLS = {"arm": "arm", "L": "L ms", "fills_day": "fills/day", "net_day": "net $/day",
        "net_lo": "CI lo", "net_hi": "CI hi", "c_per_usd": "net c/$", "mk10_c": "10 s mk c/$",
        "mk10_day": "10 s mk $/day", "win": "win", "max_dd": "max DD $"}
NAMES = {"vt_v3p_m0.02_any": "**predictive taker (primary, frozen)**",
         "vt_v3p_m0.02_r0.1_s60_sl0.02": "predictive taker, refr 0.1 s (2nd look)",
         "vt_v3p_m0.02_r0.2_s150_sl0.02": "predictive taker, 150 sh (2nd look)",
         "vt_v1_m0.02_trigger": "predictive veto on their trigger",
         "vt_v1_m0.01_micf": "predictive veto on micf",
         "vt_v1_m0.03_any": "predictive taker, 1 s model, margin 3 c",
         "vm_fair0.03_p-0.03": "predictive maker (1 s model pulls)",
         "vm_v3p_fair0.02_p-0.03": "predictive maker (3 s model pulls, 2nd look)",
         "micf": "micf (strategy winner)", "theirs_micro": "their rule, rebuilt",
         "strategy_maker_mkm": "strategy maker (microprice pulls)",
         "leaderA_all": "leader A actual", "leaderB_all": "leader B actual"}


def sim_table(tag: str, arms=None) -> str:
    t = pd.read_csv(OUT / f"score-{tag}.csv")
    if arms is not None:
        t = t[t["arm"].isin(arms)]
    t = t.sort_values(["L", "mk10_day"], ascending=[True, False])
    t["arm"] = t["arm"].map(lambda a: NAMES.get(a, a))
    t["win"] = t["win"].map(lambda w: f"{w:.2f}")
    return md(t[list(COLS)].rename(columns=COLS), 1)


def paired_table(tag: str, arms=None) -> str:
    p = pd.read_csv(OUT / f"paired-{tag}.csv")
    if arms is not None:
        p = p[p["arm"].isin(arms)]
    p["arm"] = p["arm"].map(lambda a: NAMES.get(a, a))
    return md(p.rename(columns={"mk10_gain_day": "10 s mk gain vs micf $/day", "lo": "CI lo", "hi": "CI hi"}), 0)


def main() -> None:
    parts = []
    for tag, title in (("final", "Final test (run 3, frozen)"), ("final_comp", "Final test, 50 ms race window + half of each level"),
                       ("ext", "Extension of the frozen test (15:00-19:00 UTC)"),
                       ("dev1", "Run 3 dev hours (transfer check before the freeze)"),
                       ("sel1", "Run 2 select hours (selection)"), ("basemk_select", "Makers, run 2 select"),
                       ("basemk_dev3", "Makers, run 3 dev"), ("basemk_test3", "Makers, run 3 test")):
        if not (OUT / f"score-{tag}.csv").exists():
            continue
        arms = None
        if tag == "sel1":
            arms = list(NAMES)
        parts.append(f"### {title}\n\n" + sim_table(tag, arms) + "\n" + paired_table(tag, arms))
    (OUT / "tables.md").write_text("\n\n".join(parts) + "\n")
    print("\n\n".join(parts)[:3000])


if __name__ == "__main__":
    main()
