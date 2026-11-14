"""Baseline arm (c): the two 5m leaders' actual fills in the recorded markets, scored like
our simulated fills (hold to resolution, full taker fee at our 0% tier, makers pay none).

    nice -n 10 python3 -m research.strategy.eval.leaders [--markout]

--markout adds mk10v (each fill valued at the venue mid 10 s after its block second, from
the replayed book; block times are ~2 s coarse) to the saved fills. Data API /trades per
market (all fills, plus takerOnly to tag taker fills; cached on disk, the markets are
closed). Writes data/out/strategy/fills-leaders.pkl, same columns as eval/sim.py
(arm = leaderA_all / leaderA_taker / leaderB_..., L = 0)."""
from __future__ import annotations

import sys

import numpy as np
import pandas as pd

from .. import OUT, ROOT, fee
from ..ingest.load import Store
from .prep import split, usable

sys.path.insert(0, str(ROOT))
from btclat.api.data import market_trades  # noqa: E402

WALLETS = {"A": "0xc53375ff94e96100f2b30a4b5775db35218d69a9",
           "B": "0x3048d65321be3497164cdfc2996f94f98a2e7537"}


def _key(t: dict) -> tuple:
    return (t["transactionHash"], t["proxyWallet"], t["asset"], t["side"])


def market_fills(cid: str, up: str) -> pd.DataFrame:
    tk = {_key(t) for t in market_trades(cid, taker_only=True)}
    rows = []
    for t in market_trades(cid, taker_only=False):
        w = t["proxyWallet"].lower()
        for name, addr in WALLETS.items():
            if w == addr:
                rows.append({"who": name, "ts": float(t["timestamp"]), "is_up": t["asset"] == up,
                             "buy": t["side"] == "BUY", "shares": float(t["size"]),
                             "px": float(t["price"]), "taker": _key(t) in tk})
    return pd.DataFrame(rows)


def add_markout(f: pd.DataFrame, st: Store) -> pd.DataFrame:
    from ..sim.grid import Book
    parts = []
    for i, g in f.groupby("m"):
        m = st.market(int(i))
        meta = m["meta"]
        book = Book(m["ev"], meta["start"] - 2, meta["end"] + 2, m["gaps"])
        mid = book.mid(book.g_ceil(g["ts"].to_numpy() + 10.0))
        val = np.where(g["is_up"], mid, 1 - mid)
        val = np.where(np.isfinite(val), val, np.where(g["is_up"], st.outcome[meta["slug"]],
                                                       1 - st.outcome[meta["slug"]]))
        parts.append(g.assign(mk10v=g["shares"] * val - g["cost"] - g["fee"]))
    return pd.concat(parts)


def main() -> None:
    if "--markout" in sys.argv:
        st = Store()
        f = pd.read_pickle(OUT / "fills-leaders.pkl")
        add_markout(f, st).to_pickle(OUT / "fills-leaders.pkl")
        return
    st = Store()
    sp = split(st.mk)
    out = []
    for i in usable(st):
        m = st.mk.iloc[i]
        f = market_fills(m["condition_id"], str(m["up"]))
        if not len(f):
            continue
        o = st.outcome[m["slug"]]
        won = np.where(f["is_up"], o, 1 - o)
        sign = np.where(f["buy"], 1.0, -1.0)  # sells close exposure at px
        f["cost"] = sign * f["shares"] * f["px"]
        f["fee"] = np.where(f["taker"], f["shares"] * fee(f["px"]), 0.0)
        f["pnl"] = sign * f["shares"] * won - f["cost"] - f["fee"]
        f["won"] = np.where(f["buy"], won, 1 - won)
        f["m"], f["end"], f["split"], f["L"] = i, m["end"], sp[i], 0
        f["secs_left"] = m["end"] - f["ts"]
        out.append(f)
        print(i, len(f), flush=True)
    f = pd.concat(out, ignore_index=True)
    arms = []
    for who in WALLETS:
        g = f[f["who"] == who]
        arms.append(g.assign(arm=f"leader{who}_all"))
        arms.append(g[g["taker"]].assign(arm=f"leader{who}_taker"))
    pd.concat(arms, ignore_index=True).to_pickle(OUT / "fills-leaders.pkl")


if __name__ == "__main__":
    main()
