"""Why the perp queue-imbalance taker lost held out (strategy invention 3, "lost a
comparison"): decompose the value of buying the side the perp queue leans to into the book
move it predicts, the half spread, the hold slippage and the taker fee.

    python3 -m research.predict.model.diag_imb [--seg select] [--L 0]

Per-share cents, gated like the strategy takers (price 0.05-0.95, >= 20 s left)."""
from __future__ import annotations

import argparse

import numpy as np
import pandas as pd

from .. import OUT
from ...strategy import fee
from ..report.md import md
from .data import load


def decompose(df: pd.DataFrame, side: np.ndarray, L: int) -> dict:
    up = side > 0
    mid0 = df["pm_mid"].to_numpy(float)
    seen = np.where(up, df["pm_ba"] / 100, 1 - df["pm_bb"] / 100)
    paid = np.where(up, df[f"x_ba{L}"] / 100, 1 - df[f"x_bb{L}"] / 100)
    sm = lambda x: np.where(up, x, 1 - x)  # noqa: E731
    out = {"n": len(df)}
    for k in (1, 3, 10):
        out[f"move{k}s_c"] = 100 * np.nanmean(sm(df[f"x_m{k}_{L}"].to_numpy(float)) - sm(mid0))
    out["half_spread_c"] = 100 * np.nanmean(seen - sm(mid0))
    out["hold_slip_c"] = 100 * np.nanmean(paid - seen)
    out["fee_c"] = 100 * np.nanmean(fee(paid))
    v = sm(df[f"x_m10_{L}"].to_numpy(float)) - paid - fee(paid)
    out["net10_c"] = 100 * np.nanmean(v)
    out["net10_c_per_usd"] = 100 * np.nanmean(v) / np.nanmean(paid)
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seg", default="select")
    ap.add_argument("--L", type=int, default=0)
    a = ap.parse_args()
    df = load(a.seg, frac=0.5, seed=3)
    L = a.L
    ok = df["pm_mid"].between(0.05, 0.95) & (df["secs_left"] >= 20)
    ok &= (df[f"x_ba{L}"] < 100) & (df[f"x_bb{L}"] > 0) & (df[f"x_bad{L}"] == 0)
    df = df[ok]
    rows = []
    imb = df["p_imb"].to_numpy(float)
    for lo, hi in ((0.0, 0.4), (0.4, 0.8), (0.8, 0.95), (0.95, 1.01)):
        w = (np.abs(imb) >= lo) & (np.abs(imb) < hi)
        rows.append({"rule": f"|perp imb| {lo}-{min(hi, 1)}", **decompose(df[w], np.sign(imb[w]), L)})
    mic = (df["p_dmic0.1"] + df["s_dmic0.1"]).to_numpy(float)
    w = np.abs(df["p_dmic0.1"].to_numpy(float)) >= 0.002
    rows.append({"rule": "leaders' trigger (micro 0.1 s >= 0.002 bp)", **decompose(df[w], np.sign(mic[w]), L)})
    w2 = w & (np.abs(imb) > 0.8) & (np.sign(imb) == np.sign(mic))
    rows.append({"rule": "trigger + imb agrees > 0.8", **decompose(df[w2], np.sign(mic[w2]), L)})
    w3 = (np.abs(imb) > 0.8) & (df["p_spr"] == 1).to_numpy() & (np.abs(df["p_dmic0.1"]) < 1e-4).to_numpy()
    rows.append({"rule": "|imb| > 0.8, no recent micro move", **decompose(df[w3], np.sign(imb[w3]), L)})
    out = pd.DataFrame(rows)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"diag_imb_{a.seg}_L{L}.md").write_text(md(out, 2))
    print(md(out, 2))


if __name__ == "__main__":
    main()
