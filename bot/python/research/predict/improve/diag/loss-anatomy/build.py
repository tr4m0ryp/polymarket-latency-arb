"""Build the per-fill state table (and the per-market regime table) on the allowed windows.

Reads the frozen runs' fills (data/out/predict/fills-<tag>.pkl), never re-simulates. Writes
data/out/predict/improve/loss-anatomy/fills_state.pkl and markets_state.pkl."""
from __future__ import annotations

import time

import numpy as np
import pandas as pd

from . import ARMS, LS, POUT, SEALED, WINDOWS, WORK
from .data import pmbook, state
from .data.guard import check_ids, market_ids, meta
from .data.own import outcome_columns, own_columns


def _fills(window: str, ids: list[int]) -> pd.DataFrame:
    f = pd.read_pickle(POUT / f"fills-{WINDOWS[window]}.pkl")
    f = f[f["arm"].isin(ARMS) & f["L"].isin(LS) & f["m"].isin(ids)].copy()
    f["window"] = window
    return f


def main() -> None:
    ids = market_ids()
    allm = sorted({i for v in ids.values() for i in v})
    mt = meta(allm)
    check_ids(ids, mt)
    assert mt["start"].max() < SEALED
    fills = pd.concat([_fills(w, v) for w, v in ids.items()], ignore_index=True)
    assert fills["t"].max() < SEALED
    win_of = {i: w for w, v in ids.items() for i in v}
    rows, mrows, t0 = [], [], time.time()
    for n, i in enumerate(allm):
        start, end = float(mt.at[i, "start"]), float(mt.at[i, "end"])
        assert start < SEALED and end <= SEALED
        tb = state.tab(i)
        mrows.append({"m": i, "window": win_of[i], "start": start, **state.market_state(tb)})
        fm = fills[fills["m"] == i]
        if not len(fm):
            continue
        bk, t_ok = pmbook.book(i, start, end)
        for (arm, L), g in fm.groupby(["arm", "L"]):
            g = g.sort_values("t").reset_index(drop=True)
            s = state.fill_state(tb, g, int(L))
            v = pmbook.venue_state(bk, t_ok, g["t"].to_numpy(), g["side"].to_numpy(float),
                                   s["seen"].to_numpy(), int(L))
            rows.append(pd.concat([g, s, pd.DataFrame(v)], axis=1))
        if n % 25 == 0:
            print(f"{n}/{len(allm)} markets, {time.time() - t0:.0f} s", flush=True)
    f = pd.concat(rows, ignore_index=True)
    f = outcome_columns(own_columns(f))
    WORK.mkdir(parents=True, exist_ok=True)
    f.to_pickle(WORK / "fills_state.pkl")
    pd.DataFrame(mrows).to_pickle(WORK / "markets_state.pkl")
    print("fills", len(f), "markets", len(mrows), "venue cols", int(np.isfinite(f["v_top"]).sum()))


if __name__ == "__main__":
    main()
