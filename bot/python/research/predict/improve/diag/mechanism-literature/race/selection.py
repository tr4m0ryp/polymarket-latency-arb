"""The hold as a last look: what does a stale quote's survival to our match say about the move?

If makers who leave a stale quote are merely slow, survivors carry MORE value (the move was
big and nobody pulled). If they leave it because they judge the move to be noise, survivors
carry LESS value at the very price we saw (adverse selection by the 150 ms hold, Cartea-
Jaimungal-Walton's last look applied to the whole venue). Measured by perp msgs/s tercile
(calm D1-3, mid D4-7, busy D8-10), with level size held fixed in an OLS. Market bootstrap."""
from __future__ import annotations

import numpy as np
import pandas as pd

GROUPS = {0: "calm D1-3", 1: "mid D4-7", 2: "busy D8-10"}


def groups(ev: pd.DataFrame, col: str = "pmsg10") -> pd.Series:
    q = np.quantile(ev[col].dropna(), [0.3, 0.7])
    return pd.Series(np.where(ev[col] <= q[0], 0, np.where(ev[col] > q[1], 2, 1)), index=ev.index)


def _boot(ms, fn, B=600, seed=13):
    um = np.unique(ms)
    idx = [np.flatnonzero(ms == m) for m in um]
    rng = np.random.default_rng(seed)
    bs = np.array([fn(np.concatenate([idx[j] for j in rng.integers(0, len(um), len(um))])) for _ in range(B)])
    return np.nanpercentile(bs, 2.5, 0), np.nanpercentile(bs, 97.5, 0)


def survival_table(ev: pd.DataFrame) -> pd.DataFrame:
    g = groups(ev)
    rows = []
    for k, nm in GROUPS.items():
        e = ev[g == k]
        al, ms = e["c_alive"].to_numpy() == 1, e["m"].to_numpy()
        gone = e["gone"].to_numpy()
        cols = {}
        for y in ("vseen_1", "vseen_10", "v0_1"):
            v = 100 * e[y].to_numpy(float)
            f = lambda ix, v=v: np.nanmean(v[ix][al[ix]]) - np.nanmean(v[ix][~al[ix]])  # noqa: E731
            lo, hi = _boot(ms, f)
            cols[y] = (f(np.arange(len(e))), lo, hi)
        cont = (e["per1"] >= 1).to_numpy(float)
        fc = lambda ix: cont[ix][al[ix]].mean() - cont[ix][~al[ix]].mean()  # noqa: E731
        lo, hi = _boot(ms, fc)
        rows.append({"state": nm, "events": len(e), "alive": round(al.mean(), 2),
                     "ends < 150 ms": round((gone < 0.15).mean(), 2),
                     "150-300 ms": round(((gone >= 0.15) & (gone < 0.3)).mean(), 2),
                     "0.3-1 s": round(((gone >= 0.3) & (gone < 1)).mean(), 2), "> 1 s": round((gone >= 1).mean(), 2),
                     "alive - gone: v at seen price 1s c [CI]": "%+.1f [%+.1f, %+.1f]" % cols["vseen_1"],
                     "same, 10s c [CI]": "%+.1f [%+.1f, %+.1f]" % cols["vseen_10"],
                     "alive - gone: our L0 1s c [CI]": "%+.1f [%+.1f, %+.1f]" % cols["v0_1"],
                     "alive - gone: P(perp move held 1s) [CI]": f"{fc(np.arange(len(e))):+.2f} [{lo:+.2f}, {hi:+.2f}]"})
    return pd.DataFrame(rows)


def selection_ols(ev: pd.DataFrame) -> pd.DataFrame:
    """vseen_1 (c) on alive, busy, alive x busy, log level size, log surprise, spread (calm and
    busy terciles only); the alive x busy term is the regime flip of the hold's selection."""
    g = groups(ev)
    d = ev[g != 1].assign(busy=(g[g != 1] == 2).astype(float))
    d = d.assign(y=100 * d["vseen_1"], ab=d["c_alive"] * d["busy"], ls=np.log1p(d["size0"]),
                 lsur=np.log(d["surprise"].clip(lower=1e-3)))
    xs = ["c_alive", "busy", "ab", "ls", "lsur", "spr0"]
    d = d[["m", "y"] + xs].replace([np.inf, -np.inf], np.nan).dropna()
    X = np.column_stack([np.ones(len(d)), d[xs].to_numpy(float)])
    Y = d["y"].to_numpy(float)
    beta = np.linalg.lstsq(X, Y, rcond=None)[0]
    lo, hi = _boot(d["m"].to_numpy(), lambda ix: np.linalg.lstsq(X[ix], Y[ix], rcond=None)[0], B=400)
    names = ["const", "alive", "busy", "alive x busy", "log level size", "log surprise", "spread c"]
    return pd.DataFrame({"x": names, "beta c": beta.round(2), "lo": lo.round(2), "hi": hi.round(2)})
