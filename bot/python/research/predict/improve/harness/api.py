"""Plug-in interface: what a candidate implements and what its decision function may read.

A candidate is a callable `candidate(fold: Fold) -> Arm | list[Arm]` (or predict sim arm spec
dicts, converted by `from_spec`). One Arm = one fixed decision rule; several = variants the
harness chooses between on the fold's choose windows. An Arm's `decide(mk, L)` sees one
market at a time on our receipt clock and returns the orders it would send:

    taker: {"t": receipt times (sorted), "side": +1 Up / -1 Down, "shares", "limit": price 0-1}
    maker: {"t": decision times (sorted), "bid": Up-frame tick (0 = none), "ask": tick (0 = none)}

The harness then runs the strategy replay simulator unchanged (150 ms hold, venue stamps,
survival-window competition) at each L. `Market.tab` drops every target (y_*), outcome path
(x_*) and outcome column, so a decision cannot read the future through it."""
from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from typing import Callable

import numpy as np
import pandas as pd

from ... import CACHE
from ...model.data import TAB
from ...model.store import load_model, predict_sides
from ....strategy.eval.prep import FEAT2
from .guard import model_sha16

LOOKAHEAD = ("y_", "x_")
PRED = CACHE / "improve" / "harness" / "pred"   # saved-model predictions per market (by model hash)
_MODELS: dict[str, dict] = {}


@dataclass
class Arm:
    name: str
    decide: Callable[["Market", int], dict | None]
    kind: str = "taker"          # "taker" | "maker"
    size: float = 60.0           # maker quote size (shares)
    max_open: float = 300.0      # maker open-inventory cap (shares)
    ref: str | None = None       # set only on the frozen arms: reuse the frozen-reference results


def frozen_model(name: str) -> dict:
    """A saved value model by full name (e.g. "v1_L0"), loaded once per process."""
    if name not in _MODELS:
        _MODELS[name] = load_model(name)
    return _MODELS[name]


@lru_cache(maxsize=None)
def _sha(name: str) -> str:
    return model_sha16(name)


def saved_pred(i: int, name: str, tab: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    """predict_sides of a saved model on market i, memoised on disk (keyed by the model hash)."""
    p = PRED / f"{name}_{_sha(name)}" / f"{i}.npz"
    st = (TAB / f"{i}.npz").stat()
    sig = np.array([st.st_size, st.st_mtime_ns, len(tab)], dtype=np.int64)
    if p.exists():
        with np.load(p) as z:
            if "sig" in z.files and np.array_equal(z["sig"], sig):
                return z["up"], z["dn"]
    up, dn = predict_sides(tab, frozen_model(name))
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_name(f"{i}.{os.getpid()}.tmp.npz")
    np.savez(tmp, up=up, dn=dn, sig=sig)
    os.replace(tmp, p)
    return up, dn


class Market:
    """One allowed market as a decision function may see it (lazy, cached per market)."""

    def __init__(self, i: int, meta: dict):
        self.id, self.meta = i, meta
        self.start, self.end = float(meta["start"]), float(meta["end"])
        self._tab, self._f2, self._pred = None, False, {}

    @property
    def tab(self) -> pd.DataFrame:
        """Decision table (feats/run.py rows: receipt-clock features, pm_bb/pm_ba/pm_mid seen,
        fair_p, zs), targets and outcome stripped. Treat as read-only."""
        if self._tab is None:
            with np.load(TAB / f"{self.id}.npz") as z:
                keep = [k for k in z.files if not k.startswith(LOOKAHEAD) and k != "outcome"]
                self._tab = pd.DataFrame({k: z[k] for k in keep})
        return self._tab

    @property
    def f2(self) -> pd.DataFrame | None:
        """Strategy v2 (microprice) feature table, the input of micf / their rule; None if absent."""
        if self._f2 is False:
            p = FEAT2 / f"{self.id}.pkl"
            self._f2 = pd.read_pickle(p) if p.exists() else None
        return self._f2

    def pred(self, model, L: int | None = None) -> tuple[np.ndarray, np.ndarray]:
        """Per-share value predictions (Up, Down) for every tab row. `model` is a saved model
        name ("v1" -> "v1_L{L}" when L is given, or a full name) or a model dict
        {"model", "vf"} fitted by the candidate."""
        if isinstance(model, str):
            key = f"{model}_L{L}" if L is not None and "_L" not in model else model
            if key not in self._pred:
                self._pred[key] = saved_pred(self.id, key, self.tab)
        else:
            key = ("obj", id(model))
            if key not in self._pred:
                self._pred[key] = predict_sides(self.tab, model)
        return self._pred[key]

    def activity(self) -> dict:
        """Label-free activity of the market: decision rows and leaders'-trigger-sized perp
        microprice moves (|p_dmic0.1| >= 0.002 bp), the report's busy-hour signature."""
        d = self.tab
        trig = int((np.abs(d["p_dmic0.1"].to_numpy(float)) >= 0.002).sum()) if "p_dmic0.1" in d else 0
        return {"m": self.id, "start": self.start, "n_tab": len(d), "n_trig": trig}


def check_decisions(d: dict, kind: str) -> int:
    """Validate a decision dict; returns its length."""
    keys = ("t", "side", "shares", "limit") if kind == "taker" else ("t", "bid", "ask")
    miss = [k for k in keys if k not in d]
    assert not miss, f"decision dict lacks {miss}"
    n = len(d["t"])
    assert all(len(d[k]) == n for k in keys), "decision arrays differ in length"
    if n:
        t = np.asarray(d["t"], float)
        assert (np.diff(t) >= 0).all(), "decision times must be sorted"
        if kind == "taker":
            s = np.asarray(d["side"])
            assert np.isin(s, (-1, 1)).all(), "side must be +1 / -1"
            lim = np.asarray(d["limit"], float)
            assert ((lim > 0) & (lim < 1)).all(), "limit must be a price in (0, 1)"
    return n
