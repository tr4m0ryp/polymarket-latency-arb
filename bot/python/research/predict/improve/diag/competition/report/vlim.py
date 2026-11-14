"""Competition-adaptive limits (sim/vlim.py, sim kind `vlim`): each rule vs the same arm at
60 sh / + 2 c and vs micf at 60 sh under the same fill model, paired market bootstrap.

Selection (fixed before reading select): per arm, the rule with the largest select-window
paired gain vs the deployed arm under e+25 among rules whose comp gain is also >= 0; read on
unseen / quiet / busy.

    python3 -m research.predict.improve.diag.competition.report.vlim"""
from __future__ import annotations

import pandas as pd

from .....report.md import md
from .. import CACHE, OUT
from ..sim.vlim import VLIM
from .boot import arm_cols, day_ci, fmt, load, markets, ratio_ci
from .whatif import _paired

ARMS = (("vt_v1_m0.03_any", 0), ("vt_v1_m0.02_trigger", 0), ("vt_v1_m0.02_trigger", -40), ("micf", 0))
FILLS = ("base", "e+25", "comp", "e-25")


def merged() -> tuple[pd.DataFrame, dict]:
    o, ids = load()
    key = ["arm", "L", "m", "t"]
    s = pd.concat([pd.read_pickle(p) for p in sorted(CACHE.glob("orders-*-vlim.pkl"))], ignore_index=True)
    s = s[key + [c for c in s.columns if "@" in c]]
    return o.merge(s, on=key, how="left"), ids


def _sc(rule: str, fm: str) -> str:
    return fm if rule == "60" else f"{rule}@{fm}"


def select(o, ids) -> dict:
    mk = markets(ids, "select")
    pick = {}
    for arm, L in ARMS:
        best = None
        for rule in VLIM:
            g = {fm: _paired(arm_cols(o, arm, L, _sc(rule, fm), mk)["mk"], arm_cols(o, arm, L, fm, mk)["mk"])[0]
                 for fm in ("e+25", "comp")}
            if g["comp"] >= 0 and (best is None or g["e+25"] > best[1]):
                best = (rule, g["e+25"])
        pick[(arm, L)] = best[0] if best else None
    return pick


def table(o, ids, rules_for, groups=("select", "unseen", "quiet", "busy")) -> pd.DataFrame:
    rows = []
    for g in groups:
        mk = markets(ids, g)
        for fm in FILLS:
            m0 = arm_cols(o, "micf", 0, fm, mk)
            for arm, L in ARMS:
                ref = arm_cols(o, arm, L, fm, mk)
                for rule in ("60",) + tuple(rules_for(arm, L)):
                    a = arm_cols(o, arm, L, _sc(rule, fm), mk)
                    r = {"group": g, "fill": fm, "arm": arm, "L": L, "rule": rule,
                         "sh/fill": round(a["sh"] / max(a["n"], 1)),
                         "mk10 c/$": fmt(ratio_ci(a["mk"], a["cost"]), 1), "mk10 $/day": fmt(day_ci(a["mk"])),
                         "vs micf 60 sh": fmt(_paired(a["mk"], m0["mk"])[:3]) if (arm, rule) != ("micf", "60") else ""}
                    if rule != "60":
                        r["vs deployed"] = fmt(_paired(a["mk"], ref["mk"])[:3])
                    rows.append(r)
    return pd.DataFrame(rows)


def main() -> None:
    o, ids = merged()
    pick = select(o, ids)
    full = table(o, ids, lambda a, L: tuple(VLIM), groups=("select",))
    t = table(o, ids, lambda a, L: tuple(x for x in (pick[(a, L)], "ek3000_60_200") if x))
    full.to_csv(OUT / "diag-competition-vlim-select.csv", index=False)
    t.to_csv(OUT / "diag-competition-vlim.csv", index=False)
    txt = (f"# Competition-adaptive limits\n\nPicked on select (e+25 gain vs deployed, comp >= 0): {pick}\n\n"
           "## Picked rules (+ size-only reference)\n\n" + md(t.fillna(""), 1)
           + "\n\n## Every rule, select\n\n" + md(full.fillna(""), 1))
    (OUT / "diag-competition-vlim.md").write_text(txt)
    print(f"picked {pick}")


if __name__ == "__main__":
    main()
