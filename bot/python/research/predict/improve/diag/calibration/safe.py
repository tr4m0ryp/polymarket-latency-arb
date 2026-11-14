"""Sealed-data guard. Market lists come from earlier frozen runs' market files (select, dev3,
test3 run 1, ext) or, for train, from the run-2 split bounds; every list is asserted to end
before SEALED, and the store never opens an hour file starting at or after SEALED nor a
market that ends after it. No directory is ever globbed for market tables."""
from __future__ import annotations

import numpy as np
import pandas as pd

from ..... import predict
from .....strategy import CACHE as SCACHE
from .....strategy.ingest.load import Store
from . import SEALED

TAGS = {"select": "sel1", "dev3": "dev1", "final": "final", "ext": "ext"}


def market_ids(window: str) -> list[int]:
    if window == "train":
        mk = pd.read_csv(SCACHE / "markets.csv", usecols=["start"])
        mk = mk[(mk["start"] >= predict.RUN2) & (mk["start"] < predict.SPLIT)]
        ids = [int(i) for i in mk.index if (predict.CACHE / "tab" / f"{i}.npz").exists()]
        starts = mk.loc[ids, "start"]
    else:
        d = pd.read_csv(predict.OUT / f"markets-{TAGS[window]}.csv")
        ids, starts = [int(x) for x in d["m"]], d["start"]
    assert len(ids) and float(starts.max()) < SEALED, f"{window}: sealed market in list"
    return ids


def start_of(ids) -> np.ndarray:
    mk = pd.read_csv(SCACHE / "markets.csv", usecols=["start"])
    return mk["start"].to_numpy(float)[np.asarray(ids, dtype=np.int64)]


def check(starts) -> None:
    """Assert a set of market starts is entirely before the sealed segment."""
    assert float(pd.Series(starts).max()) < SEALED, "sealed market reached"


class SafeStore(Store):
    """Store that cannot read an hour file starting at or after SEALED, nor a sealed market."""

    def __init__(self, keep: int = 4):
        super().__init__(keep)
        self.have = {h for h in self.have if h * 3600 < SEALED}

    def market(self, i: int, pre: float = 420.0):
        start, end = float(self.mk.start[i]), float(self.mk.end[i])
        assert start < SEALED and end <= SEALED, f"market {i} is sealed"
        return super().market(i, pre)
