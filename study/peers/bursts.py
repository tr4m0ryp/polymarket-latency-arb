"""Spot-reaction bursts: who fires first on the same market and side.

A burst is a run of latency-style taker fills on one (market, side) that
starts at the first such fill (t0) and spans BURST_S seconds after it. Each
wallet present in the burst gets its own first fill time, so
  lag      = first fill ts - t0           (0 = first mover or tied with it)
  gap_c    = 100 * d * (vwap_pi - p0)     cents paid above the first-mover
             price p0 (VWAP of all burst fills at t0); > 0 = worse price
Fill ts is the Polygon block timestamp (~2 s blocks), so lags come in
block-sized steps and same-block ties are common; ties are kept as ties."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from study.wallets import load_fills, load_markets  # noqa: E402

BURST_S = 5
PRE_OPEN_S = 60  # the 60 s strike-TWAP window before 5m/15m markets open


def taker_frame(slug: str) -> pd.DataFrame:
    mk = load_markets(slug)
    f = load_fills(slug, mk)
    start = f["condition_id"].map(mk["start_ts"]).astype(float)
    f = f[(f["taker"] == 1) & (f["ts"] >= start - PRE_OPEN_S) & (f["q"] != 0)]
    f = f.assign(d=np.sign(f["q"]).astype(int))
    return f[["wallet", "condition_id", "ts", "d", "q", "pi", "usd", "pnl", "tx"]]


def assign_bursts(g: pd.DataFrame) -> tuple[np.ndarray, pd.Index]:
    """Anchored windows per (market, side): a new burst opens at the first
    fill more than BURST_S s after the current burst's t0."""
    g = g.sort_values(["condition_id", "d", "ts"], kind="stable")
    key = (g["condition_id"].astype("category").cat.codes.to_numpy() * 2
           + (g["d"].to_numpy() > 0))
    ts = g["ts"].to_numpy()
    bid = np.empty(len(g), dtype=np.int64)
    b, t0, last = -1, -1e18, -1
    for i in range(len(g)):
        if key[i] != last or ts[i] - t0 > BURST_S:
            b += 1
            t0, last = ts[i], key[i]
        bid[i] = b
    return bid, g.index


def burst_table(lat: pd.DataFrame) -> pd.DataFrame:
    """Per (burst, wallet): first ts, lag, vwap, usd, pnl, price gap."""
    bid, idx = assign_bursts(lat)
    x = lat.loc[idx].assign(burst=bid)
    x["t0"] = x.groupby("burst")["ts"].transform("min")
    at0 = x[x["ts"] == x["t0"]]
    p0 = (at0["pi"] * at0["usd"]).groupby(at0["burst"]).sum() / at0.groupby("burst")["usd"].sum()
    x["piu"] = x["pi"] * x["usd"]
    w = x.groupby(["burst", "wallet"]).agg(
        condition_id=("condition_id", "first"), d=("d", "first"), t0=("t0", "first"),
        first_ts=("ts", "min"), usd=("usd", "sum"), piu=("piu", "sum"), pnl=("pnl", "sum"),
        n=("ts", "size")).reset_index()
    w["vwap"] = w["piu"] / w["usd"].where(w["usd"] > 0)
    w["lag"] = w["first_ts"] - w["t0"]
    w["p0"] = w["burst"].map(p0)
    w["gap_c"] = 100 * w["d"] * (w["vwap"] - w["p0"])
    w["n_wallets"] = w.groupby("burst")["wallet"].transform("size")
    w["rank"] = w.groupby("burst")["first_ts"].rank(method="min")
    return w.drop(columns="piu")


def latest_burst(other: pd.DataFrame, bursts: pd.DataFrame, same: bool) -> np.ndarray:
    """Seconds since the latest burst t0 on the same (or opposite) side of the
    same market, for each fill in `other` (NaN when none came before)."""
    b = bursts.drop_duplicates("burst")[["condition_id", "d", "t0"]].copy()
    if not same:
        b["d"] = -b["d"]
    b["key"] = b["condition_id"] + ":" + b["d"].astype(str)
    o = other.assign(key=other["condition_id"] + ":" + other["d"].astype(str),
                     _i=np.arange(len(other)))
    m = pd.merge_asof(o.sort_values("ts"), b.sort_values("t0")[["key", "t0"]],
                      left_on="ts", right_on="t0", by="key", direction="backward")
    m = m.sort_values("_i")
    return (m["ts"] - m["t0"]).to_numpy(dtype=float)
