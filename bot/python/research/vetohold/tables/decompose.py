"""Step 2: why the veto arm loses under the hold (limit seen + 2 c, 60 sh, `real` hold).

(a) depth survival: shares at <= limit at decision (venue clock) vs at match; removed depth
    split into traded (prints on those levels in (t, match]) and pulled (the rest).
(b) adverse selection: hold-free markout (buy at seen at t, valued at match + 10 s) of orders
    weighted by their fill probability vs by their miss probability.
(c) drift: side-frame ask at match minus seen; ask at decision on the venue clock minus seen
    (our feed's staleness).
(d) veto: the same numbers for vt_any / micf, kept vs vetoed trigger signals, and by edge.

    PYTHONPATH=. python3 -m research.vetohold.tables.decompose -> data/out/vetohold/decompose.md"""
from __future__ import annotations

import numpy as np
import pandas as pd

from research.predict.report.md import md

from .. import ANY, MICF, OUT, VETO
from .common import paper_pnl, rows, stats


def profile(g: pd.DataFrame) -> dict:
    w = g["fillp_k2"]
    inst = lambda wt: (wt * g["mk_inst"]).sum() / (wt * g["seen"]).sum() * 100  # noqa: E731
    stale = g["ask_t"].isna() | (np.abs(g["ask_t"] - g["seen"]) > 0.005)
    return {"orders": len(g), "fill": w.mean(),
            "dep_t med": g["dep_t"].median(), "dep_m med": g["dep_m"].median(),
            "survive %": g["dep_m"].clip(upper=g["dep_t"]).sum() / g["dep_t"].sum() * 100,
            ">=60 sh survive %": (g["dep_m"] >= 60).mean() * 100,
            "pulled % of removed": (1 - g["traded"].sum() / g["removed"].sum()) * 100,
            "inst mk filled c/$": inst(w), "inst mk missed c/$": inst(1 - w),
            "ask drift p50 c": np.nanmedian(g["ask_m"] - g["seen"]) * 100,
            "ask drift mean c": np.nanmean(g["ask_m"] - g["seen"]) * 100,
            "stale at t %": stale.mean() * 100}


def bridge(d: pd.DataFrame, mk: list[str]) -> pd.DataFrame:
    """Paper log -> research replay at 150 ms -> real hold, $/day with volume and c/$."""
    v = d[d["arm"] == VETO]
    p = v[v["scen"] == "real"].copy()
    p["pp"] = paper_pnl(p)
    out = [dict(step="paper bot log", **_vol(p, "pp", "paper_cost", mk))]
    for sc, name in (("paper", "replay at 150 ms (venue clock)"), ("q10", "hold p10"),
                     ("q50", "hold p50"), ("real", "hold drawn (live distribution)")):
        out.append(dict(step=name, **_vol(v[v["scen"] == sc], "pnl_k2_60", "cost_k2_60", mk)))
    return pd.DataFrame(out)


def _vol(g, pnl, cost, mk):
    s = stats(g, pnl, cost, mk)
    days = len(mk) / 288
    return {"$ traded/day": g[cost].sum() / days, "mk10 c/$": s["c_per_$"], "$/day": s["usd_day"]}


def main():
    d = rows()
    mk = sorted(d["slug"].unique())
    real = d[d["scen"] == "real"]
    out = ["# Why the veto arm fails under the hold\n", "## Bridge: paper to live-like\n", md(bridge(d, mk), 2)]
    prof = [dict(set=f"{a} ({s})", **profile(d[(d["arm"] == a) & (d["scen"] == s)]))
            for a in (VETO, ANY, MICF) for s in ("paper", "real")]
    out += ["\n## (a)-(c) by arm, 150 ms replay vs real hold\n", md(pd.DataFrame(prof), 1)]
    v = real[real["arm"] == VETO].copy()
    v["paper_pnl"] = paper_pnl(v)
    st = v["ask_t"].isna() | (np.abs(v["ask_t"] - v["seen"]) > 0.005)
    rows_ = []
    for name, g in (("venue ask = seen at t", v[~st]), ("venue ask != seen at t (stale feed)", v[st])):
        sp, sr = stats(g, "paper_pnl", "paper_cost", mk), stats(g, "pnl_k2_60", "cost_k2_60", mk)
        rows_.append({"veto orders": name, "n": len(g), "paper $/day": sp["usd_day"], "paper c/$": sp["c_per_$"],
                      "real-hold $/day": sr["usd_day"], "real-hold c/$": sr["c_per_$"]})
    out += ["\n## Feed staleness at decision (veto)\n", md(pd.DataFrame(rows_), 1)]
    v["edge_q"] = pd.qcut(v["f_edge"], 5)
    v["mv_q"] = pd.qcut(v["f_perp_0.25"].rank(method="first"), 5, labels=False)
    for col, lab in (("edge_q", "model edge quintile"), ("mv_q", "perp 250 ms move quintile (signed)")):
        t = [dict(bin=str(b), **profile(g)) for b, g in v.groupby(col, observed=True)]
        out += [f"\n## (d) veto by {lab}\n", md(pd.DataFrame(t), 1)]
    try:
        tr = rows("rows-trigger")
        t = [dict(set=f"{a} ({s})", **profile(tr[(tr["arm"] == a) & (tr["scen"] == s)]))
             for a in ("trig_kept", "trig_vetoed") for s in ("paper", "real")]
        tm = sorted(tr["slug"].unique())
        for a in ("trig_kept", "trig_vetoed"):
            s = stats(tr[(tr["arm"] == a) & (tr["scen"] == "real")], "pnl_k2_60", "cost_k2_60", tm)
            t.append({"set": f"{a} real: mk10 c/$ {s['c_per_$']:+.1f} [{s['c_lo']:+.1f}, {s['c_hi']:+.1f}]"})
        out += ["\n## (d) trigger signals kept vs vetoed by the model (simulator tables, vetoed 20% sample)\n",
                md(pd.DataFrame(t), 1)]
    except FileNotFoundError:
        pass
    (OUT / "decompose.md").write_text("\n".join(out) + "\n")
    print("\n".join(out))


if __name__ == "__main__":
    main()
