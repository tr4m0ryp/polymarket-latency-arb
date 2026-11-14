"""Latency classes from the fingerprint columns.

    python3 research/classify.py     # re-label data/out/latency/wallets.csv

Shared spot-reaction gate (all must hold):
  taker_share >= 0.30 and n_taker_fills >= 100   it crosses the spread itself
  align3 >= 0.60 and align3_z >= 4               its taker side follows the BTC
                                                 move of the 3 s before the fill
  fresh_edge > 0                                 the newest 10 s of spot moved
                                                 fair value toward its side
  live_share >= 0.90                             trades while price can matter:
                                                 live window, or the 60 s TWAP
                                                 strike window before it (5m/15m)
Classes on top of the gate:
  latency_arb          directional <= 0.5 (trades both sides of one market as
                       spot ticks), coverage >= 0.5, fills_per_market >= 5,
                       mo2 > 0 (the book reprices toward it within 2 s)
  latency_arb_partial  directional <= 0.5, misses coverage / fills / mo2
  momentum_taker       directional > 0.5: one spot-triggered bet per market
  none                 fails the gate
Classes ignore PnL on purpose, so losing copies of the strategy stay in."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

GATE = {"taker_share": 0.30, "n_taker_fills": 100, "align3": 0.60, "align3_z": 4.0,
        "live_share": 0.90}
ARB = {"directional": 0.5, "coverage": 0.5, "fills_per_market": 5.0}


def classify(w: pd.DataFrame) -> pd.DataFrame:
    w = w.copy()
    w["live_share"] = w["in_window_share"] + w["strike_window_share"]
    gate = ((w["taker_share"] >= GATE["taker_share"])
            & (w["n_taker_fills"] >= GATE["n_taker_fills"])
            & (w["align3"] >= GATE["align3"]) & (w["align3_z"] >= GATE["align3_z"])
            & (w["fresh_edge"] > 0) & (w["live_share"] >= GATE["live_share"]))
    two_sided = w["directional"] <= ARB["directional"]
    full = ((w["coverage"] >= ARB["coverage"])
            & (w["fills_per_market"] >= ARB["fills_per_market"]) & (w["mo2"] > 0))
    w["latency_class"] = np.select(
        [gate & two_sided & full, gate & two_sided, gate],
        ["latency_arb", "latency_arb_partial", "momentum_taker"], "none")
    w["profitable"] = w["pnl"] > 0
    w["copy_fragile"] = w["copy_keep2"] < 0.5
    return w


def rollup(w: pd.DataFrame) -> pd.DataFrame:
    """One row per wallet that is latency_arb(_partial) in any family:
    PnL summed over all its BTC up/down families, and per class."""
    arb = w["latency_class"].str.startswith("latency_arb")
    keep = w.loc[arb, "wallet"].unique()
    x = w[w["wallet"].isin(keep)].copy()
    x["fam"] = x["series"].str.replace("btc-up-or-down-", "") + ":" + x["latency_class"]
    x["arb_pnl"] = np.where(x["latency_class"].str.startswith("latency_arb"), x["pnl"], 0.0)
    r = x.groupby("wallet").agg(btc_pnl=("pnl", "sum"), arb_pnl=("arb_pnl", "sum"),
                                volume_usd=("volume_usd", "sum"), markets=("n_markets", "sum"),
                                families=("fam", lambda v: ";".join(sorted(v))))
    r["roi"] = r["btc_pnl"] / r["volume_usd"]
    return r.sort_values("btc_pnl", ascending=False).reset_index()


def write(w: pd.DataFrame, out: Path) -> pd.DataFrame:
    w = w.sort_values(["latency_class", "pnl"], ascending=[True, False])
    w.to_csv(out / "wallets.csv", index=False, float_format="%.6g")
    rollup(w).to_csv(out / "wallet_rollup.csv", index=False, float_format="%.6g")
    return w


if __name__ == "__main__":
    out = Path(__file__).resolve().parents[1] / "data" / "out" / "latency"
    w = write(classify(pd.read_csv(out / "wallets.csv")), out)
    print(w.groupby(["series", "latency_class"]).size().to_string())
