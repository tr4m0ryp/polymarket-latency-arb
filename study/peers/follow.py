"""Followers: wallets outside the latency set that buy the side the bots just
bought, a few seconds later.

For every taker fill of a non-latency wallet, measure the time since the
latest latency burst on the SAME (market, side) and on the OPPOSITE side.
A follower's USD lands 1..FOLLOW_S s after same-side bursts much more often
than after opposite-side bursts (the control: same market, same moment of
the window, same activity level, wrong direction).
  follow_same / follow_opp   USD share of its fills in that 1..FOLLOW_S window
  excess                     follow_same - follow_opp
In 5m/15m bursts are so dense that both shares saturate, so the sharper test
is direction: among fills whose most recent burst (either side) came 1..DIR_S
s earlier, the USD share that went the SAME way as that burst (0.5 = blind).
  dir_agree, dir_usd, dir_z  (z with Kish effective n)"""
from __future__ import annotations

import numpy as np
import pandas as pd

from bursts import latest_burst

FOLLOW_S = 30
DIR_S = 10


def follower_table(other: pd.DataFrame, bt: pd.DataFrame, min_fills: int = 50) -> pd.DataFrame:
    o = other.copy()
    o["lag_same"] = latest_burst(o, bt, same=True)
    o["lag_opp"] = latest_burst(o, bt, same=False)
    win = lambda s: s.between(1, FOLLOW_S)  # noqa: E731
    o["fs"] = np.where(win(o["lag_same"]), o["usd"], 0.0)
    o["fo"] = np.where(win(o["lag_opp"]), o["usd"], 0.0)
    o["l0"] = np.where(o["lag_same"] == 0, o["usd"], 0.0)
    near = np.fmin(o["lag_same"], o["lag_opp"])
    o["du"] = np.where(near.between(1, DIR_S), o["usd"], 0.0)
    o["da"] = np.where(o["lag_same"] < o["lag_opp"].fillna(np.inf), o["du"], 0.0)
    o["du2"] = o["du"] ** 2
    g = o.groupby("wallet")
    t = pd.DataFrame({"fills": g.size(), "usd": g["usd"].sum(), "fs": g["fs"].sum(),
                      "fo": g["fo"].sum(), "l0": g["l0"].sum(), "pnl": g["pnl"].sum(),
                      "med_lag_same": g["lag_same"].median(), "dir_usd": g["du"].sum(),
                      "da": g["da"].sum(), "du2": g["du2"].sum()})
    t = t[t["fills"] >= min_fills]
    t["follow_same"] = t["fs"] / t["usd"]
    t["follow_opp"] = t["fo"] / t["usd"]
    t["co_move"] = t["l0"] / t["usd"]
    t["excess"] = t["follow_same"] - t["follow_opp"]
    t["dir_agree"] = t["da"] / t["dir_usd"].where(t["dir_usd"] > 0)
    n_eff = t["dir_usd"] ** 2 / t["du2"].where(t["du2"] > 0)
    t["dir_z"] = (t["dir_agree"] - 0.5) / np.sqrt(0.25 / n_eff)
    return t.drop(columns=["fs", "fo", "l0", "da", "du2"]).reset_index()


def follow_pnl_curve(other: pd.DataFrame, bt: pd.DataFrame) -> pd.DataFrame:
    """What entering after the bots earns: PnL/USD of all non-latency taker
    fills by seconds since the latest same-side burst."""
    lag = latest_burst(other, bt, same=True)
    bins = [-0.5, 0.5, 2.5, 5.5, 10.5, 30.5, 120.5, np.inf]
    lab = ["0", "1-2", "3-5", "6-10", "11-30", "31-120", ">120"]
    b = pd.cut(pd.Series(lag), bins, labels=lab)
    o = other.assign(bin=b.cat.add_categories("none").fillna("none").to_numpy())
    g = o.groupby("bin", observed=False)
    return pd.DataFrame({"fills": g.size(), "usd": g["usd"].sum(),
                         "pnl_per_usd": g["pnl"].sum() / g["usd"].sum()}).reset_index()
