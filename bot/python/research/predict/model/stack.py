"""Gated, side-stacked frames for the value models: one row per (decision, side) with
oriented features and the per-share taker value at each L (model/derive.py)."""
from __future__ import annotations

import numpy as np
import pandas as pd

from .. import L_MS
from .data import features
from .derive import add_derived, side_values
from .orient import orient


def gate(df: pd.DataFrame) -> pd.Series:
    """Strategy-style gates: token price 0.05-0.95, >= 20 s left, a two-sided book."""
    return (df["pm_mid"].between(0.05, 0.95) & (df["secs_left"] >= 20)
            & (df["pm_bb"] > 0) & (df["pm_ba"] < 100))


def stacked(df: pd.DataFrame, perp_trades: bool = False, ks=(1, 3, 10)) -> tuple[pd.DataFrame, list[str]]:
    df = add_derived(df[gate(df)].copy())
    feats = features(df, perp_trades)
    parts = []
    for side in (1, -1):
        o = orient(df, feats, side)
        extra = {"side": np.full(len(df), side), "m": df["m"].to_numpy(), "t": df["t"].to_numpy(),
                 "row": np.arange(len(df))}
        for L in L_MS:
            for k in ks:
                up, dn = side_values(df, L, k)
                extra[f"v{k}_{L}"] = up if side > 0 else dn
            extra[f"bad{L}"] = df[f"x_bad{L}"].to_numpy()
            mid_tm = (df[f"x_ba{L}"].to_numpy(float) + df[f"x_bb{L}"].to_numpy(float)) / 200
            post = df[f"x_m1_{L}"].to_numpy(float) - mid_tm
            extra[f"post1_{L}"] = post if side > 0 else -post
        o = pd.concat([o, pd.DataFrame(extra, index=o.index)], axis=1)
        parts.append(o)
    out = pd.concat(parts, ignore_index=True)
    vf = [c for c in parts[0].columns if c not in ("side", "m", "t", "row") and not c.startswith(("v3_", "v10_", "v1_", "bad", "post1_"))]
    return out, vf
