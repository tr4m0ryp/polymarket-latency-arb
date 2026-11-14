"""C4 race-clock taker: predict the stale maker's cancel during the 150 ms hold, not the price,
and set the order's size and walk from the depth predicted to survive to our match.

- depth.py  receipt-clock replay of the Polymarket level sizes (no venue stamps, no look-ahead):
            size at our seen ask / bid and the next worse level per decision row, plus the
            stale-level events (fair-value jumps) and whether their level survived to our match.
- clock.py  P_alive = sigmoid(b . [log q_seen, log pm_tsc, a_hat - 0.22, log pm60]) fitted once
            on run 2 train events (fold-invariant); a_hat = per-market EWMA of past outcomes.
- arms.py   harness candidates race_taker / race_veto (frozen firing, race-keyed size / limit).
- drive.py  one simulation pass of every variant on all allowed markets, fold choice and the
            per-variant tables the kill tests need (variants.py: the r1-r4 variant sets).
- build.py (depth cache), diag.py (train-market order anatomy), report.py / summary.py (tables).
Outputs: data/out/predict/improve/cand-race/ (clock.json, diag-train.md, r1-r4/, summary.md).

Sealed data: every market touched asserts start < SEALED (1791744900)."""
from __future__ import annotations

from pathlib import Path

import numpy as np

from .... import CACHE as PCACHE, OUT as POUT
from ...harness.guard import SEALED

NAME = "cand-race"
OUT = POUT / "improve" / NAME
CACHE = PCACHE / "improve" / NAME
LAG_RX = 0.016          # Polymarket stamp -> our receipt, median (grid.py)
MATCH = (0.150 + LAG_RX, 0.200 + LAG_RX)   # receipt-clock window of our L = 0 match (J 10-50 ms)
KNOWN = 0.27            # an event's outcome is usable from t_e + KNOWN on
PRIOR = 0.22            # prior survival rate of a stale level (memory EWMA start)
SPAN = 8                # EWMA span of the market memory


def assert_open(starts) -> None:
    s = np.atleast_1d(np.asarray(starts, float))
    assert len(s) == 0 or (np.isfinite(s).all() and s.max() < SEALED), "sealed market touched"


__all__ = ["OUT", "CACHE", "MATCH", "KNOWN", "PRIOR", "SPAN", "assert_open", "Path"]
