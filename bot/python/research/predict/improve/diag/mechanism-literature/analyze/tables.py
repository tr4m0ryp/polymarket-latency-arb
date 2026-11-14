"""Per-bucket tables of the event study: venue response, rival takers, our post-hold value,
Binance persistence and feed lags, by an activity index (deciles) or by window."""
from __future__ import annotations

import numpy as np
import pandas as pd

from .stats import boot_median, boot_ratio, fmt


def clean(ev: pd.DataFrame) -> pd.DataFrame:
    ev = ev[(ev["bb0"] > 0) & (ev["ba0"] < 100) & (ev["pm_silence"] < 2.0) & (ev["lag_pmfeed"] < 0.5)].copy()
    ev["beat0"] = (ev["lag_q"].fillna(99) > ev["lag_feed"] + 0.150).astype(float)   # quote still there at our L=0 match
    ev["fast150"] = (ev["lag_q"].fillna(99) < 0.150).astype(float)                  # requoted inside one hold
    ev["front"] = ev["vseen_1"] - ev["v0_1"]
    ev["rival_early"] = (ev["n_s0.1"] + ev["n_s0.2"]) - (ev["n_o0.1"] + ev["n_o0.2"])  # 100-300 ms
    ev["rival_late"] = (ev["n_s0.3"] + ev["n_s0.5"]) - (ev["n_o0.3"] + ev["n_o0.5"])   # 300 ms-1 s
    ev["pre_flow"] = ev["n_s-0.3"] - ev["n_o-0.3"]
    ev["cancel"] = ((ev["snipe"] == 0) & ev["lag_q"].notna()).astype(float)
    ev["cont10"] = (ev["per10"] >= ev["per0.15"]).astype(float)
    ev["abs_c0"] = ev["c0"].abs()
    return ev


def row(g: pd.DataFrame) -> dict:
    lq = boot_median(g, "lag_q")
    lf = boot_median(g, "lag_feed")
    v0 = boot_ratio(g, "v0_1")
    v10 = boot_ratio(g, "v0_10")
    sn = boot_ratio(g, "snipe")
    bt = boot_ratio(g, "beat0")
    pt = boot_ratio(g, "pass3", "imp3")
    return {
        "events": len(g), "mkts": g["m"].nunique(),
        "|c0| c": f"{g['abs_c0'].median():.1f}",
        "spread c": f"{g['spr0'].mean():.2f}",
        "feed lag ms": fmt(lf[0], lf[1], lf[2], 0, 1000).replace("+", ""),
        "feed p90 ms": f"{1000 * g['lag_feed'].quantile(0.9):.0f}",
        "requote ms": fmt(lq[0], lq[1], lq[2], 0, 1000).replace("+", ""),
        "P(<150ms)": f"{g['fast150'].mean():.2f}",
        "P(quote alive at our match)": fmt(bt[0], bt[1], bt[2], 2).replace("+", ""),
        "ended by trade": fmt(sn[0], sn[1], sn[2], 2).replace("+", ""),
        "rival prints 100-300ms": f"{g['rival_early'].mean():+.2f}",
        "rival prints 0.3-1s": f"{g['rival_late'].mean():+.2f}",
        "pre-flow": f"{g['pre_flow'].mean():+.2f}",
        "v seen 1s c": f"{100 * g['vseen_1'].mean():+.1f}",
        "v L0 1s c": fmt(v0[0], v0[1], v0[2], 1, 100),
        "v L0 10s c": fmt(v10[0], v10[1], v10[2], 1, 100),
        "slip L0 c": f"{g['slip0'].mean():+.1f}",
        "persist 1s": f"{g['per1'].median():.2f}",
        "persist 10s": f"{g['per10'].median():.2f}",
        "pass-through 3s": fmt(pt[0], pt[1], pt[2], 2).replace("+", ""),
    }


def by(ev: pd.DataFrame, key: str, labels=None) -> pd.DataFrame:
    rows = []
    for k, g in ev.groupby(key, sort=True):
        r = {key: labels[k] if labels is not None else k}
        r.update(row(g))
        rows.append(r)
    return pd.DataFrame(rows)


def edges(ev: pd.DataFrame, col: str, b: pd.Series) -> list[str]:
    return [f"{ev.loc[b == k, col].min():.3g}-{ev.loc[b == k, col].max():.3g}" for k in sorted(b.unique())]


def spearman(ev: pd.DataFrame, ys, xs) -> pd.DataFrame:
    out = {x: [ev[[x, y]].dropna().corr(method="spearman").iloc[0, 1] for y in ys] for x in xs}
    return pd.DataFrame(out, index=ys).round(3)


def ols(ev: pd.DataFrame, y: str, xs: list[str], B: int = 300, seed: int = 3) -> pd.DataFrame:
    """OLS with standardized regressors; CI from a market bootstrap."""
    d = ev[["m", y] + xs].replace([np.inf, -np.inf], np.nan).dropna()
    X = (d[xs] - d[xs].mean()) / d[xs].std()
    X = np.column_stack([np.ones(len(d)), X.to_numpy()])
    Y = d[y].to_numpy(float)
    beta = np.linalg.lstsq(X, Y, rcond=None)[0]
    ms = d["m"].to_numpy()
    groups = [np.flatnonzero(ms == m) for m in np.unique(ms)]
    rng, bs = np.random.default_rng(seed), []
    for _ in range(B):
        idx = np.concatenate([groups[j] for j in rng.integers(0, len(groups), len(groups))])
        bs.append(np.linalg.lstsq(X[idx], Y[idx], rcond=None)[0])
    bs = np.array(bs)
    return pd.DataFrame({"beta": beta, "lo": np.percentile(bs, 2.5, 0), "hi": np.percentile(bs, 97.5, 0)},
                        index=["const"] + xs)


def split(ev: pd.DataFrame, key: str, flag: pd.Series, names=("feed ok", "feed lagged")) -> pd.DataFrame:
    """Post-hold value and quote survival per `key` bucket, split by a boolean state."""
    rows = []
    for k, g in ev.groupby(key, sort=True):
        r = {key: k}
        for nm, sub in ((names[0], g[~flag.loc[g.index]]), (names[1], g[flag.loc[g.index]])):
            v = boot_ratio(sub, "v0_1") if len(sub) > 10 else (np.nan,) * 3
            r[f"{nm} n"] = len(sub)
            r[f"{nm} v L0 1s c"] = fmt(v[0], v[1], v[2], 1, 100)
            r[f"{nm} v seen 1s c"] = f"{100 * sub['vseen_1'].mean():+.1f}" if len(sub) else "n/a"
            r[f"{nm} alive"] = f"{sub['beat0'].mean():.2f}" if len(sub) else "n/a"
        rows.append(r)
    return pd.DataFrame(rows)
