"""Per-event cause of the stale level's end and the per-bucket rows of the decile tables.

Clocks are relative to the Binance event time T0 (venue clocks). Our L = 0 order matches at
`match` = our perp feed lag + 150 ms. The stale level ends at `lag_q` (censored at 10 s):
- consumed: rival prints at or through the stale price before the end added up to >= 80% of
  the level's size at T0 (the level was eaten);
- cancel: any other end (the maker repriced, possibly after a partial hit);
- alive: still resting at our match.
Hazards are events per second of exposure (first stale-price print, maker end within 1 s)."""
from __future__ import annotations

import numpy as np
import pandas as pd

from .. import CENSOR, HOLD
from ..analyze.stats import boot_median, boot_ratio, fmt

EAT = 0.8


def prep(raw: pd.DataFrame) -> pd.DataFrame:
    d = raw[(raw["bb0"] > 0) & (raw["ba0"] < 100) & (raw["pm_silence"] < 2.0) & (raw["lag_pmfeed"] < 0.5)].copy()
    d["gone"] = d["lag_q"].fillna(np.inf)
    d["match"] = d["lag_feed"] + HOLD
    d["eaten"] = (d["snipe"] == 1) & (d["v_snipe"] >= EAT * d["size0"])
    by = d["gone"] <= d["match"]
    d["c_alive"] = (~by).astype(float)
    d["c_cancel"] = (by & ~d["eaten"]).astype(float)
    d["c_eaten"] = (by & d["eaten"]).astype(float)
    d["risk_tr"] = np.minimum(np.minimum(d["t_snipe"].fillna(np.inf), d["gone"]), CENSOR)
    d["risk_1s"] = np.minimum(d["gone"], 1.0)
    d["end_1s"] = ((d["gone"] <= 1.0) & ~d["eaten"]).astype(float)
    d["wave"] = (d["n_s0.2"] + d["n_s0.3"]) / 0.3          # prints toward s per s, 200-500 ms
    d["wave_bg"] = d["n_s-0.3"] / 0.3                       # same, the 300 ms before T0
    d["fast150"] = (d["gone"] < 0.150).astype(float)
    d["l_size"] = np.log1p(d["size0"])
    return d


def hz(g: pd.DataFrame, num: str, den: str):
    return boot_ratio(g, num, den)


def requote_row(g: pd.DataFrame) -> dict:
    lq, lm = boot_median(g, "lag_q"), boot_median(g, "lag_m")
    ch = hz(g, "end_1s", "risk_1s")
    return {"events": len(g), "mkts": g["m"].nunique(), "level size sh": f"{g['size0'].median():.0f}",
            "requote ms [CI]": fmt(lq[0], lq[1], lq[2], 0, 1000).replace("+", ""),
            "mid reprice ms": f"{1000 * g['lag_m'].median():.0f}",
            "P(< 150 ms)": f"{g['fast150'].mean():.2f}",
            "maker end hazard /s [CI]": fmt(ch[0], ch[1], ch[2], 2).replace("+", "")}


def race_row(g: pd.DataFrame, p: pd.DataFrame) -> dict:
    he, hp = hz(g, "snipe", "risk_tr"), hz(p, "snipe", "risk_tr")
    a = boot_ratio(g, "c_alive")
    return {"events": len(g), "alive at our match [CI]": fmt(a[0], a[1], a[2], 2).replace("+", ""),
            "cancelled": f"{g['c_cancel'].mean():.2f}", "eaten": f"{g['c_eaten'].mean():.2f}",
            "stale-price hazard /s": fmt(he[0], he[1], he[2], 2).replace("+", ""),
            "placebo /s": f"{hp[0]:.2f}", "excess /s": f"{he[0] - hp[0]:+.2f}",
            "wave 200-500ms /s": f"{g['wave'].mean():.1f}", "placebo wave /s": f"{p['wave'].mean():.1f}",
            "excess wave /s": f"{g['wave'].mean() - p['wave'].mean():+.1f}"}


def value_row(g: pd.DataFrame) -> dict:
    al, gn = g[g["c_alive"] == 1], g[g["c_alive"] == 0]
    v, va, vg = boot_ratio(g, "v0_1"), boot_ratio(al, "v0_1"), boot_ratio(gn, "v0_1")
    return {"events": len(g), "v seen 1s c": f"{100 * g['vseen_1'].mean():+.1f}",
            "v L0 1s c [CI]": fmt(v[0], v[1], v[2], 1, 100),
            "alive: v L0 c [CI]": fmt(va[0], va[1], va[2], 1, 100),
            "gone: v L0 c [CI]": fmt(vg[0], vg[1], vg[2], 1, 100),
            "alive: persist 1s": f"{al['per1'].median():.2f}", "gone: persist 1s": f"{gn['per1'].median():.2f}",
            "alive: v seen c": f"{100 * al['vseen_1'].mean():+.1f}", "gone: v seen c": f"{100 * gn['vseen_1'].mean():+.1f}"}
