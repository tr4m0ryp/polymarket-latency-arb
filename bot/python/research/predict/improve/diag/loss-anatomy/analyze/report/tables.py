"""Compact markdown tables for the loss-anatomy result (selected rows / pivots of the CSVs)."""
from __future__ import annotations

import pandas as pd

from research.predict.report.md import md

WIN = ["select", "dev3", "test3r1", "ext"]
COMBOS = [("taker1s", 0), ("veto", 0), ("taker1s", -40), ("veto", -40), ("micf", 0)]


def _lab(x: pd.Series) -> pd.Series:
    return x.astype(str).str.replace(", 1000000000.0]", ", inf)", regex=False)


def _lo(b: str) -> float:
    return float(str(b).split(",")[0].strip("("))


def overview(o: pd.DataFrame) -> str:
    o = o.assign(cell=lambda d: d.apply(lambda r: f"{r.c_usd:+.1f} / {r.fills_day:,.0f}", axis=1))
    p = o.pivot_table(index=["arm", "L"], columns="window", values="cell", aggfunc="first")[WIN]
    return md(p.reset_index())


def decomp(d: pd.DataFrame) -> str:
    d = d.assign(fill=d["lose"].map({0.0: "winner", 1.0: "loser"}))
    cols = ["arm", "L", "fill", "n", "d_move", "d_half", "d_walk", "d_fee", "d_hold", "mk_sh"]
    return md(d[cols].sort_values(["arm", "L", "fill"], ascending=[False, False, False]), 2)


def auc(a: pd.DataFrame, n: int = 16) -> str:
    def cell(r, k):
        return f"{r[k]:.2f} [{r[k + '_lo']:.2f}, {r[k + '_hi']:.2f}] {int(r[k + '_win_same'])}/4"
    a = a[a["group"] != "post hoc"].copy()
    keys = [f"{x}_L{L}" for x, L in COMBOS]
    a["s"] = sum((a[k] - 0.5).abs() for k in keys[:4])
    a = a.nlargest(n, "s")
    out = pd.DataFrame({"var": a["var"], "group": a["group"],
                        **{k: [cell(r, k) for _, r in a.iterrows()] for k in keys}})
    return md(out)


def delta_bins(d: pd.DataFrame) -> str:
    d = d.assign(cell=lambda x: x.apply(lambda r: f"{r.c_usd:+.1f} ({r.fills}, {r.share_ext:.0%} ext)", axis=1))
    order = sorted(dict.fromkeys(d["delta_bin"]), key=_lo)
    p = d.pivot_table(index="delta_bin", columns=["arm", "L"], values="cell", aggfunc="first").reindex(order)
    p.index = _lab(pd.Series(p.index)).to_numpy()
    p.columns = [f"{a} L{L}" for a, L in p.columns]
    return md(p.rename_axis("delta c/bp").reset_index())


def delta_windows(d: pd.DataFrame) -> str:
    d = d[d["arm"] != "micf"]
    d = d.assign(cell=lambda x: x.apply(lambda r: f"{r['delta_median']:.1f} / {r['share_delta<5']:.0%} / "
                                        f"{r['lowdelta_fills_day']:,.0f}", axis=1))
    p = d.pivot_table(index=["arm", "L"], columns="window", values="cell", aggfunc="first")[WIN]
    return md(p.reset_index())


def calib(c: pd.DataFrame, L: int) -> str:
    c = c[c["L"] == L][["regime", "delta_bin", "rows", "mkts", "pred_c", "real_1s_c", "real_10s_c"]].copy()
    c["delta_bin"] = _lab(c["delta_bin"])
    c[["rows", "mkts"]] = c[["rows", "mkts"]].astype(int)
    return md(c, 1)


def hours(h: pd.DataFrame) -> str:
    h = h[(h["L"] == 0) & h["window"].isin(["test3r1", "ext"]) & (h["arm"] != "micf")]
    h = h.assign(cell=lambda x: x.apply(lambda r: f"{r.c_usd:+.1f} ({r.fills}, d {r.delta_med:.0f})", axis=1))
    p = h.pivot_table(index=["window", "hour"], columns="arm", values="cell", aggfunc="first")
    return md(p.reset_index())


def gate_grid(g: pd.DataFrame) -> str:
    g = g[["arm", "L", "thr", "picked", "fit_gain_day", "read_dropped", "read_gain_day", "read_lo",
           "read_hi", "read_p_le0", "read_c_before", "read_c_after"]]
    return md(g, 1)


def rules(r: pd.DataFrame) -> str:
    r = r.assign(cell=lambda x: x.apply(lambda q: f"{q.gain_day:+,.0f} [{q.lo:+,.0f}, {q.hi:+,.0f}] ({q.dropped})", axis=1))
    p = r.pivot_table(index=["rule", "arm", "L"], columns="window", values="cell", aggfunc="first")[WIN]
    return md(p.reset_index())


def comp(c: pd.DataFrame) -> str:
    c = c.assign(cell=lambda x: x.apply(lambda r: f"{r.c_usd:+.1f} ({r.fills})", axis=1))
    p = c.pivot_table(index="delta_bin", columns=["arm", "run"], values="cell", aggfunc="first")
    p = p.reindex(sorted(p.index, key=_lo))
    p.index = _lab(pd.Series(p.index)).to_numpy()
    p.columns = [f"{a} {r}" for a, r in p.columns]
    return md(p.rename_axis("delta c/bp").reset_index())


def tails(t: pd.DataFrame) -> str:
    return md(t[["arm", "L", "markets", "usd_total", "bottom5_usd", "bottom5_fills", "top5_usd", "losing_mkts"]], 2)


def worst(w: pd.DataFrame) -> str:
    cols = ["window", "m", "hour", "n", "usd", "c_usd", "f_pred", "f_abs_mid", "f_secs_left", "f_burst_pos",
            "f_rv60", "m_range_c"]
    return md(w[cols], 2)
