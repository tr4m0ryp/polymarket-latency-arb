"""Load the label files into one frame (+ the feature matrix) and the rule helpers shared by
training and scoring."""
from __future__ import annotations

import numpy as np
import pandas as pd

from .. import SPLIT
from . import LAB

EXTRA = ("x_dep0", "x_dep2", "x_dep5", "x_ddep0.25", "x_ddep1.0", "x_age", "x_rlag")
REFR = 0.2


def load() -> tuple[pd.DataFrame, np.ndarray]:
    cols, Xs = [], []
    for p in sorted(LAB.glob("*.npz"), key=lambda p: int(p.stem)):
        with np.load(p) as z:
            if int(z["n"]) == 0:
                continue
            Xs.append(z["X"])
            cols.append(pd.DataFrame({k: z[k] for k in z.files if k not in ("X", "n")}))
    d = pd.concat(cols, ignore_index=True)
    d["test"] = d["t"] >= SPLIT
    return d, np.concatenate(Xs)


def v1_pred(d: pd.DataFrame) -> np.ndarray:
    """v1's value on the trigger side, -inf where v1 prefers the other side (the arm's rule)."""
    e = np.where(d["side"] > 0, d["pu"], d["pd"])
    o = np.where(d["side"] > 0, d["pd"], d["pu"])
    return np.where(e >= o, e, -np.inf)


def design(name: str, X: np.ndarray, d: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    """(model input, rows the model decides on) for a variant name.
    A/B: v1 features (+x: the book extras), every trigger row.
    S (stacked): v1 features + v1's trigger-side value (+x), rows where v1 value >= 0.
    G (gate): same inputs as S, rows v1 already keeps (value >= 2 c)."""
    parts = [X]
    v1 = v1_pred(d)
    if name[0] in "SG":
        parts.append(np.where(np.isfinite(v1), v1, -0.2)[:, None].astype(np.float32))
    if name.endswith("+x"):
        parts.append(d[list(EXTRA)].to_numpy(np.float32))
    region = np.ones(len(d), bool) if name[0] in "AB" else (v1 >= (0.0 if name[0] == "S" else 0.02))
    return (np.hstack(parts) if len(parts) > 1 else X), region


def refractory(d: pd.DataFrame, send: np.ndarray) -> np.ndarray:
    """Per market, keep a sent row only if >= 0.2 s after the last kept one."""
    keep = np.zeros(len(d), bool)
    t, m = d["t"].to_numpy(), d["m"].to_numpy()
    last_m, last_t = -1, -np.inf
    for i in np.flatnonzero(send):     # rows are in market, then time order
        if m[i] != last_m:
            last_m, last_t = m[i], -np.inf
        if t[i] - last_t >= REFR:
            keep[i], last_t = True, t[i]
    return keep


class Product:
    """P(survive at i = 0) x E[value | filled]: two regressors behind one predict()."""

    def __init__(self, ps, vf):
        self.ps, self.vf = ps, vf

    def predict(self, X):
        return np.clip(self.ps.predict(X), 0, 1) * self.vf.predict(X)
