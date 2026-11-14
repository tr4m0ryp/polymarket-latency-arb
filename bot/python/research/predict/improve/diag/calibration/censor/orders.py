"""Every order of the frozen 1 s taker (vt_v1_m0.03_any, rebuilt exactly by rules.vtaker on the
cached frozen predictions) with its fill outcome from the recalibration simulator run
(fills-recal-<win>.pkl, arm vt_v1_m3, which reproduces the frozen agg files to the cent) and
its best-level realised values at the decision (model/derive.side_values, 1 s and 10 s marks).

Fields per order: win, m, t, side, L, pred, r1, r10 (best level, $/sh), ask_move (best ask of
the bought side at the match minus the seen ask, $), filled, fill_sh, mk10_sh (fill 10 s
markout per share), busy (row busy index)."""
from __future__ import annotations

import numpy as np
import pandas as pd

from ......predict.model.data import TAB
from ......predict.model.derive import side_values
from ......predict.sim import rules
from ....harness.api import saved_pred
from .. import OUT
from ..ctx.load import busy, ctx
from ..safe import TAGS, check, market_ids, start_of

WINS = ("select", "dev3", "final", "ext")


def _fills(win: str) -> pd.DataFrame:
    f = pd.read_pickle(OUT / "sim" / f"fills-recal-{win}.pkl")
    f = f[f["arm"] == "vt_v1_m3"]
    return f.groupby(["m", "L", "t", "side"]).agg(fill_sh=("shares", "sum"), mk10=("mk10v", "sum")).reset_index()


def market_orders(i: int, L: int) -> pd.DataFrame:
    with np.load(TAB / f"{i}.npz") as z:
        df = pd.DataFrame({k: z[k] for k in z.files})
    up, dn = saved_pred(i, f"v1_L{L}", df[[c for c in df.columns if not c.startswith(("y_", "x_"))]])
    d = rules.vtaker(df, up, dn, margin=0.03)
    if not len(d["t"]):
        return pd.DataFrame()
    ix = np.searchsorted(df["t"].to_numpy(), d["t"])
    side = d["side"]
    out = {"m": i, "L": L, "t": d["t"], "side": side, "pred": d["edge"]}
    for k in (1, 10):
        u, w = side_values(df, L, k)
        out[f"r{k}"] = np.where(side > 0, u[ix], w[ix])
    ba, bb = df[f"x_ba{L}"].to_numpy(float)[ix] / 100, df[f"x_bb{L}"].to_numpy(float)[ix] / 100
    seen = np.where(side > 0, df["pm_ba"].to_numpy(float)[ix] / 100, 1 - df["pm_bb"].to_numpy(float)[ix] / 100)
    out["ask_move"] = np.where(side > 0, ba, 1 - bb) - seen
    out["busy"] = busy(ctx(i, len(df)))[ix]
    return pd.DataFrame(out)


def orders(win: str) -> pd.DataFrame:
    ids = market_ids(win)
    check(start_of(ids))
    o = pd.concat([market_orders(i, L) for i in ids for L in (0, -40)], ignore_index=True)
    f = _fills(win)
    o = o.merge(f, on=["m", "L", "t", "side"], how="left")
    o["filled"] = o["fill_sh"].fillna(0) > 0
    o["mk10_sh"] = o["mk10"] / o["fill_sh"]
    assert int(o["filled"].sum()) == len(f[f["m"].isin(ids)]), "fills not matched to orders"
    return o.assign(win=win)
