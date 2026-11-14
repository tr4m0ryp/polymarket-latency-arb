"""Validate the feed's trade-direction labels (last_trade_price `side`) against the venue book.

A print at an Up-frame price >= the best Up ask resting one grid step (5 ms) before its venue
stamp was buyer-initiated in the Up frame; <= the best bid, seller-initiated. Agreement of the
label with that price test is the label's accuracy on the prints the test can classify.

    OMP_NUM_THREADS=2 nice -n 10 python3 research/predict/improve/diag/mechanism-literature sidecheck"""
from __future__ import annotations

import numpy as np
import pandas as pd

from research.predict.report.md import md
from research.strategy.sim.grid import Book
from .. import OUT, SEALED
from ..data.guard import assert_allowed, market_ids, meta
from ..data.load import Hours, market
from ..events.response import flow

DIR = OUT / "diag-mechanism-literature"


def one(hrs: Hours, i: int, m: pd.Series) -> pd.DataFrame:
    d = market(hrs, i, m)
    if d is None or not d["tr"]:
        return pd.DataFrame()
    start, end = float(m["start"]), float(m["end"])
    book = Book(d["ev"], start - 2, end + 2)
    ts, dr, p, sz = flow(d["tr"])
    w = (ts > start) & (ts < end)
    ts, dr, p, sz = ts[w], dr[w], p[w], sz[w]
    g = np.clip(book.g_floor(ts) - 1, 0, None)
    bb, ba = book.bb[g] / 100, book.ba[g] / 100
    ok = (bb > 0) & (ba < 1)
    cls = np.where(p >= ba - 1e-9, 1, np.where(p <= bb + 1e-9, -1, 0))
    return pd.DataFrame({"m": i, "start": start, "label": dr[ok], "cls": cls[ok], "size": sz[ok],
                         "spr": (ba - bb)[ok]})


def main() -> None:
    ids = market_ids()
    win = {i: w for w, v in ids.items() for i in v}
    pick = sorted(win)[::8]
    mt = meta(pick)
    hrs, parts = Hours(keep=2), []
    for i in pick:
        x = one(hrs, i, mt.loc[i])
        if len(x):
            parts.append(x.assign(window=win[i]))
    d = pd.concat(parts, ignore_index=True)
    assert_allowed(d["start"], "sidecheck")
    assert d["start"].max() < SEALED
    rows = []
    for w, g in list(d.groupby("window")) + [("all", d)]:
        c = g[g["cls"] != 0]
        rows.append({"window": w, "markets": g["m"].nunique(), "prints": len(g),
                     "classifiable": round(len(c) / len(g), 3),
                     "label agrees": round(float((c["label"] == c["cls"]).mean()), 3),
                     "agrees, size-weighted": round(float(c["size"][c["label"] == c["cls"]].sum() / c["size"].sum()), 3),
                     "agrees, 1-tick spread": round(float((c["label"] == c["cls"])[c["spr"] < 0.015].mean()), 3)})
    t = pd.DataFrame(rows)
    DIR.mkdir(parents=True, exist_ok=True)
    t.to_csv(DIR / "trade_side_check.csv", index=False)
    print(md(t, 3))


if __name__ == "__main__":
    np.seterr(all="ignore")
    main()
