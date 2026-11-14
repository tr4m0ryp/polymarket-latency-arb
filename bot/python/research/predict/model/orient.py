"""Side-oriented features: one row per (decision, side), every directional feature signed so
that positive means "toward this side" (Up as is, Down mirrored). A single value model then
serves both sides and sees twice the data.

Mirroring for Down: signed Binance / book features flip sign; bid / ask kinds swap (queue
depletion, mid up / down intensities, time-to-depletion); the token price becomes 1 - mid and
the seen price the Down ask (1 - Up bid)."""
from __future__ import annotations

import numpy as np
import pandas as pd

SWAP = [("p_depb", "p_depa"), ("s_depb", "s_depa"), ("p_ttdb", "p_ttda"), ("s_ttdb", "s_ttda"),
        ("p_up0.4", "p_dn0.4"), ("p_up2", "p_dn2"), ("s_up0.4", "s_dn0.4"), ("s_up2", "s_dn2"),
        ("fair_edge_up", "fair_edge_dn")]
NEUTRAL = {"p_spr", "p_lq", "p_lam", "p_ttd_min", "p_tsm", "s_spr", "s_lq", "s_lam", "s_ttd_min",
           "s_tsm", "st_tn", "ft_tn", "pm_spr", "secs_left", "lzs", "sigma", "pm_tsc", "delta"}
SIDE_ONLY = {"pm_mid"}


def signed_cols(cols) -> list[str]:
    sw = {c for p in SWAP for c in p}
    return [c for c in cols if c not in NEUTRAL and c not in sw and c not in SIDE_ONLY]


def orient(df: pd.DataFrame, feats: list[str], side: int) -> pd.DataFrame:
    out = pd.DataFrame(index=df.index)
    sw = dict(SWAP + [(b, a) for a, b in SWAP])
    for c in feats:
        if c in NEUTRAL:
            out[c] = df[c]
        elif c in sw:
            out[c] = df[c] if side > 0 else df[sw[c]]
        elif c == "pm_mid":
            out["tok_mid"] = df[c] if side > 0 else 1 - df[c]
        else:
            out[c] = df[c] if side > 0 else -df[c]
    seen = df["pm_ba"] / 100 if side > 0 else 1 - df["pm_bb"] / 100
    out["seen"] = seen
    out["half_spread"] = seen - (df["pm_mid"] if side > 0 else 1 - df["pm_mid"])
    return out
