"""A one-row stand-in for the pandas frames the research rules read, so the live bot calls
research/strategy/signals/rules.py `micro` and research/predict/sim/rules.py `vtaker`
unchanged: `frame["col"].to_numpy()` returns a length-1 float array and `len(frame)` is 1."""
from __future__ import annotations

import numpy as np


class Col(np.ndarray):
    def to_numpy(self, dtype=None):
        return np.asarray(self, dtype=dtype) if dtype is not None else np.asarray(self)


class Frame(dict):
    def __init__(self, row: dict):
        super().__init__({k: np.array([v], dtype=float).view(Col) for k, v in row.items()})

    def __len__(self) -> int:
        return 1
