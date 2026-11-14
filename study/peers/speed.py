"""Per-wallet speed and price quality inside contested bursts.

Contested = at least 2 latency-style wallets fired in the burst.
  first_share     share of contested bursts where the wallet's first fill is
                  in the first block (lag 0, ties included)
  solo_first      share where it is alone in the first block
  med_lag/mean_lag  seconds behind the burst's first mover
  gap_c           USD-weighted cents paid above the first-mover price
  edge_l0/edge_late  PnL per USD of its burst entries at lag 0 vs lag > 0"""
from __future__ import annotations

import numpy as np
import pandas as pd


def _wavg(v: pd.Series, w: pd.Series) -> float:
    ok = v.notna() & (w > 0)
    return float(np.average(v[ok], weights=w[ok])) if ok.any() else np.nan


def wallet_speed(bt: pd.DataFrame, min_contested: int = 30) -> pd.DataFrame:
    c = bt[bt["n_wallets"] >= 2].copy()
    first_n = c[c["lag"] == 0].groupby("burst").size()
    c["solo"] = (c["lag"] == 0) & (c["burst"].map(first_n) == 1)
    rows = []
    for w, g in c.groupby("wallet"):
        if len(g) < min_contested:
            continue
        l0, late = g[g["lag"] == 0], g[g["lag"] > 0]
        rows.append({
            "wallet": w, "bursts": int((bt["wallet"] == w).sum()), "contested": len(g),
            "first_share": float((g["lag"] == 0).mean()), "solo_first": float(g["solo"].mean()),
            "med_lag": float(g["lag"].median()), "mean_lag": float(g["lag"].mean()),
            "gap_c": _wavg(g["gap_c"], g["usd"]),
            "gap_c_late": _wavg(late["gap_c"], late["usd"]),
            "burst_usd": float(g["usd"].sum()),
            "edge_l0": float(l0["pnl"].sum() / l0["usd"].sum()) if l0["usd"].sum() > 0 else np.nan,
            "edge_late": float(late["pnl"].sum() / late["usd"].sum()) if late["usd"].sum() > 0 else np.nan,
        })
    return pd.DataFrame(rows)


def lag_curve(bt: pd.DataFrame) -> pd.DataFrame:
    """Edge of a burst entry as a function of how late it came."""
    c = bt[bt["n_wallets"] >= 2]
    g = c.groupby("lag")
    return pd.DataFrame({"entries": g.size(), "usd": g["usd"].sum(),
                         "pnl_per_usd": g["pnl"].sum() / g["usd"].sum(),
                         "gap_c": g.apply(lambda x: _wavg(x["gap_c"], x["usd"]),
                                          include_groups=False)}).reset_index()


def pair_order(bt: pd.DataFrame, wallets: list[str], min_co: int = 50) -> pd.DataFrame:
    """Head-to-head: in bursts both entered, who was earlier, and do their
    burst sizes co-move (one operator splitting an order sizes together)."""
    x = bt[bt["wallet"].isin(wallets)]
    lag = x.pivot_table(index="burst", columns="wallet", values="lag", aggfunc="first")
    usd = x.pivot_table(index="burst", columns="wallet", values="usd", aggfunc="first")
    rows = []
    cols = list(lag.columns)
    for i, a in enumerate(cols):
        for b in cols[i + 1:]:
            m = lag[a].notna() & lag[b].notna()
            n = int(m.sum())
            if n < min_co:
                continue
            la, lb = lag.loc[m, a], lag.loc[m, b]
            ua, ub = np.log(usd.loc[m, a].clip(lower=0.01)), np.log(usd.loc[m, b].clip(lower=0.01))
            sd = min(ua.std(), ub.std())
            rows.append({"a": a, "b": b, "co_bursts": n,
                         "a_first": float((la < lb).mean()), "tie": float((la == lb).mean()),
                         "b_first": float((la > lb).mean()),
                         "size_sd": float(sd), "size_corr": float(np.corrcoef(ua, ub)[0, 1]) if sd > 0 else np.nan})
    return pd.DataFrame(rows)


def duel(pairs: pd.DataFrame) -> pd.DataFrame:
    """Net head-to-head speed per wallet and family: over all opponents,
    (bursts where it was strictly earlier - strictly later) / co-bursts."""
    a = pairs[["series", "a", "co_bursts", "a_first", "b_first"]].set_axis(
        ["series", "wallet", "n", "win", "loss"], axis=1)
    b = pairs[["series", "b", "co_bursts", "b_first", "a_first"]].set_axis(
        ["series", "wallet", "n", "win", "loss"], axis=1)
    d = pd.concat([a, b])
    d["net"] = (d["win"] - d["loss"]) * d["n"]
    t = d.groupby(["series", "wallet"]).agg(net=("net", "sum"), duel_n=("n", "sum"))
    t["duel"] = t["net"] / t["duel_n"]
    return t.drop(columns="net").reset_index()
