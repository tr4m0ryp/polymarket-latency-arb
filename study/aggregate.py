"""Per wallet x family fingerprint columns from the per-fill frame.

USD-weighted throughout. Spot alignment is measured on TAKER fills only: a
latency bot crosses the spread right after spot moves, while a maker's fills
are chosen by whoever hits it.
  align{k}     share of taker USD whose side agrees with the BTC move over
               the k s before the fill (fills with a zero move excluded)
  align_post   the same against the 10 s AFTER the fill (no edge expected)
  fresh_edge   sum q*(fair - fair_stale) / USD over taker fills: how much of
               the fill rides the newest 10 s of spot
  model_edge   sum q*(fair - pi) / USD over taker fills: spot-implied
               value of the fill at the price paid
  mo{L}        markout per USD traded (all fills)"""
from __future__ import annotations

import numpy as np
import pandas as pd

from features import LOOKBACKS, MO_LAGS


def _w(x: pd.DataFrame, ret: str) -> float:
    s = np.sign(x[ret].to_numpy())
    q = np.sign(x["q"].to_numpy())
    m = (s != 0) & ~np.isnan(x[ret].to_numpy())
    u = x["usd"].to_numpy()[m]
    return float((u * (q[m] == s[m])).sum() / u.sum()) if u.sum() > 0 else np.nan


def _z(x: pd.DataFrame, ret: str, a: float) -> float:
    """z of a USD-weighted share against 0.5, with Kish effective n."""
    u = x.loc[(np.sign(x[ret]) != 0) & x[ret].notna(), "usd"].to_numpy()
    if u.sum() <= 0 or np.isnan(a):
        return np.nan
    n_eff = u.sum() ** 2 / (u ** 2).sum()
    return float((a - 0.5) / (0.5 / np.sqrt(n_eff)))


def _stats(x: pd.DataFrame, n_family: int, spot: bool) -> pd.Series:
    usd = x["usd"].sum()
    mk = x.groupby("condition_id").agg(pnl=("pnl", "sum"), Q=("q", "sum"),
                                       g=("q", lambda v: v.abs().sum()),
                                       first_t=("t_rel", "min"))
    tk = x[x["taker"] == 1]
    tu = tk["usd"].sum()
    hours = pd.to_datetime(x["ts"], unit="s").dt.floor("h").nunique()
    span_h = (x["ts"].max() - x["ts"].min()) / 3600 + 1
    out = {
        "n_markets": len(mk), "coverage": len(mk) / n_family, "n_fills": len(x),
        "fills_per_market": len(x) / len(mk), "volume_usd": usd,
        "med_fill_usd": x["usd"].median(),
        "pnl": x["pnl"].sum(), "roi": x["pnl"].sum() / max(usd, 1e-9),
        "win_rate_mkts": float((mk["pnl"] > 0).mean()),
        "n_taker_fills": len(tk), "taker_share": tu / max(usd, 1e-9),
        "in_window_share": x.loc[(x["t_rel"] >= 0) & (x["t_rel"] <= 1), "usd"].sum() / max(usd, 1e-9),
        "strike_window_share": x.loc[(x["ts"] >= x["start_ts"] - 60)
                                     & (x["ts"] < x["start_ts"]), "usd"].sum() / max(usd, 1e-9),
        "t_rel_usd": (x["usd"] * x["t_rel"]).sum() / max(usd, 1e-9),
        "first_t_med": mk["first_t"].median(),
        "directional": float((mk["Q"].abs() / mk["g"].clip(lower=1e-9)).mean()),
        "active_hour_share": hours / max(span_h, 1),
        **{f"mo{lag}": x[f"mo{lag}"].sum() / max(usd, 1e-9) for lag in MO_LAGS},
    }
    if spot:
        for k in LOOKBACKS:
            out[f"align{k}"] = _w(tk, f"r{k}")
        out["align3_z"] = _z(tk, "r3", out["align3"])
        out["align_post"] = _w(tk, "rf10")
        ok = tk["fair"].notna()
        tq, tuu = tk.loc[ok, "q"], max(tk.loc[ok, "usd"].sum(), 1e-9)
        out["fresh_edge"] = float((tq * (tk.loc[ok, "fair"] - tk.loc[ok, "fair_stale"])).sum() / tuu)
        out["model_edge"] = float((tq * (tk.loc[ok, "fair"] - tk.loc[ok, "pi"])).sum() / tuu)
    return pd.Series(out)


def wallet_table(f: pd.DataFrame, n_family: int, min_markets: int = 10,
                 spot: bool = True) -> pd.DataFrame:
    cnt = f.groupby("wallet")["condition_id"].nunique()
    keep = cnt[cnt >= min_markets].index
    g = f[f["wallet"].isin(keep)].groupby("wallet", sort=False)
    t = g.apply(lambda x: _stats(x, n_family, spot), include_groups=False)
    t.insert(0, "series", f["series"].iloc[0])
    return t.reset_index()
