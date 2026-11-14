"""Size sweep of the winner (100-300 sh; `--kind edge`: shares scaled by the predicted value)
under the base, e+25 and comp fill models, paired vs the same arm at 60 sh and vs micf at
60 sh (the frozen baseline), per window group.

    python3 -m research.predict.improve.diag.competition.report.sweep [--kind sweep|edge]"""
from __future__ import annotations

import argparse

import pandas as pd

from .....report.md import md
from .. import CACHE, OUT
from .boot import arm_cols, day_ci, fmt, load, markets, ratio_ci
from ..sim.scen import EDGE, EDGE2, SWEEP
from .whatif import _paired

ARMS = (("vt_v1_m0.03_any", 0), ("vt_v1_m0.02_trigger", 0), ("vt_v1_m0.02_trigger", -40), ("micf", 0))
RULES = {"sweep": tuple(SWEEP), "edge": tuple(EDGE), "edge2": tuple(EDGE2)}
FILLS = ("base", "e+25", "comp")


def merged(kind: str) -> tuple[pd.DataFrame, dict]:
    o, ids = load()
    key = ["arm", "L", "m", "t"]
    parts = [pd.read_pickle(p) for p in sorted(CACHE.glob(f"orders-*-{kind}.pkl"))]
    s = pd.concat(parts, ignore_index=True)
    s = s[key + [c for c in s.columns if c.startswith(RULES[kind]) and c not in o.columns]]
    return o.merge(s, on=key, how="left"), ids


def table(o: pd.DataFrame, ids: dict, sizes, groups=("select", "unseen", "busy")) -> pd.DataFrame:
    rows = []
    for g in groups:
        mk = markets(ids, g)
        for fm in FILLS:
            m0 = arm_cols(o, "micf", 0, fm, mk)
            for arm, L in ARMS:
                ref = arm_cols(o, arm, L, fm, mk)
                for size in ("60",) + tuple(sizes):
                    a = ref if size == "60" else arm_cols(o, arm, L, f"{size}@{fm}", mk)
                    r = {"group": g, "fill": fm, "arm": arm, "L": L, "size": size,
                         "mk10 c/$": fmt(ratio_ci(a["mk"], a["cost"]), 1), "mk10 $/day": fmt(day_ci(a["mk"]))}
                    if size != "60":
                        r["vs 60 sh"] = fmt(_paired(a["mk"], ref["mk"])[:3])
                    if arm != "micf" or size != "60":
                        r["vs micf 60 sh"] = fmt(_paired(a["mk"], m0["mk"])[:3])
                    rows.append(r)
    return pd.DataFrame(rows)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--kind", default="sweep")
    a = ap.parse_args()
    o, ids = merged(a.kind)
    t = table(o, ids, RULES[a.kind])
    t.to_csv(OUT / f"diag-competition-{a.kind}.csv", index=False)
    (OUT / f"diag-competition-{a.kind}.md").write_text(f"# Size rules: {a.kind} (paired, market bootstrap)\n\n" + md(t.fillna(""), 1))
    print(md(t.fillna(""), 1))


if __name__ == "__main__":
    main()
