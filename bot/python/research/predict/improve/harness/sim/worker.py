"""One market through the strategy replay simulator, every requested arm x L x variant.

Fill logic is the strategy simulator's, unchanged (research/strategy/sim/taker.py, maker.py;
same call as research/predict/sim/run.py). Variants: base = J 10 ms race window, full level
(the frozen runs); comp = J 50 ms, half of each level (final_comp, competition sensitivity).
Makers have no race window: only their base variant is simulated."""
from __future__ import annotations

import pandas as pd

from ....sim.fills import aggregate, score
from .....strategy.sim import maker, taker
from .....strategy.sim.grid import Book
from ..api import Market, check_decisions
from ..guard import SafeStore

HOLD = 0.150
VARIANTS = {"base": (0.010, 1.0), "comp": (0.050, 0.5)}

_CFG: dict = {}      # set by sim/pool.py before the fork: arms {key: Arm}, L, variants, threads
_ST = None


def _store() -> SafeStore:
    global _ST
    _ST = _ST or SafeStore()
    return _ST


def _fills(book, m: dict, arm, d: dict, L: int, J: float, cap: float) -> pd.DataFrame:
    if arm.kind == "maker":
        r = maker.run(book, m["tr"], d["t"], d["bid"], d["ask"], L / 1000, arm.size, arm.max_open, HOLD)
        f = pd.DataFrame(r, columns=["tf", "side", "shares", "px"]) if r else pd.DataFrame()
        if len(f):
            f["t"], f["cost"], f["fee"] = f["tf"], f["shares"] * f["px"], 0.0
        return f
    fills, _ = taker.run(book, d["t"], d["side"], d["shares"], d["limit"], L / 1000, J, cap, HOLD)
    return pd.DataFrame(fills) if fills else pd.DataFrame()


def simulate_market(task) -> tuple[int, pd.DataFrame, dict]:
    """task = (market id, arm keys). Returns (id, per arm x L x variant aggregates, activity)."""
    i, keys = task
    m = _store().market(i)
    meta = m["meta"]
    book = Book(m["ev"], meta["start"] - 2, meta["end"] + 2, m["gaps"])
    o = float(m["outcome"])
    mk = Market(i, meta)
    out = []
    for key in keys:
        arm = _CFG["arms"][key]
        for L in _CFG["L"]:
            d = arm.decide(mk, L)
            if d is None or not check_decisions(d, arm.kind):
                continue
            for var in _CFG["variants"]:
                if arm.kind == "maker" and var != "base":
                    continue
                f = _fills(book, m, arm, d, L, *VARIANTS[var])
                if not len(f):
                    continue
                f["arm"], f["L"], f["m"], f["end"] = key, L, i, meta["end"]
                a = aggregate(score(f, book, o))
                a["var"] = var
                out.append(a)
    agg = pd.concat(out, ignore_index=True) if out else pd.DataFrame()
    return i, agg, mk.activity()


def init_worker() -> None:
    from threadpoolctl import threadpool_limits
    threadpool_limits(limits=_CFG.get("threads", 1))
