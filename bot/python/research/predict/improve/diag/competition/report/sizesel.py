"""Size rules pooled across the three size runs (fixed sizes `sweep`, edge-keyed `edge`,
`edge2`), one selection rule applied on select only, read on unseen / quiet / busy.

Rules: per arm, (guard) the size rule with the largest select-window paired gain vs the
deployed 60 sh under e+25 among rules whose comp gain CI lower bound on select is > 0, and
(robust) the rule with the largest comp gain CI lower bound on select.
It was written after the sweep / edge / edge2 tables had been printed, so the unseen read is a
diagnostic, not a blind test; the sealed prereg2 segment is the test.

    python3 -m research.predict.improve.diag.competition.report.sizesel"""
from __future__ import annotations

import pandas as pd

from .....report.md import md
from .. import CACHE, OUT
from ..sim.scen import EDGE, EDGE2, SWEEP
from .boot import arm_cols, day_ci, fmt, load, markets, ratio_ci
from .whatif import _paired

ARMS = (("vt_v1_m0.03_any", 0), ("vt_v1_m0.02_trigger", 0), ("vt_v1_m0.02_trigger", -40), ("micf", 0))
RULES = tuple(SWEEP) + tuple(EDGE) + tuple(k for k in EDGE2 if k not in EDGE)
FILLS = ("base", "e+25", "comp")


def merged() -> tuple[pd.DataFrame, dict]:
    o, ids = load()
    key = ["arm", "L", "m", "t"]
    for kind in ("sweep", "edge", "edge2"):
        s = pd.concat([pd.read_pickle(p) for p in sorted(CACHE.glob(f"orders-*-{kind}.pkl"))], ignore_index=True)
        s = s[key + [c for c in s.columns if "@" in c and c not in o.columns]]
        o = o.merge(s, on=key, how="left")
    return o, ids


def _gain(o, arm, L, rule, fm, mk):
    return _paired(arm_cols(o, arm, L, f"{rule}@{fm}", mk)["mk"], arm_cols(o, arm, L, fm, mk)["mk"])


def select(o, ids, robust: bool = False) -> dict:
    """guard: max e+25 gain among rules with comp CI low > 0; robust: max comp CI low bound."""
    mk = markets(ids, "select")
    pick = {}
    for arm, L in ARMS:
        if robust:
            ok = [(r, _gain(o, arm, L, r, "comp", mk)[1]) for r in RULES]
            ok = [x for x in ok if x[1] > 0]
        else:
            ok = [(r, _gain(o, arm, L, r, "e+25", mk)[0]) for r in RULES if _gain(o, arm, L, r, "comp", mk)[1] > 0]
        pick[(arm, L)] = max(ok, key=lambda x: x[1])[0] if ok else None
    return pick


def table(o, ids, pick, groups=("select", "unseen", "quiet", "busy")) -> pd.DataFrame:
    rows = []
    for g in groups:
        mk = markets(ids, g)
        for fm in FILLS:
            m0 = arm_cols(o, "micf", 0, fm, mk)
            for (arm, L), rule in pick.items():
                if rule is None:
                    continue
                a, ref = arm_cols(o, arm, L, f"{rule}@{fm}", mk), arm_cols(o, arm, L, fm, mk)
                rows.append({"group": g, "fill": fm, "arm": arm, "L": L, "rule": rule,
                             "sh/fill": round(a["sh"] / max(a["n"], 1)),
                             "mk10 c/$": fmt(ratio_ci(a["mk"], a["cost"]), 1), "mk10 $/day": fmt(day_ci(a["mk"])),
                             "vs deployed 60 sh": fmt(_paired(a["mk"], ref["mk"])[:3]),
                             "vs micf 60 sh": fmt(_paired(a["mk"], m0["mk"])[:3])})
    return pd.DataFrame(rows)


def main() -> None:
    o, ids = merged()
    txt = "# Size rule, competition-guarded selection\n"
    for name, rob in (("guard (max e+25 gain, comp CI low > 0)", False), ("robust (max comp CI low)", True)):
        pick = select(o, ids, rob)
        t = table(o, ids, pick)
        t.to_csv(OUT / f"diag-competition-sizesel{'-robust' if rob else ''}.csv", index=False)
        txt += f"\n## {name}\n\nPicked on select: {pick}\n\n" + md(t, 1) + "\n"
    (OUT / "diag-competition-sizesel.md").write_text(txt)
    print(txt)


if __name__ == "__main__":
    main()
