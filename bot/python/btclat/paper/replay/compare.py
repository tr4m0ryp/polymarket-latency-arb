"""Column-by-column comparison of live rows with the offline table.

Diffs are reported in units of the column's offline standard deviation (`max_z`), so tiny
float noise and real disagreements read on one scale. Rows where the offline table reads
the Polymarket book one 5 ms grid step early are flagged and reported apart: at a decision
on a book change (q exactly on the grid), floor((q - t0) / DT + 1e-9) falls one step short
whenever float error in q - t0 (~2e-7 s at epoch scale) exceeds the 1e-9 guard, so the
offline row shows the book from before the change it was triggered by."""
from __future__ import annotations

import numpy as np
import pandas as pd

DT = 0.005
BOOK_COLS = ("pm_bb", "pm_ba", "pm_mid", "pm_spr", "bk0", "bk1", "bk2", "gap", "fair_p", "pm_stale")


def grid_quirk(q: np.ndarray, start: float) -> np.ndarray:
    """True where an offline book read at q or q - 0.2 / 1 / 3 s lands one grid row early."""
    t0 = float(start) - 2
    bad = np.zeros(len(q), bool)
    for a in (0.0, 0.2, 1.0, 3.0):
        x = (q - a - t0) / DT
        on_grid = np.abs(x - np.rint(x)) < 1e-3
        bad |= on_grid & (np.floor(x + 1e-9) != np.rint(x))
    return bad


def diffs(live: pd.DataFrame, off: dict, mask: np.ndarray) -> dict:
    out = {}
    for c in live.columns:
        if c == "t" or c not in off:
            continue
        a = live[c].to_numpy(float).astype(np.float32).astype(float)[mask]
        b = off[c][:len(live)].astype(float)[mask]
        nan_a, nan_b = np.isnan(a), np.isnan(b)
        d = np.where(nan_a & nan_b, 0.0, np.abs(a - b))
        d = np.where(nan_a ^ nan_b, np.inf, d)
        sd = np.nanstd(b[np.isfinite(b)]) if np.isfinite(b).any() else 1.0
        out[c] = (d, max(sd, 1e-12))
    return out


def compare(tabs: dict, rows: dict, starts: dict) -> tuple[pd.DataFrame, dict]:
    acc: dict = {}
    n_rows = n_quirk = 0
    for s, d in tabs.items():
        live = pd.DataFrame([r for r in rows[s] if r is not None])
        quirk = grid_quirk(d["t"][:len(live)], starts[s])
        n_rows += len(live)
        n_quirk += int(quirk.sum())
        for tag, mask in (("clean", ~quirk), ("quirk", quirk)):
            for c, (dd, sd) in diffs(live, d, mask).items():
                r = acc.setdefault((tag, c), {"n": 0, "max_abs": 0.0, "max_z": 0.0, "n_z_gt_1e-3": 0, "sd": sd})
                if len(dd):
                    r["n"] += len(dd)
                    r["max_abs"] = max(r["max_abs"], float(dd.max()))
                    r["max_z"] = max(r["max_z"], float(dd.max() / sd))
                    r["n_z_gt_1e-3"] += int((dd / sd > 1e-3).sum())
    df = pd.DataFrame([{"rows": k[0], "col": k[1], **v} for k, v in acc.items()])
    df["frac_z_gt_1e-3"] = df["n_z_gt_1e-3"] / df["n"].clip(lower=1)
    return df.sort_values(["rows", "max_z"], ascending=[True, False]), {"rows": n_rows, "quirk_rows": n_quirk}
