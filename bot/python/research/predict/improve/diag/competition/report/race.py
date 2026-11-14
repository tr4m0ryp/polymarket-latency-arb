"""Race-aware label arms (race/label.py, sim kind `race`) next to their frozen siblings and
micf, under every fill model, paired market bootstrap.

Selection (fixed before reading select): per family (`any` vs vt_v1_m0.03_any, `trigger` vs
vt_v1_m0.02_trigger) the race arm with the largest select-window paired gain vs micf under
e+25; it is then read on unseen, quiet and busy beside the frozen sibling.

    python3 -m research.predict.improve.diag.competition.report.race"""
from __future__ import annotations

import pandas as pd

from .....report.md import md
from .. import CACHE, OUT
from ..sim.decide import RACE
from .boot import arm_cols, day_ci, fmt, load, markets, ratio_ci
from .whatif import _paired

FILLS = ("base", "e+10", "e+25", "comp", "e-25")
SIB = {"any": "vt_v1_m0.03_any", "trigger": "vt_v1_m0.02_trigger"}
MATCHED = ("vt_v1ravg_m0.03_any", "vt_v1rmin_m0.03_any", "vt_v1ravg_m0.02_trigger", "vt_v1rmin_m0.02_trigger")


def merged() -> tuple[pd.DataFrame, dict]:
    o, ids = load()
    r = pd.concat([pd.read_pickle(p) for p in sorted(CACHE.glob("orders-*-race.pkl"))], ignore_index=True)
    return pd.concat([o, r], ignore_index=True), ids


def family(arm: str) -> str:
    return "trigger" if arm.endswith("trigger") else "any"


def select(o, ids) -> dict:
    mk = markets(ids, "select")
    m0 = arm_cols(o, "micf", 0, "e+25", mk)
    best = {}
    for arm in RACE:
        g = _paired(arm_cols(o, arm, 0, "e+25", mk)["mk"], m0["mk"])[0]
        f = family(arm)
        if f not in best or g > best[f][1]:
            best[f] = (arm, g)
    return {f: a for f, (a, _) in best.items()}


def table(o, ids, arms, groups=("select", "unseen", "quiet", "busy")) -> pd.DataFrame:
    rows = []
    for g in groups:
        mk = markets(ids, g)
        for fm in FILLS:
            m0 = arm_cols(o, "micf", 0, fm, mk)
            for arm in arms:
                a = arm_cols(o, arm, 0, fm, mk)
                r = {"group": g, "fill": fm, "arm": arm, "fills/day": round(a["n"] / (len(mk) / 288)),
                     "mk10 c/$": fmt(ratio_ci(a["mk"], a["cost"]), 1), "mk10 $/day": fmt(day_ci(a["mk"])),
                     "vs micf": fmt(_paired(a["mk"], m0["mk"])[:3])}
                if arm in RACE:
                    sib = arm_cols(o, SIB[family(arm)], 0, fm, mk)
                    r["vs frozen sibling"] = fmt(_paired(a["mk"], sib["mk"])[:3])
                rows.append(r)
    return pd.DataFrame(rows)


def main() -> None:
    o, ids = merged()
    pick = select(o, ids)
    full = table(o, ids, tuple(SIB.values()) + tuple(RACE), groups=("select",))
    t = table(o, ids, tuple(SIB.values()) + tuple(pick.values()))
    same = table(o, ids, MATCHED, groups=("unseen", "quiet", "busy"))
    t.to_csv(OUT / "diag-competition-race-label.csv", index=False)
    txt = (f"# Race-aware label arms (L = 0)\n\nPicked on select (e+25 gain vs micf): {pick}\n\n"
           "## All race arms, select\n\n" + md(full.fillna(""), 1)
           + "\n\n## Picked arms vs frozen siblings\n\n" + md(t.fillna(""), 1)
           + "\n\n## Same margin as the frozen sibling (label effect only)\n\n" + md(same.fillna(""), 1))
    (OUT / "diag-competition-race-label.md").write_text(txt)
    print(txt)


if __name__ == "__main__":
    main()
