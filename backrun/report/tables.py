"""Per-delay table of one arm: orders, fill rates, and gross edge in cents per dollar for
(a) every order at the seen ask, (b) what fills, (c) what does not, with market-bootstrap
95% intervals. Edge = held to resolution ($1 per winning share minus the price paid), before
fees. `mk10_*` = the same against the venue mid 10 s after the match."""
from __future__ import annotations

import numpy as np
import pandas as pd

from .. import CLIP, DELAYS
from .boot import draws, ratio, sums

EPS = 1e-6


def _cols(df: pd.DataFrame, d: int) -> pd.DataFrame:
    sh, cost, want, seen, won = (df[c] for c in (f"sh_{d}", f"cost_{d}", "want", "seen", "won"))
    miss = want - sh
    px = (cost / sh.where(sh > 0)).fillna(0.0)
    return pd.DataFrame({
        "slug": df["slug"], "one": 1.0, "filled": (sh > 0) * 1.0, "full": (sh >= want - EPS) * 1.0,
        "sought": CLIP, "cost": cost,
        "all_v": want * (won - seen), "all_c": want * seen,
        "fil_v": sh * won - cost,
        "mis_v": miss * (won - seen), "mis_c": miss * seen,
        "fil_at_seen_v": sh * (won - seen), "fil_at_seen_c": sh * seen,
        "mk_fil_v": sh * df[f"mk10_{d}"] - cost,
        "mk_all_v": want * (df["mk10_0"] - seen),
        "fee": 0.07 * (1 - px) * cost, "gone": (df[f"depth_{d}"] <= 0) * 1.0})


def delay_row(df: pd.DataFrame, d: int) -> dict:
    c = _cols(df, d)
    names = [x for x in c.columns if x != "slug"]
    s = sums(c, names)
    k = {n: i for i, n in enumerate(names)}
    idx = draws(len(s))
    r = lambda a, b, sc=100.0: ratio(s, k[a], k[b], idx, sc)   # noqa: E731
    b_tot = s[idx].sum(1)
    ea = 100 * b_tot[:, k["all_v"]] / b_tot[:, k["all_c"]]
    ef = 100 * b_tot[:, k["fil_v"]] / np.where(b_tot[:, k["cost"]] > 0, b_tot[:, k["cost"]], np.nan)
    em = 100 * b_tot[:, k["mis_v"]] / np.where(b_tot[:, k["mis_c"]] > 0, b_tot[:, k["mis_c"]], np.nan)
    tot = s.sum(0)

    def diff(x, y, px, py):
        lo, hi = np.nanpercentile(x - y, [2.5, 97.5])
        return {"est": round(px - py, 3), "lo": round(float(lo), 3), "hi": round(float(hi), 3)}
    e_all, e_fil, e_mis = r("all_v", "all_c"), r("fil_v", "cost"), r("mis_v", "mis_c")
    out = {"delay_ms": d, "orders": int(tot[k["one"]]), "markets": len(s),
           "fill_rate_count": r("filled", "one", 1.0), "full_fill_rate_count": r("full", "one", 1.0),
           "fill_rate_dollars": r("cost", "sought", 1.0), "depth_gone_share": r("gone", "one", 1.0),
           "edge_all_cpd": e_all, "edge_filled_cpd": e_fil, "edge_missed_cpd": e_mis,
           "edge_filled_at_seen_cpd": r("fil_at_seen_v", "fil_at_seen_c"),
           "mk10_filled_cpd": r("mk_fil_v", "cost"), "mk10_all_cpd": r("mk_all_v", "all_c"),
           "fee_filled_cpd": r("fee", "cost"), "dollars_filled": round(float(tot[k["cost"]]), 2)}
    if e_fil["est"] is not None:
        out["adverse_selection_cpd"] = diff(ef, ea, e_fil["est"], e_all["est"])
    if e_fil["est"] is not None and e_mis["est"] is not None:
        out["filled_minus_missed_cpd"] = diff(ef, em, e_fil["est"], e_mis["est"])
    return out


def arm_table(df: pd.DataFrame) -> list[dict]:
    return [delay_row(df, d) for d in DELAYS]


def by_day(df: pd.DataFrame, d: int) -> list[dict]:
    """The same row per UTC day: a check that one day does not carry the result."""
    day = (df["t"] // 86400).astype(int)
    out = []
    for k, g in df.groupby(day):
        if g["slug"].nunique() >= 20:
            x = delay_row(g, d)
            out.append({"utc_day": int(k), **{c: x[c] for c in (
                "orders", "markets", "fill_rate_dollars", "edge_all_cpd", "edge_filled_cpd")}})
    return out
