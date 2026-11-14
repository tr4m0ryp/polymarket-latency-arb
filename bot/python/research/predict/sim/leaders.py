"""Leaders' actual fills (Data API) on chosen markets, scored like simulated fills; reuses
research/strategy/eval/leaders.py. Run-2 markets come from the strategy's saved pickle.

    python3 -m research.predict.sim.leaders --seg test3"""
from __future__ import annotations

import argparse

import numpy as np
import pandas as pd

from .. import OUT
from ...strategy import OUT as SOUT, fee
from ...strategy.eval.leaders import WALLETS, add_markout, market_fills
from ...strategy.ingest.load import Store
from ..model.data import market_ids
from .fills import AGG


def fetch(ids, st: Store) -> pd.DataFrame:
    out = []
    for i in ids:
        m = st.mk.iloc[i]
        f = market_fills(m["condition_id"], str(m["up"]))
        if not len(f):
            continue
        o = st.outcome[m["slug"]]
        won = np.where(f["is_up"], o, 1 - o)
        sign = np.where(f["buy"], 1.0, -1.0)
        f["cost"] = sign * f["shares"] * f["px"]
        f["fee"] = np.where(f["taker"], f["shares"] * fee(f["px"]), 0.0)
        f["pnl"] = sign * f["shares"] * won - f["cost"] - f["fee"]
        f["won"] = np.where(f["buy"], won, 1 - won)
        f["m"], f["end"], f["L"] = i, m["end"], 0
        out.append(f)
    f = add_markout(pd.concat(out, ignore_index=True), st)
    return pd.concat([f[f["who"] == w].assign(arm=f"leader{w}_all") for w in WALLETS], ignore_index=True)


def agg(seg: str) -> pd.DataFrame:
    p = OUT / f"fills-leaders-{seg}.pkl"
    if seg in ("train", "select"):
        f = pd.read_pickle(SOUT / "fills-leaders.pkl")
        f = f[f["arm"].str.endswith("_all")]
    else:
        f = pd.read_pickle(p)
    f = f.assign(mk3v=np.nan, shares=f["shares"])
    return f.groupby(["arm", "L", "m", "end"]).agg(**AGG).reset_index()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seg", required=True)
    a = ap.parse_args()
    st = Store()
    fetch(market_ids(a.seg, st), st).to_pickle(OUT / f"fills-leaders-{a.seg}.pkl")


if __name__ == "__main__":
    main()
