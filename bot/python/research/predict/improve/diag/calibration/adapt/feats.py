"""Adaptive-gain inputs: Binance book and trade signals divided by their trailing 60 s scale
(ctx columns), computed on the un-oriented decision table; the scales are side-symmetric, so
dividing commutes with orientation (signed columns flip, swap pairs swap, as model/orient).

Per source (perp p: rate bn60, tick rate pch60, vol rv60; spot s: sp60, sch60, srv60):
  dmic{w} / dmid{w}  -> _z  : move / (vol * sqrt(w))                   (signed)
  ofi{tau}           -> _z  : / sqrt(rate * tau + 1)                    (signed)
  depb / depa        -> _r  : / (rate * 0.1 + 1)                        (swap pair)
  ttdb / ttda        -> _r  : + log(rate + 1), log messages to depletion (swap pair)
  ttd_min            -> _r  : + log(rate + 1)                           (neutral)
  lam                -> _r  : - log1p(rate), burst ratio                (neutral)
  up/dn 0.4, 2       -> _r  : / (tick rate * tau + 0.1)                 (swap pairs)
  tsm                -> _r  : + log(tick rate + 0.01)                   (neutral)
spot trades: st_sv{k} -> _z : / sqrt(trades/s * k + 1) (signed); st_tn -> _r : - log1p(trades/s).
CTX: log activity scales as plain inputs (variant ctx)."""
from __future__ import annotations

import numpy as np
import pandas as pd

SRC = {"p": ("bn60", "pch60", "rv60"), "s": ("sp60", "sch60", "srv60")}
DMIC_W, DMID_W, OFI_T = (0.025, 0.05, 0.1, 0.25, 1.0), (0.1, 1.0, 5.0), (0.025, 0.1, 0.4, 1.6)
CTX = ["c_bn60", "c_sp60", "c_rv60", "c_srv60", "c_pmtr60", "c_pm60", "c_pmtop10", "c_pch60", "c_sch60"]
SWAP = [(f"{p}_{a}_r", f"{p}_{b}_r") for p in "ps" for a, b in
        (("depb", "depa"), ("ttdb", "ttda"), ("up0.4", "dn0.4"), ("up2", "dn2"))]
NEUTRAL = {f"{p}_{k}_r" for p in "ps" for k in ("ttd_min", "lam", "tsm")} | {"st_tn_r"} | set(CTX)


def raw_replaced() -> set[str]:
    """Raw columns the agc variant drops (their normalised copies replace them)."""
    out = set()
    for p in "ps":
        out |= {f"{p}_dmic{w:g}" for w in DMIC_W} | {f"{p}_dmid{w:g}" for w in DMID_W}
        out |= {f"{p}_ofi{k:g}" for k in OFI_T}
        out |= {f"{p}_{k}" for k in ("depb", "depa", "ttdb", "ttda", "ttd_min", "lam", "up0.4", "dn0.4",
                                     "up2", "dn2", "tsm")}
    return out | {f"st_sv{k:g}" for k in (0.05, 0.2, 1.0)} | {"st_tn"}


def add_gain(df: pd.DataFrame, c: dict) -> list[str]:
    """Adds the normalised columns to df in place; returns their names."""
    new = {}
    for p, (r, tk, v) in SRC.items():
        R, C = np.asarray(c[r], float), np.asarray(c[tk], float)
        V = np.maximum(np.asarray(c[v], float), 0.01)
        for w in DMIC_W:
            new[f"{p}_dmic{w:g}_z"] = df[f"{p}_dmic{w:g}"].to_numpy(float) / (V * np.sqrt(w))
        for w in DMID_W:
            new[f"{p}_dmid{w:g}_z"] = df[f"{p}_dmid{w:g}"].to_numpy(float) / (V * np.sqrt(w))
        for k in OFI_T:
            new[f"{p}_ofi{k:g}_z"] = df[f"{p}_ofi{k:g}"].to_numpy(float) / np.sqrt(R * k + 1)
        for k in ("depb", "depa"):
            new[f"{p}_{k}_r"] = df[f"{p}_{k}"].to_numpy(float) / (R * 0.1 + 1)
        for k in ("ttdb", "ttda", "ttd_min"):
            new[f"{p}_{k}_r"] = df[f"{p}_{k}"].to_numpy(float) + np.log(R + 1)
        new[f"{p}_lam_r"] = df[f"{p}_lam"].to_numpy(float) - np.log1p(R)
        for k, tau in (("up0.4", 0.4), ("dn0.4", 0.4), ("up2", 2.0), ("dn2", 2.0)):
            new[f"{p}_{k}_r"] = df[f"{p}_{k}"].to_numpy(float) / (C * tau + 0.1)
        new[f"{p}_tsm_r"] = df[f"{p}_tsm"].to_numpy(float) + np.log(C + 0.01)
    n = np.asarray(c["stn60"], float)
    for k in (0.05, 0.2, 1.0):
        if f"st_sv{k:g}" in df:
            new[f"st_sv{k:g}_z"] = df[f"st_sv{k:g}"].to_numpy(float) / np.sqrt(n * k + 1)
    if "st_tn" in df:
        new["st_tn_r"] = df["st_tn"].to_numpy(float) - np.log1p(n)
    for k in CTX:
        x = np.asarray(c[k[2:]], float)
        new[k] = np.log1p(x * (100 if k in ("c_rv60", "c_srv60") else 1))
    for k, x in new.items():
        df[k] = x.astype(np.float32)
    return list(new)


def orient_gain(df: pd.DataFrame, cols: list[str], side: int) -> pd.DataFrame:
    sw = dict(SWAP + [(b, a) for a, b in SWAP])
    out = {}
    for k in cols:
        if k in NEUTRAL:
            out[k] = df[k].to_numpy()
        elif k in sw:
            out[k] = df[k if side > 0 else sw[k]].to_numpy()
        else:
            out[k] = df[k].to_numpy() * (1 if side > 0 else -1)
    return pd.DataFrame(out, index=df.index)


def feature_set(variant: str, vf_v1: list[str], gain: list[str]) -> list[str]:
    base = variant
    if variant.startswith(("ds", "q25")):
        base = variant.split("_", 1)[1] if "_" in variant else "v1r"
    gain_only = [g for g in gain if g not in CTX]
    if base == "v1r":
        return list(vf_v1)
    if base == "ctx":
        return list(vf_v1) + CTX
    if base == "agc_add":
        return list(vf_v1) + gain_only
    if base == "agc":
        drop = raw_replaced()
        return [c for c in vf_v1 if c not in drop] + gain_only
    raise ValueError(variant)
