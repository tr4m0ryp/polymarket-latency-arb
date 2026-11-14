"""Invention 1: perp-driven fair value with an explicit staleness term.

The book is treated as a delayed, partial filter of Binance. Each lag bucket of the perp (and
spot) move is converted to settlement z-units (move * zscale: how far it shifts the 60 s TWAP
z-score with the time and volatility left), the book's own recent repricing (bk*) says how much
is already in, and the level gap to the TWAP model says how far the book sits from spot. A ridge
regression on training hours learns how much of each is still to come in the next 3 s:

    fair = Phi( Phi^-1(our mid) + w . x )

so `w . x` is the pending repricing, i.e. the staleness of the book in z-units.
Invention 3 (`imb=True`): the perp's top-of-book queue imbalance, scaled as a 1 bp move,
predicts the next repricing before the perp mid moves (queue depletion precedes the tick)."""
from __future__ import annotations

import json

import numpy as np
import pandas as pd
from scipy.special import ndtr

from .features import BUCKETS, z

N = len(BUCKETS)


def design(df: pd.DataFrame, srcs=("perp", "smid"), extra=True, imb=False) -> np.ndarray:
    """srcs may include 'pmic' / 'smic' (microprice lag buckets, v2 feature tables)."""
    zs = df["zs"].to_numpy(dtype=float) * 1e-4
    cols = []
    if imb:
        q = np.nan_to_num(df["imb"].to_numpy(dtype=float))
        cols += [q * zs, np.sign(q) * (np.abs(q) > 0.8) * zs]
    for s in srcs:
        for k in range(N):
            cols.append(np.nan_to_num(df[f"{s}{k}"].to_numpy(dtype=float)) * zs)
    if extra:
        cols += [df[f"bk{k}"].to_numpy(dtype=float) for k in range(3)]
        cols.append(np.clip(np.nan_to_num(df["gap"].to_numpy(dtype=float)), -2, 2))
    return np.column_stack(cols)


class Fair:
    def __init__(self, srcs=("perp", "smid"), extra=True, lam=1.0, imb=False):
        self.srcs, self.extra, self.lam, self.imb, self.w = tuple(srcs), extra, lam, imb, None

    def fit(self, df: pd.DataFrame) -> "Fair":
        X, y = design(df, self.srcs, self.extra, self.imb), df["y"].to_numpy(dtype=float)
        ok = np.isfinite(y) & np.isfinite(X).all(1) & (df["mid"].between(0.05, 0.95)).to_numpy()
        X, y = X[ok], np.clip(y[ok], -1.5, 1.5)
        A = X.T @ X + self.lam * np.eye(X.shape[1])
        self.w = np.linalg.solve(A, X.T @ y)
        pred = X @ self.w
        self.r2 = float(1 - ((y - pred) ** 2).mean() / y.var())
        return self

    def dz(self, df: pd.DataFrame) -> np.ndarray:
        return design(df, self.srcs, self.extra, self.imb) @ self.w

    def p(self, df: pd.DataFrame) -> np.ndarray:
        return ndtr(z(df["mid"].to_numpy(dtype=float)) + self.dz(df))

    def save(self, path) -> None:
        path.write_text(json.dumps({"srcs": self.srcs, "extra": self.extra, "lam": self.lam,
                                    "imb": self.imb,
                                    "w": list(map(float, self.w)), "r2": self.r2}, indent=1))

    @classmethod
    def load(cls, path) -> "Fair":
        d = json.loads(path.read_text())
        f = cls(d["srcs"], d["extra"], d["lam"], d.get("imb", False))
        f.w, f.r2 = np.array(d["w"]), d["r2"]
        return f
