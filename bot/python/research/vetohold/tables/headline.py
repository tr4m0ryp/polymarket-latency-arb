"""Step 1: the veto arm's own paper orders through the measured hold, every limit.

    PYTHONPATH=. python3 -m research.vetohold.tables.headline -> data/out/vetohold/headline.md"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from research.predict.report.md import md

from .. import ANY, LIMS, MICF, OUT, VETO
from .common import ci, paired, paper_pnl, rows, stats

SCEN = ("paper", "nohold", "q10", "q25", "q50", "q75", "q90", "real")


def lim_row(g: pd.DataFrame, lim: str, mk: list[str]) -> dict:
    s = stats(g, f"pnl_{lim}_60", f"cost_{lim}_60", mk)
    r = stats(g, f"res_{lim}_60", f"cost_{lim}_60", mk)
    sh = g[f"sh_{lim}_60"]
    return {"limit": lim, "fill": g[f"fillp_{lim}"].mean(), "sh/order": sh.mean(),
            "px - seen c": (g[f"cost_{lim}_60"] - sh * g["seen"]).sum() / sh.sum() * 100,
            "mk10 c/$": ci(s, "c_per_$", "c_lo", "c_hi"), "res c/$": ci(r, "c_per_$", "c_lo", "c_hi"),
            "$/order": g[f"pnl_{lim}_60"].mean(), "$/day": ci(s, "usd_day", "d_lo", "d_hi", 0),
            "res $/day": ci(r, "usd_day", "d_lo", "d_hi", 0)}


def main():
    d = rows()
    mk = sorted(d["slug"].unique())
    hold = json.loads((OUT / "hold.json").read_text())
    out = [f"# Veto arm under the measured hold\n\nmarkets {len(mk)}, live hold n {hold['n']}: "
           + ", ".join(f"{k} {v[0] * 1e3:.0f} ms" for k, v in hold["scenarios"].items()) + "\n"]
    v = d[(d["arm"] == VETO) & (d["scen"] == "real")].copy()
    v["paper_pnl"] = paper_pnl(v)
    sp = stats(v, "paper_pnl", "paper_cost", mk)
    out.append(f"## Paper bot's own log, same orders\n\norders {len(v)}, fill {np.mean(v['paper_fill'] > 0):.3f}, "
               f"mk10 {ci(sp, 'c_per_$', 'c_lo', 'c_hi')} c/$, {ci(sp, 'usd_day', 'd_lo', 'd_hi', 0)} $/day\n")
    for sc, title in (("real", "Real hold (each order draws its hold from the live distribution)"),
                      ("paper", "Research replay at 150 ms (the simulator's hold), for reference"),
                      ("nohold", "No hold (3 ms), for reference")):
        g = d[(d["arm"] == VETO) & (d["scen"] == sc)]
        out += [f"\n## {title}, 60 sh, every limit\n", md(pd.DataFrame([lim_row(g, x, mk) for x in LIMS]), 3)]
    t2 = []
    for sc in SCEN:
        g = d[(d["arm"] == VETO) & (d["scen"] == sc)]
        for lim in ("k2", "k5", "k10"):
            r = lim_row(g, lim, mk)
            t2.append({"hold": sc, **{k: r[k] for k in ("limit", "fill", "mk10 c/$", "$/day")}})
    out += ["\n## Per hold scenario\n", md(pd.DataFrame(t2), 3)]
    t3 = []
    for sc in ("paper", "q50", "real"):
        m = d[(d["arm"] == MICF) & (d["scen"] == sc)]
        for arm in (VETO, ANY, MICF):
            g = d[(d["arm"] == arm) & (d["scen"] == sc)]
            s = stats(g, "pnl_k2_60", "cost_k2_60", mk)
            p = paired(g, "pnl_k2_60", m, "pnl_k2_60", mk) if arm != MICF else {"gain_day": np.nan, "g_lo": np.nan, "g_hi": np.nan}
            t3.append({"hold": sc, "arm": arm, "orders": len(g), "fill": g["fillp_k2"].mean(),
                       "mk10 c/$": ci(s, "c_per_$", "c_lo", "c_hi"), "$/day": ci(s, "usd_day", "d_lo", "d_hi", 0),
                       "gain vs micf $/day": ci(p, "gain_day", "g_lo", "g_hi", 0)})
    out += ["\n## Arms side by side (seen + 2 c, 60 sh)\n", md(pd.DataFrame(t3), 3)]
    t4 = []
    for q in (5, 15, 30, 60):
        for lim in ("k2", "k5"):
            s = stats(v, f"pnl_{lim}_{q}", f"cost_{lim}_{q}", mk)
            t4.append({"size sh": q, "limit": lim, "mk10 c/$": ci(s, "c_per_$", "c_lo", "c_hi"),
                       "$/day": ci(s, "usd_day", "d_lo", "d_hi", 0)})
    out += ["\n## Real hold by order size\n", md(pd.DataFrame(t4), 3)]
    (OUT / "headline.md").write_text("\n".join(out) + "\n")
    print("\n".join(out))


if __name__ == "__main__":
    main()
