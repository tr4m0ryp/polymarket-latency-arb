"""Sealed-data and frozen-artifact guards for the evaluation harness.

The prereg2 test segment (5m markets starting >= SEALED = 2026-10-11 18:55 UTC through the
end of run 3) is sealed: no market list here is ever built by globbing a cache directory;
windows come from the earlier frozen runs' market files and train ids from markets.csv
filtered on start first. `SafeStore` cannot open an hour file starting at or after SEALED
nor a sealed market (the 18:00 hour is read for the 18:00-18:50 ext markets, filtered to
their own market index, as the frozen ext run did). The frozen value models are checked
against their pre-registered hashes before any simulation."""
from __future__ import annotations

import hashlib
import os

import numpy as np

from .... import predict
from ....strategy import CACHE as SCACHE, ROOT
from ....strategy.ingest.load import Store

SEALED = 1791744900          # 2026-10-11 18:55 UTC: prereg2 test segment starts here
MODELS_SHA16 = {"v1_L-40": "8b1fd3f3662c7648", "v1_L0": "570a9c1015c555c5",
                "v1_L50": "dc58889b5f201854"}


def assert_allowed(starts, what: str = "markets") -> None:
    """Every market start must be before SEALED (raises on any sealed or empty-start id)."""
    s = np.asarray(starts, dtype=float)
    if len(s):
        assert np.isfinite(s).all() and s.max() < SEALED, f"{what}: sealed market (start >= {SEALED})"


def check_env() -> None:
    """Refuse the paper bot's cache overrides (data/paper/ is off limits)."""
    for k in ("BTCLAT_PREDICT_CACHE", "BTCLAT_STRATEGY_CACHE", "BTCLAT_LIVE"):
        assert not os.environ.get(k), f"{k} is set: the harness reads research caches only"
    assert SCACHE == ROOT / "data" / "cache" / "strategy"
    assert predict.CACHE == ROOT / "data" / "cache" / "predict"


def model_sha16(name: str) -> str:
    p = predict.OUT / "models" / f"{name}.pkl"
    return hashlib.sha256(p.read_bytes()).hexdigest()[:16]


def check_models(names=("v1_L0", "v1_L-40")) -> dict:
    out = {n: model_sha16(n) for n in names}
    for n, h in out.items():
        assert h == MODELS_SHA16[n], f"frozen model {n} changed: {h} != {MODELS_SHA16[n]}"
    return out


class SafeStore(Store):
    """Store that cannot read an hour file starting at or after SEALED, nor a sealed market."""

    def __init__(self, keep: int = 4):
        super().__init__(keep)
        self.have = {h for h in self.have if h * 3600 < SEALED}
        ok = set(self.mk.loc[self.mk["start"] < SEALED, "slug"])     # drop sealed outcomes and gaps
        self.outcome = {k: v for k, v in self.outcome.items() if k in ok}
        self.gaps = {k: v for k, v in self.gaps.items() if k in ok}

    def market(self, i: int, pre: float = 420.0):
        start, end = float(self.mk.start[i]), float(self.mk.end[i])
        assert start < SEALED and end <= SEALED, f"market {i} is sealed"
        return super().market(i, pre)
