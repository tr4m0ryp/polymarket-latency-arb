"""Score wallets for skill that survives the price they paid.

Hit rate alone rewards buying favourites at 0.97. The test used here asks
whether a wallet's PnL beats what the market price already implied:
under the null "the price at each fill was the true probability", a
market's PnL Q*(R - pi) has mean 0 and variance Q^2 * pi(1-pi). Two
statistics are reported:
  z_dir     sum(pnl) / sqrt(sum(var)) over directional positions only;
            the outcome null is wrong for spread capture (Q ~ 0)
  t_event   t-stat of per-event PnL, model-free, robust to correlated
            brackets inside one event and valid for every style
t_event is recomputed on a chronological hold-out (A = older half of the
markets, B = newer) so that selection on A is confirmed on unseen B."""
from __future__ import annotations

import numpy as np
import pandas as pd

LAGS = (2, 10, 60)


def copy_prices(f: pd.DataFrame, lag: int) -> np.ndarray:
    """YES-frame price of the first fill in the same market >= lag seconds
    after each fill: what a follower reacting with that delay would pay.
    NaN when the market printed nothing afterwards."""
    out = np.full(len(f), np.nan)
    for _, idx in f.groupby("condition_id").indices.items():
        ts = f["ts"].to_numpy()[idx]
        pi = f["pi"].to_numpy()[idx]
        j = np.searchsorted(ts, ts + lag, side="left")
        ok = j < len(idx)
        out[idx[ok]] = pi[j[ok]]
    return out


def per_market(f: pd.DataFrame) -> pd.DataFrame:
    f = f.copy()
    f["aq"] = f["q"].abs()
    f["aq_pi"] = f["aq"] * f["pi"]
    f["usd_t"] = f["usd"] * f["t_rel"]
    f["usd_taker"] = f["usd"] * f["taker"]
    for lag in LAGS:
        cp = copy_prices(f, lag)
        f[f"cpnl{lag}"] = np.where(np.isnan(cp), 0.0, f["q"] * (f["R"] - cp))
    g = f.groupby(["wallet", "condition_id"], sort=False)
    m = g.agg(series=("series", "first"), event=("event", "first"), R=("R", "first"),
              end_ts=("end_ts", "first"), Q=("q", "sum"), gross=("aq", "sum"),
              aq_pi=("aq_pi", "sum"), pnl=("pnl", "sum"), usd=("usd", "sum"),
              usd_t=("usd_t", "sum"), usd_taker=("usd_taker", "sum"),
              first_t=("t_rel", "min"), first_secs_to_end=("secs_to_end", "max"),
              n_fills=("q", "size"),
              **{f"cpnl{lag}": (f"cpnl{lag}", "sum") for lag in LAGS}).reset_index()
    m["pibar"] = (m["aq_pi"] / m["gross"]).clip(0.005, 0.995)
    m["var"] = m["Q"] ** 2 * m["pibar"] * (1 - m["pibar"])
    m["directional"] = m["Q"].abs() / m["gross"]
    # price paid for the side finally held, and whether that side won
    m["paid"] = np.where(m["Q"] >= 0, m["pibar"], 1 - m["pibar"])
    m["hit"] = np.sign(m["Q"]) * (m["R"] - m["pibar"]) > 0
    return m


def t_event(m: pd.DataFrame) -> float:
    ev = m.groupby("event")["pnl"].sum()
    if len(ev) < 3:
        return np.nan
    sd = ev.std(ddof=1)
    return ev.mean() / (sd / np.sqrt(len(ev))) if sd > 0 else np.nan


def _wallet_stats(m: pd.DataFrame) -> pd.Series:
    ev = m.groupby("event")["pnl"].sum()
    d = m[m["directional"] >= 0.5]
    w = m["usd"].clip(lower=1e-9)
    return pd.Series({
        "n_markets": len(m), "n_events": len(ev), "volume_usd": m["usd"].sum(),
        "pnl": m["pnl"].sum(), "roi": m["pnl"].sum() / max(m["usd"].sum(), 1e-9),
        "z_dir": d["pnl"].sum() / np.sqrt(d["var"].sum()) if d["var"].sum() > 0 else np.nan,
        "t_event": t_event(m),
        "hit_rate": d["hit"].mean() if len(d) else np.nan,
        "avg_paid": np.average(d["paid"], weights=d["usd"].clip(lower=1e-9)) if len(d) else np.nan,
        "directional": np.average(m["directional"], weights=w),
        "taker_share": m["usd_taker"].sum() / max(m["usd"].sum(), 1e-9),
        "t_rel_usd": m["usd_t"].sum() / max(m["usd"].sum(), 1e-9),
        "first_t_med": m["first_t"].median(),
        "first_secs_to_end_med": m["first_secs_to_end"].median(),
        "fills_per_market": m["n_fills"].mean(),
        **{f"copy_keep{lag}": m[f"cpnl{lag}"].sum() / m["pnl"].sum() if m["pnl"].sum() > 0 else np.nan
           for lag in LAGS},
    })


def score(f: pd.DataFrame, min_markets: int = 10) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return (per-market positions, per wallet x series scores)."""
    m = per_market(f)
    cnt = m.groupby(["wallet", "series"])["condition_id"].transform("size")
    m = m[cnt >= min_markets]
    cut = m.groupby("series")["end_ts"].transform("median")
    m["half"] = np.where(m["end_ts"] <= cut, "A", "B")
    full = m.groupby(["wallet", "series"]).apply(_wallet_stats, include_groups=False)
    parts = []
    for h in ("A", "B"):
        s = m[m["half"] == h].groupby(["wallet", "series"]).apply(
            lambda x: pd.Series({"pnl": x["pnl"].sum(), "n": x["event"].nunique(),
                                 "t": t_event(x)}),
            include_groups=False)
        parts.append(s.add_suffix(f"_{h}"))
    out = full.join(parts[0]).join(parts[1]).reset_index()
    return m, out
