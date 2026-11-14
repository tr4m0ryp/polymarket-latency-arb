"""Counterfactual limits for every sent order, replayed at its own match instant.

Match instant M = ack - 14 ms (our 36 fills sit at send + 246 ms median on the venue clock and
are acknowledged 14 ms later). At M the order sweeps the replayed asks up to its limit (FAK,
partial fills allowed); 10 s markout uses the replayed mid at M + 10 s, after the taker fee
0.07 p (1 - p) per share. `edge` rows scale the limit with the model's predicted edge."""
from __future__ import annotations

import numpy as np
import pandas as pd

from .replay import Replay, best, sweep

ACK_AFTER_MATCH = 0.014
KS = range(0, 11)
FS = (0.3, 0.5, 0.7, 1.0)


def _fee(p):
    return 0.07 * p * (1 - p)


def _mid(r: Replay, t: float):
    bb, ba = best(*r.at(t))
    return None if bb is None or ba is None else (bb + ba) / 2


def _depth(asks, limit):
    return sum(s for p, s in asks.items() if p <= limit + 1e-9)


def one(o, ev) -> list[dict]:
    """Rows (rule, filled, px, mk10_c, pnl) for one order; ev is its token's stream."""
    M = o.t_ack - ACK_AFTER_MATCH
    r = Replay(ev)
    _, a_send = r.at(o.t_send)
    a_send = dict(a_send)
    bb_s, ba_s = best(*r.at(o.t_send))
    trades = [p for t, k, p in ev if k == "trade" and o.t_send < t <= M]
    bids, asks = r.at(M - 0.001)
    asks = dict(asks)
    bb_m, ba_m = best(bids, asks)
    mid10 = _mid(r, M + 10.0)
    lim0 = o.limit
    base = {
        "sig": o.sig, "slug": o.slug, "filled_live": o.filled, "seen": o.seen, "limit": lim0,
        "edge": o.edge, "ok": r.ok, "ba_send": ba_s, "ba_match": ba_m, "mid10": mid10,
        "dep_send": _depth(a_send, lim0), "dep_match": _depth(asks, lim0),
        "taken": sum(p[2] for p in trades if p[0] == "BUY" and p[1] <= lim0 + 1e-9),
    }
    rules = [(f"k{k}", round(o.seen + k / 100, 2)) for k in KS]
    rules += [(f"f{f}", round(o.seen + np.ceil(f * o.edge * 100 - 1e-9) / 100, 2)) for f in FS]
    rules += [("live", lim0)]
    out = []
    for name, lim in rules:
        sh, px = sweep(asks, lim, o.size)
        row = dict(base, rule=name, lim=lim, fill_sh=sh, px=px)
        if sh > 0 and mid10 is not None:
            row["mk10_c"] = (mid10 - px - _fee(px)) / px * 100
            row["pnl"] = sh * (mid10 - px - _fee(px))
            row["cost"] = sh * px
        out.append(row)
    return out


def run(orders: pd.DataFrame, st: dict) -> pd.DataFrame:
    rows = []
    for o in orders.itertuples():
        rows += one(o, st.get(o.token, []))
    return pd.DataFrame(rows)
