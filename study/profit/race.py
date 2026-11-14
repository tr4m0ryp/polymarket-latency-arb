"""Who gets to the stale quote first.

Taker fills of all latency wallets in a family are chained into bursts per
(market, direction): a burst continues while consecutive fills are <= GAP s
apart. A fill's lag is ts - burst start (block timestamps, ~2 s blocks).
  lead_share    share of the wallet's taker USD in the burst's first block
  med_lag       USD-weighted median lag in s
  burst_edge    gross PnL per USD by lag (0, 2-4, >4 s) - what being late costs"""
from __future__ import annotations

import numpy as np
import pandas as pd

GAP = 4


def lags(f: pd.DataFrame) -> pd.DataFrame:
    tk = f[f["taker"] == 1].copy()
    tk["dir"] = np.sign(tk["q"])
    tk = tk.sort_values(["condition_id", "dir", "ts"], kind="stable")
    new = (tk["condition_id"].ne(tk["condition_id"].shift())
           | tk["dir"].ne(tk["dir"].shift())
           | (tk["ts"].diff() > GAP))
    tk["burst"] = new.cumsum()
    tk["lag"] = tk["ts"] - tk.groupby("burst")["ts"].transform("min")
    return tk


def _wmed(x: pd.DataFrame) -> float:
    o = np.argsort(x["lag"].to_numpy())
    c = np.cumsum(x["usd"].to_numpy()[o])
    return float(x["lag"].to_numpy()[o][np.searchsorted(c, c[-1] / 2)])


def race(f: pd.DataFrame) -> pd.DataFrame:
    tk = lags(f)
    g = tk.groupby("wallet")
    u = g["usd"].sum()
    out = pd.DataFrame({"lead_share": tk[tk["lag"] == 0].groupby("wallet")["usd"].sum()
                        .reindex(u.index).fillna(0) / u,
                        "med_lag": g.apply(_wmed, include_groups=False)})
    for name, lo, hi in [("lag0", 0, 0), ("lag2_4", 1, 4), ("lag5p", 5, 1e9)]:
        x = tk[tk["lag"].between(lo, hi)].groupby("wallet")
        out[f"edge_{name}"] = x["pnl"].sum() / x["usd"].sum().clip(lower=1e-9)
        out[f"usd_{name}"] = x["usd"].sum().reindex(u.index).fillna(0) / u
    return out.reset_index()
