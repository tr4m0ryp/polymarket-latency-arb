"""Allowed evaluation windows and the two-fold window cross-validation.

Windows reuse the exact market lists of the earlier frozen runs, so the baselines reproduce
the report: select = run 2 after 10-10 10:00 (`sel1`, 144), dev3 = run 3 before 10-11 08:00
(`dev1`, 120), test3r1 = test run 1 08:00-14:50 starts (`final`, 83), ext = 14:55-18:50
starts (`ext`, 48). train = run 2 before 10-10 10:00 (models fit here), never evaluated.

Fold A: choose on {select, dev3}, evaluate on {test3r1, ext}.
Fold B: choose on {test3r1, ext}, evaluate on {select, dev3}."""
from __future__ import annotations

from functools import lru_cache

import pandas as pd

from ... import OUT, RUN2, SPLIT
from ....strategy import CACHE as SCACHE
from ...model.data import TAB
from .guard import SEALED, assert_allowed

WINDOWS = {"select": "sel1", "dev3": "dev1", "test3r1": "final", "ext": "ext"}
FOLDS = {"A": (("select", "dev3"), ("test3r1", "ext")),
         "B": (("test3r1", "ext"), ("select", "dev3"))}
BUSY15 = (1791730800, 1791734400)   # 2026-10-11 15:00-16:00 UTC starts: the report's busiest hour


@lru_cache(maxsize=None)
def _window(w: str) -> tuple[tuple[int, ...], tuple[float, ...]]:
    d = pd.read_csv(OUT / f"markets-{WINDOWS[w]}.csv").sort_values("m")
    assert_allowed(d["start"], w)
    return tuple(int(x) for x in d["m"]), tuple(float(x) for x in d["start"])


def ids(w: str) -> list[int]:
    """Sorted market ids of an allowed window (train included)."""
    if w == "train":
        return train_ids()
    return list(_window(w)[0])


def starts(w: str) -> dict[int, float]:
    if w == "train":
        mk = _markets()
        return {i: float(mk.start[i]) for i in train_ids()}
    i, s = _window(w)
    return dict(zip(i, s))


@lru_cache(maxsize=1)
def _markets() -> pd.DataFrame:
    return pd.read_csv(SCACHE / "markets.csv", usecols=["start", "end"])


@lru_cache(maxsize=1)
def train_ids_t() -> tuple[int, ...]:
    """Run 2 markets before the select split that have a decision table (checked per id)."""
    mk = _markets()
    sel = mk.index[(mk["start"] >= RUN2) & (mk["start"] < SPLIT)]
    out = tuple(int(i) for i in sel if (TAB / f"{int(i)}.npz").exists())
    assert_allowed(mk.start[list(out)], "train")
    return out


def train_ids() -> list[int]:
    return list(train_ids_t())


def all_eval_ids() -> list[int]:
    out = sorted({i for w in WINDOWS for i in ids(w)})
    assert len(out) == sum(len(ids(w)) for w in WINDOWS), "windows overlap"
    return out


def window_of(i: int) -> str:
    for w in WINDOWS:
        if i in starts(w):
            return w
    raise KeyError(i)


assert SEALED > SPLIT
