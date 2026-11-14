"""Derived tables for the peers report, all computed from the peers_*.csv files."""
from __future__ import annotations

import numpy as np
import pandas as pd

from ops import groups
from speed import duel

OP_Q, OP_PNL = 0.7, 0.7          # operator edge: positions and PnL co-move
FOL_Z, FOL_AGREE, FOL_USD = 4.0, 0.65, 1000.0


def rank_table(speed: pd.DataFrame, pairs: pd.DataFrame, min_contested: int = 100) -> pd.DataFrame:
    s = speed[speed["contested"] >= min_contested].merge(duel(pairs), on=["series", "wallet"],
                                                        how="left")
    s["roi"] = s["pnl"] / s["volume_usd"]
    g = s.groupby("series")
    s["pnl_rank"] = g["pnl"].rank(ascending=False, method="min").astype(int)
    s["speed_rank"] = g["duel"].rank(ascending=False, method="min")
    return s.sort_values(["series", "pnl_rank"])


def rank_corr(r: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for fam, x in r.dropna(subset=["duel"]).groupby("series"):
        sp = lambda a, b: x[a].rank().corr(x[b].rank())  # noqa: E731
        arb = x[x["latency_class"].str.startswith("latency_arb")]
        rows.append({"series": fam, "wallets": len(x),
                     "rho_speed_pnl": sp("duel", "pnl"), "rho_speed_roi": sp("duel", "roi"),
                     "rho_first_pnl": sp("first_share", "pnl"),
                     "rho_edge0_roi": sp("edge_l0", "roi"),
                     "arb_wallets": len(arb),
                     "rho_speed_pnl_arb": arb["duel"].rank().corr(arb["pnl"].rank())
                     if len(arb) >= 4 else np.nan})
    return pd.DataFrame(rows)


def operator_groups(opcorr: pd.DataFrame, wallets: pd.DataFrame) -> pd.DataFrame:
    e = opcorr[(opcorr["q_corr"] >= OP_Q) & (opcorr["pnl_corr"] >= OP_PNL)]
    gid = groups(e)
    btc = wallets.groupby("wallet")["pnl"].sum()
    rows = []
    for g, members in pd.Series(gid).groupby(pd.Series(gid)):
        m = sorted(members.index, key=lambda w: -btc.get(w, 0))
        ee = e[e["a"].isin(m) | e["b"].isin(m)]
        rows.append({"group": g, "n": len(m), "btc_pnl": float(btc.reindex(m).sum()),
                     "families": ",".join(sorted(ee["series"].str.replace("btc-up-or-down-", "").unique())),
                     "q_corr_min": ee["q_corr"].min(), "pnl_corr_min": ee["pnl_corr"].min(),
                     "members": "; ".join(f"{w} ({btc.get(w, 0):+,.0f})" for w in m)})
    return pd.DataFrame(rows).sort_values("btc_pnl", ascending=False)


def followers(fo: pd.DataFrame) -> pd.DataFrame:
    return fo[(fo["dir_z"] >= FOL_Z) & (fo["dir_agree"] >= FOL_AGREE)
              & (fo["dir_usd"] >= FOL_USD)].sort_values("pnl", ascending=False)


def population(fo: pd.DataFrame) -> pd.DataFrame:
    g = fo.groupby("series")
    return pd.DataFrame({
        "wallets": g.size(),
        "dir_agree_usd": g.apply(lambda x: (x["dir_agree"] * x["dir_usd"]).sum()
                                 / x["dir_usd"].sum(), include_groups=False),
        "z_ge_4": g.apply(lambda x: int((x["dir_z"] >= 4).sum()), include_groups=False),
        "z_le_-4": g.apply(lambda x: int((x["dir_z"] <= -4).sum()), include_groups=False),
    }).reset_index()
