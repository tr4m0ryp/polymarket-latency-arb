"""What happened during the hold (send -> match -> ack): per-order table and a summary by i.

The venue matches about 14 ms before the ack (reports/live-hold.md), so the `ack` book snapshot is
the best view of the ask the order actually met. mk10 is the bought token's mid at ack + 10 s:
c/$ = 100 * (sh * mid - cost - fee) / cost for fills; for a miss the hypothetical markout is one
share bought at the seen ask (fee 0.07 p (1 - p)), 100 * (mid - seen - fee) / seen."""
from __future__ import annotations

import numpy as np
import pandas as pd

from btclat.trade.report.stats import boot_cpd

from .orders import fee_of

COLS = ["cid", "slug", "i", "i_mode", "k", "limit", "seen", "ask_match", "ask_send", "ask_move_c", "seen_to_match_c",
        "depth_send", "depth_ack", "depth_survival", "filled", "fill_px", "mk10_cpd", "miss_mk10_cpd", "first_ack_ms"]


def table(df: pd.DataFrame) -> pd.DataFrame:
    if not len(df):
        return pd.DataFrame(columns=COLS)
    s = df[df["sent"]].copy()
    g = lambda c: s[c] if c in s else pd.Series(np.nan, index=s.index)
    mid = g("bk_a10_mid")
    out = pd.DataFrame({"cid": s["cid"], "slug": s["slug"], "i": s["i"].round(3), "i_mode": s["i_mode"], "k": s["k"],
                        "limit": s["limit"], "seen": s["seen"], "ask_match": g("bk_ack_ba"), "ask_send": g("bk_send_ba")})
    out["ask_move_c"] = 100 * (out["ask_match"] - out["ask_send"])
    out["seen_to_match_c"] = 100 * (out["ask_match"] - out["seen"])
    out["depth_send"], out["depth_ack"] = g("bk_send_depth"), g("bk_ack_depth")
    out["depth_survival"] = (out["depth_ack"] / out["depth_send"]).where(out["depth_send"] > 0)
    out["filled"], out["fill_px"] = s["filled"], s["px"]
    out["mk10_cpd"] = np.where(s["filled"], 100 * (s["fill_sh"] * mid - s["fill_cost"] - s["fee"]) / s["fill_cost"], np.nan)
    out["miss_mk10_cpd"] = np.where(~s["filled"], 100 * (mid - s["seen"] - fee_of(s["seen"], 1.0)) / s["seen"], np.nan)
    out["first_ack_ms"] = s["first_ack_ms"]
    # kept for the summary bootstrap (not rendered)
    out["_num"] = np.where(s["filled"], s["fill_sh"] * mid - s["fill_cost"] - s["fee"], np.nan)
    out["_den"] = np.where(s["filled"], s["fill_cost"], np.nan)
    return out


def summary(t: pd.DataFrame, by: str) -> pd.DataFrame:
    rows = []
    for key, g in t.groupby(by, dropna=False):
        f = g[g["filled"]]
        m, lo, hi = boot_cpd(f["_num"], f["_den"], f["slug"])
        rows.append({by: key, "n": len(g), "fills": len(f), "fill_rate": len(f) / len(g), "mk10_cpd": m, "lo": lo, "hi": hi,
                     "miss_mk10_cpd": g["miss_mk10_cpd"].mean(), "ask_move_c": g["ask_move_c"].mean(),
                     "depth_survival": g["depth_survival"].mean(), "first_ack_p50_ms": g["first_ack_ms"].median()})
    return pd.DataFrame(rows)
