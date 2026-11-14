"""Summary tables over the event rows (event.study output)."""
from __future__ import annotations

import numpy as np
import pandas as pd

from event import CENSOR, EXPOST, OFFS, PROF


def lead_table(ev: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (s, f), g in ev.groupby(["set", "fam"]):
        lag = g["lag_recv"]
        moved = lag.notna()
        rows.append({"set": s, "fam": f, "n": len(g),
                     "already_moved": g["pre_moved"].mean(),
                     "p_move_250ms": (lag <= 0.25).mean(), "p_move_1s": (lag <= 1).mean(),
                     f"p_move_{CENSOR:g}s": moved.mean(),
                     "lag_med": lag.median(), "lag_server_med": g["lag_server"].median(),
                     "by_trade": g.loc[moved, "by_trade"].mean()})
    return pd.DataFrame(rows)


def profile(ev: pd.DataFrame) -> pd.DataFrame:
    """Signed move since R0 - 1.2 s, as a fraction of its value at +3 s (book)
    and +5 s (Binance), averaged over events; offsets on our receipt clock."""
    rows = []
    for (s, f), g in ev.groupby(["set", "fam"]):
        if s == "baseline":
            continue
        r = {"set": s, "fam": f, "n": len(g), "book_c_3s": 100 * g[f"dmid_{EXPOST:g}"].mean(),
             "binance_bp_5s": g["dbn_5"].mean()}
        for o in PROF:
            r[f"book_{o:g}"] = g[f"dmid_{o:g}"].mean() / g[f"dmid_{EXPOST:g}"].mean()
        for o in PROF:
            r[f"bn_{o:g}"] = g[f"dbn_{o:g}"].mean() / g["dbn_5"].mean()
        rows.append(r)
    return pd.DataFrame(rows)


def depth_table(ev: pd.DataFrame, fk: str) -> pd.DataFrame:
    """Stale depth under fair `fk` (mo: book mid 3 s later; mdl: spot model).
    edge_X = USD of fee-adjusted edge still on the book X s after our receipt."""
    rows = []
    for (s, f), g in ev.groupby(["set", "fam"]):
        u0 = g[f"{fk}_usd_0"]
        r = {"set": s, "fam": f, "n": len(g), "has_stale": (u0 > 0).mean(),
             "usd0_med_if_any": u0[u0 > 0].median() if (u0 > 0).any() else 0.0,
             "usd0_mean": u0.mean()}
        for o in OFFS:
            r[f"edge_{o:g}s"] = g[f"{fk}_edge_{o:g}"].mean()
        rows.append(r)
    return pd.DataFrame(rows)


def by_move(ev: pd.DataFrame, fam: str) -> pd.DataFrame:
    g = ev[(ev["fam"] == fam) & (ev["set"] == "burst1")].copy()
    g["bucket"] = pd.cut(g["dbn_5"], [-np.inf, 1, 2, 3, 5, np.inf], right=False).astype(str)
    return g.groupby("bucket", observed=True).agg(
        n=("d", "size"), book_c_3s=("dmid_3", lambda x: 100 * x.mean()),
        mdl_dfair_c=("dfair", lambda x: 100 * x.abs().mean()),
        mo_usd0=("mo_usd_0", "mean"), mo_edge0=("mo_edge_0", "mean"),
        mo_edge_250ms=("mo_edge_0.25", "mean"), mo_edge_1s=("mo_edge_1", "mean"),
        taken_usd=("taken_usd", "mean"), taken_edge=("taken_edge", "mean")).reset_index()


def taken_table(ev: pd.DataFrame) -> pd.DataFrame:
    """What takers actually did in [R0 - 0.5, R0 + 2] s: USD bought on the burst
    side, its fee-adjusted edge vs the book mid 3 s later, and USD bought against."""
    return ev.groupby(["set", "fam"]).agg(
        n=("d", "size"), fills=("taken_n", "mean"), usd_with=("taken_usd", "mean"),
        usd_against=("against_usd", "mean"), edge_with=("taken_edge", "mean"),
        edge_with_med=("taken_edge", "median")).reset_index()
