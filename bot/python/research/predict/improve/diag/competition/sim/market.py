"""One market: decisions of every arm, the base fill with its competition measurements, and
every fill scenario's got / cost / fee / 10 s markout per order (wide columns <scen>_<x>)."""
from __future__ import annotations

import numpy as np
import pandas as pd

from ......strategy.sim.grid import Book, _replay
from .. import SEALED
from .decide import decisions
from ..data.prints import up_frame
from .scen import scenarios
from .measure import order_stats
from .taker import run

HOLD = 0.150


def _mark(book, recs, side, won, h=10.0):
    tf = np.array([r["tf"] for r in recs])
    mid = book.mid(book.g_ceil(tf + h))
    mk = np.where(side > 0, mid, 1 - mid)
    return np.where(np.isfinite(mk), mk, won)


def _cols(book, recs, side, won, pre):
    got = np.array([r["got"] for r in recs])
    cost = np.array([r["cost"] for r in recs])
    fee = np.array([r["fee"] for r in recs])
    out = {f"{pre}_got": got, f"{pre}_cost": cost, f"{pre}_fee": fee,
           f"{pre}_mk10v": got * _mark(book, recs, side, won) - cost - fee}
    if pre == "base":
        out["base_mk3v"] = got * _mark(book, recs, side, won, 3.0) - cost - fee
        out["base_mk1v"] = got * _mark(book, recs, side, won, 1.0) - cost - fee
    return out


def one(st, i: int, win: str, kind: str = "main") -> pd.DataFrame:
    m = st.market(i)
    meta = m["meta"]
    assert meta["start"] < SEALED
    book = Book(m["ev"], meta["start"] - 2, meta["end"] + 2, m["gaps"])
    ev = m["ev"]
    R = _replay(ev["t"], ev["side"], ev["tick"].astype(np.int64), ev["size"], book.t0, book.n)
    p = up_frame(m["tr"], i, tag_leaders=win in ("final", "ext"))
    o = float(m["outcome"])
    parts = []
    for arm, L, d in decisions(i, race=kind == "race"):
        Ls = L / 1000
        base = run(book, d["t"], d["side"], d["shares"], d["limit"], Ls, hold=HOLD)
        side = d["side"].astype(int)
        won = np.where(side > 0, o, 1 - o)
        if kind == "main":
            f = pd.DataFrame([order_stats(book, R, p, ev["t"], d, j, base[j], Ls, HOLD) for j in range(len(base))])
        else:
            f = pd.DataFrame(index=range(len(base)))
        f["arm"], f["L"], f["m"], f["win"], f["end"] = arm, L, i, win, meta["end"]
        f["t"], f["side"], f["seen"], f["edge"], f["won"] = d["t"], side, d["seen"], d["edge"], won
        f["skip"] = [r["skip"] for r in base]
        f["secs_left"] = meta["end"] - d["t"]
        f["lv0"] = [r["lv"][0][1] if r["lv"] else 0.0 for r in base]   # shares at the first level hit
        cols = _cols(book, base, side, won, "base")
        for name, kw, rule in scenarios(kind):
            if name == "base":
                continue
            sh = d["shares"] if rule is None else rule(d, f)
            lim = d["limit"] if "slip" not in kw else np.minimum(d["seen"] + kw["slip"], 0.99)
            lim = kw["lim"](d) if "lim" in kw else lim
            recs = run(book, d["t"], d["side"], sh, lim, Ls, kw["J"], kw["cap"], HOLD, kw["e"])
            cols.update(_cols(book, recs, side, won, name))
        parts.append(pd.concat([f, pd.DataFrame(cols)], axis=1))
    return pd.concat(parts, ignore_index=True) if parts else pd.DataFrame()
