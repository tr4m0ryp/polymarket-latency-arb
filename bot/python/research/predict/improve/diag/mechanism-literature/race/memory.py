"""Maker-speed memory: does the stale level's fate on the previous Binance event of the same
market predict its fate on this one? Polymarket makers differ in speed (level size drives
requote time, Weller's fast vs slow liquidity), and the same makers quote a market for its
whole 5 minutes, so survival should persist across events if speed is a maker trait.

Pairs = consecutive events of one market <= 60 s apart (both observable before the second
event's decision: the first event's survival is known ~0.3 s after it). Market bootstrap."""
from __future__ import annotations

import numpy as np
import pandas as pd

from .selection import _boot


def pairs(ev: pd.DataFrame, gap: float = 60.0) -> pd.DataFrame:
    e = ev.sort_values(["m", "T0"]).copy()
    for c in ("c_alive", "lag_q", "T0", "size0", "side", "v0_1"):
        e[f"prev_{c}"] = e.groupby("m")[c].shift(1)
    e = e[(e["T0"] - e["prev_T0"] <= gap) & e["prev_c_alive"].notna()]
    e["same_side"] = (e["side"] == e["prev_side"]).astype(float)
    return e


def memory_table(ev: pd.DataFrame) -> pd.DataFrame:
    p = pairs(ev)
    rows = []
    for nm, g in (("all pairs", p), ("same side", p[p["same_side"] == 1]), ("opposite side", p[p["same_side"] == 0])):
        pa, al, ms = g["prev_c_alive"].to_numpy() == 1, g["c_alive"].to_numpy(), g["m"].to_numpy()
        v = 100 * g["v0_1"].to_numpy(float)
        fa = lambda ix: al[ix][pa[ix]].mean() - al[ix][~pa[ix]].mean()  # noqa: E731
        fv = lambda ix: np.nanmean(v[ix][pa[ix]]) - np.nanmean(v[ix][~pa[ix]])  # noqa: E731
        la, ha = _boot(ms, fa)
        lv, hv = _boot(ms, fv)
        lq = g[["lag_q", "prev_lag_q"]].clip(upper=10).dropna()
        rows.append({"pairs": nm, "n": len(g), "mkts": g["m"].nunique(),
                     "P(alive | prev alive)": round(al[pa].mean(), 2), "P(alive | prev gone)": round(al[~pa].mean(), 2),
                     "diff [CI]": f"{fa(np.arange(len(g))):+.2f} [{la:+.2f}, {ha:+.2f}]",
                     "our L0 1s c: prev alive - prev gone [CI]": f"{fv(np.arange(len(g))):+.1f} [{lv:+.1f}, {hv:+.1f}]",
                     "Spearman requote ms": round(lq.corr(method="spearman").iloc[0, 1], 2)})
    return pd.DataFrame(rows)


def memory_ols(ev: pd.DataFrame) -> pd.DataFrame:
    """alive on prev alive, log size now, log size prev, log perp msgs/s, log surprise (LPM)."""
    p = pairs(ev)
    d = p.assign(ls=np.log1p(p["size0"]), lsp=np.log1p(p["prev_size0"]), lm=np.log1p(p["pmsg10"]),
                 lsur=np.log(p["surprise"].clip(lower=1e-3)))
    xs = ["prev_c_alive", "ls", "lsp", "lm", "lsur", "same_side"]
    d = d[["m", "c_alive"] + xs].replace([np.inf, -np.inf], np.nan).dropna()
    X = np.column_stack([np.ones(len(d)), d[xs].to_numpy(float)])
    Y = d["c_alive"].to_numpy(float)
    beta = np.linalg.lstsq(X, Y, rcond=None)[0]
    lo, hi = _boot(d["m"].to_numpy(), lambda ix: np.linalg.lstsq(X[ix], Y[ix], rcond=None)[0], B=400)
    names = ["const", "prev alive", "log size now", "log size prev", "log perp msgs/s", "log surprise", "same side"]
    return pd.DataFrame({"x": names, "beta": beta.round(3), "lo": lo.round(3), "hi": hi.round(3)})
