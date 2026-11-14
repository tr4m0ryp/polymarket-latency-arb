"""Build the event table: every Binance perp event on every allowed market, with the venue's
response, our taker's post-hold value and the activity state before it.

    OMP_NUM_THREADS=2 nice -n 10 python3 research/predict/improve/diag/mechanism-literature build
        [--windows select,dev3,test3r1,ext] [--limit N]

Writes WORK/events.pkl (data/cache/predict/improve/mechanism-literature/)."""
from __future__ import annotations

import argparse
import time

import numpy as np
import pandas as pd

from research.strategy.sim.grid import Book
from . import SEALED, WINDOWS, WORK
from .data.guard import assert_allowed, market_ids, meta
from .data.load import Hours, market
from .events.activity import activity
from .events.detect import detect, perp_logmid
from .events.response import flow, respond


def one(hrs: Hours, i: int, m: pd.Series) -> pd.DataFrame:
    d = market(hrs, i, m)
    if d is None or d["tab"] is None or not d["perp"]:
        return pd.DataFrame()
    start, end = float(m["start"]), float(m["end"])
    e, pl = detect(d["perp"], d["tab"], start, end)
    if not e or not len(e["k"]):
        return pd.DataFrame()
    book = Book(d["ev"], start - 2, end + 2)
    fl = flow(d["tr"])
    lm = perp_logmid(d["perp"])
    out = []
    for flag, x in ((0, e), (1, pl)):
        if not x or not len(x["k"]):
            continue
        act = activity(d["perp"], lm, d["spot_bk"], d["spot_tr"], d["ev"], fl[0], x)
        rows = [respond(book, fl, float(act["T0"][j]), float(act["t0"][j]), int(x["side"][j]))
                for j in range(len(x["k"]))]
        df = pd.concat([pd.DataFrame({k: v for k, v in x.items() if k not in ("k", "base")}),
                        pd.DataFrame(act), pd.DataFrame(rows)], axis=1)
        df["placebo"] = flag
        out.append(df)
    df = pd.concat(out, ignore_index=True)
    df["m"], df["start"] = i, start
    return df


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--windows", default=",".join(WINDOWS))
    ap.add_argument("--limit", type=int, default=None)
    a = ap.parse_args()
    ids = market_ids(a.windows.split(","))
    allm = sorted({i for v in ids.values() for i in v})
    mt = meta(allm)
    win = {i: w for w, v in ids.items() for i in v}
    if a.limit:
        allm = allm[:: max(1, len(allm) // a.limit)][: a.limit]
    parts, t0 = [], time.time()
    hrs = Hours(keep=2)
    for n, i in enumerate(allm):
        df = one(hrs, i, mt.loc[i])
        if len(df):
            df["window"] = win[i]
            parts.append(df)
        if n % 25 == 0:
            print(f"{n}/{len(allm)} markets, {sum(len(p) for p in parts)} events, {time.time() - t0:.0f}s",
                  flush=True)
    ev = pd.concat(parts, ignore_index=True)
    assert_allowed(ev["start"], "events")
    assert ev["start"].max() < SEALED and ev["T0"].max() < SEALED
    WORK.mkdir(parents=True, exist_ok=True)
    ev.to_pickle(WORK / "events.pkl")
    print("rows", len(ev), "placebo", int(ev["placebo"].sum()), "markets", ev["m"].nunique(), "max start", int(ev["start"].max()),
          "by window", ev.groupby("window").size().to_dict())
    print(ev.describe().T.round(3).to_string())


if __name__ == "__main__":
    np.seterr(all="ignore")
    main()
