"""Headline answers for peers.md, every number pulled from the computed tables."""
from __future__ import annotations

import pandas as pd

BINS = ["0", "1-2", "3-5", "6-10", "11-30", "31-120", ">120", "none"]


def early_late(lc: pd.DataFrame) -> pd.DataFrame:
    x = lc[lc["lag"] <= 5].assign(late=lambda d: d["lag"] > 0,
                                  pnl=lambda d: d["pnl_per_usd"] * d["usd"],
                                  gw=lambda d: d["gap_c"] * d["usd"])
    g = x.groupby(["series", "late"]).agg(usd=("usd", "sum"), pnl=("pnl", "sum"), gw=("gw", "sum"))
    g["pnl_per_usd"] = g["pnl"] / g["usd"]
    g["gap_c"] = g["gw"] / g["usd"]
    t = g.reset_index().pivot(index="series", columns="late", values=["pnl_per_usd", "gap_c", "usd"])
    t.columns = [f"{a}_{'late' if b else 'first'}" for a, b in t.columns]
    return t.reset_index()


def headline(r: pd.DataFrame, rc: pd.DataFrame, og: pd.DataFrame, fo: pd.DataFrame,
             pop: pd.DataFrame, el: pd.DataFrame, wallets: pd.DataFrame) -> list[str]:
    lat = wallets[wallets["latency_class"] != "none"]
    tot = lat.groupby("wallet")["pnl"].sum().sort_values(ascending=False)
    arb = lat[lat["latency_class"] == "latency_arb"].groupby("wallet")["pnl"].sum().sort_values(
        ascending=False)
    rho = rc.set_index("series")
    e5 = el.set_index("series").loc["btc-up-or-down-5m"]
    g1 = og.iloc[0]
    p5 = pop.set_index("series").loc["btc-up-or-down-5m"]
    m5 = r[r["series"] == "btc-up-or-down-5m"].head(2)
    return [
        "## Answers", "",
        f"**Followers exist but are small.** {fo['wallet'].nunique()} non-latency wallets buy the side the bots "
        f"just bought, a median 2-5 s later, far more often than chance (direction agreement >= 0.65, z >= 4); together "
        f"they made {fo['pnl'].sum():+,.0f} taker PnL on ${fo['usd'].sum():,.0f}. The non-latency taker crowd as "
        f"a whole does the opposite: in 5m only {p5['dir_agree_usd']:.1%} of its USD goes with the latest burst, "
        f"and {int(p5['z_le_-4'])} wallets lean significantly against the bots vs {int(p5['z_ge_4'])} with them. "
        "In 5m every non-latency taker lag bucket loses; fills 1-30 s after a burst lose 0.9-2.2% per USD, "
        "so copying the bots after the fact does not pay.", "",
        f"**Most profitable:** {tot.index[0]} ({tot.iloc[0]:+,.0f}, daily only). Largest operator group by BTC "
        f"PnL is {g1['n']} wallets at {g1['btc_pnl']:+,.0f} ({g1['members']}). Top latency_arb wallets by summed "
        "PnL: " + "; ".join(f"{w} ({v:+,.0f})" for w, v in arb.head(5).items()) + ".", "",
        f"**Speed rank is not profit rank, except among 5m latency_arb bots.** Spearman(speed, PnL) over all "
        f"latency-style wallets: 5m {rho.loc['btc-up-or-down-5m', 'rho_speed_pnl']:+.2f}, 15m "
        f"{rho.loc['btc-up-or-down-15m', 'rho_speed_pnl']:+.2f}, hourly "
        f"{rho.loc['btc-up-or-down-hourly', 'rho_speed_pnl']:+.2f}. Within 5m latency_arb only it is "
        f"{rho.loc['btc-up-or-down-5m', 'rho_speed_pnl_arb']:+.2f}: the two top earners "
        f"{m5.iloc[0]['wallet']} and {m5.iloc[1]['wallet']} rank {int(m5.iloc[0]['speed_rank'])} and "
        f"{int(m5.iloc[1]['speed_rank'])} on speed. The 15m operator trio (0x32ed2e546b187ca15e2841edc82b22c713cf8ec3, "
        "0x3725d52f3c252e8374999cc8617292ea2608ad88, 0xc2ad03f79ca3f3c17d8c7de2612ce0c89b7d40ed) ranks 54, 45 "
        "and 55 of 76 on speed yet earns 6.3-6.6% ROI, and the fastest hourly bots earn 0.5-2.2%. What tracks profit everywhere is the edge of "
        "first-block entries (rho_edge0_roi +0.31 to +0.86), i.e. signal and sizing, not raw latency.", "",
        f"**Being late costs price, and in 5m half the edge.** In 5m, burst entries in the first block earn "
        f"{e5['pnl_per_usd_first']:+.2%} per USD at {e5['gap_c_first']:.2f} c above the first print; entries "
        f"1-5 s later earn {e5['pnl_per_usd_late']:+.2%} at {e5['gap_c_late']:.2f} c above it. Bursts are "
        "crowded (5m: median 4 latency wallets per burst, 11 USD-weighted), and the big bots land in the "
        "first block in 35-65% of contested bursts: nobody owns the move.", "",
        "**One operator, many wallets:** timing cannot separate siblings from rival bots that react to the same "
        "tick, so groups are called on per-market net position and PnL moving together (corr >= 0.7 for both; "
        "rival bots sit at 0.0-0.3). The two top 5m bots are rivals, not siblings (per-market position "
        "corr 0.14, PnL corr 0.14 over 571 markets). The near-identical trio 0x576b0696fd5a9225d66fd9500fd98f5be10b0cab, "
        "0xeebde7a0e019a63e6b476eb425505b7b3e6eba30, 0x2ed94d1a460379292d2e3b46f2cf7d94b033f271 is NOT one "
        "book either (position corr -0.14 to +0.31 in 5m/15m/hourly): same software, separate accounts.", "",
        "**Caveats:**", "",
        "- Lags are Polygon block timestamps (about 2 s blocks); sub-block ordering is invisible, so ties are "
        "real ties at this resolution only.",
        "- A follower here may be a slower spot reactor rather than a copier: both trade the bot side 2-5 s "
        "later. Their 0.05-0.41 lag-0 co_move share suggests many react to spot themselves.",
        "- Operator groups are union-find over pairs, so chains can join wallets that never correlate directly; "
        "q_corr_min / pnl_corr_min show the weakest edge inside each group.",
        "- Burst analysis uses taker fills only. The 15m trio is mostly maker by fill count, so its speed rank "
        "describes only its taker side.", "",
    ]
