"""The fold a candidate is built for: which windows it may choose and train on.

`Fold.load_rows` is the only training-data path the harness offers: run 2 train plus the
fold's choose windows, never its evaluate windows, never a sealed market. Calling it marks
the fold as used, so the harness keys that fold's arms per fold (no result reuse across
folds for a retrained candidate)."""
from __future__ import annotations

import numpy as np
import pandas as pd

from ...model.data import TAB
from . import windows as W
from .guard import assert_allowed


class Fold:
    def __init__(self, name: str):
        self.name = name
        self.choose, self.evaluate = W.FOLDS[name]
        self.train_windows = ("train",) + tuple(self.choose)
        self.touched = False

    def __repr__(self) -> str:
        return f"Fold({self.name}: choose {self.choose}, evaluate {self.evaluate})"

    def markets(self, w: str) -> list[int]:
        """Market ids of a window the candidate may train or choose on."""
        assert w in self.train_windows, f"fold {self.name}: window {w} is an evaluate window"
        self.touched = True
        return W.ids(w)

    def load_rows(self, windows=None, cols=None, frac: float = 1.0, seed: int = 0) -> pd.DataFrame:
        """Decision-table rows (targets y_*/x_* included: this is training data) of allowed
        windows, default train + choose; column `m` = market id (the same frame as
        model.data.load, so model.stack.stacked applies; window of a market: windows.window_of)."""
        windows = self.train_windows if windows is None else tuple(windows)
        rng = np.random.default_rng(seed)
        parts = []
        for w in windows:
            for i in self.markets(w):
                with np.load(TAB / f"{i}.npz") as z:
                    keys = z.files if cols is None else [c for c in cols if c in z.files]
                    d = {k: z[k] for k in keys}
                n = len(next(iter(d.values())))
                keep = rng.random(n) < frac if frac < 1 else np.ones(n, bool)
                df = pd.DataFrame({k: v[keep] for k, v in d.items()})
                df["m"] = i
                parts.append(df)
        out = pd.concat(parts, ignore_index=True)
        assert_allowed(pd.Series(out["m"].unique()).map(W._markets().start), "training rows")
        return out
