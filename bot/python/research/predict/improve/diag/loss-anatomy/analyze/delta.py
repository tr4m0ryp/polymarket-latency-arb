"""Fill-level tables on the settlement delta (cents of the bought token per bp of BTC), the
strongest consistent separator: markout by delta bin, and how the low-delta share moves with
the window (the busy extension vs the quiet hours)."""
from __future__ import annotations

import numpy as np
import pandas as pd

from .. import SHORT
from .stats import days

DBINS = [0, 3, 5, 8, 12, 20, 40, 1e9]


def by_bin(f: pd.DataFrame, nmk: dict) -> pd.DataFrame:
    f = f.assign(delta_bin=pd.cut(f["delta"], DBINS))
    rows = []
    for (arm, L), g in f.groupby(["arm", "L"]):
        d = days(g, nmk)
        for b, x in g.groupby("delta_bin", observed=True):
            rows.append({"arm": SHORT[arm], "L": L, "delta_bin": str(b), "fills": len(x),
                         "share_ext": (x["window"] == "ext").mean(), "lose": x["lose"].mean(),
                         "pred_c": 100 * x["pred"].mean(), "mk10_c_sh": 100 * x["mk_sh"].mean(),
                         "c_usd": 100 * x["mk10v"].sum() / x["cost"].sum(), "usd_day": x["mk10v"].sum() / d})
    return pd.DataFrame(rows)


def by_window(f: pd.DataFrame, nmk: dict) -> pd.DataFrame:
    rows = []
    for (arm, L, w), x in f.groupby(["arm", "L", "window"]):
        d = nmk[w] / 288
        low = x["delta"] < 5
        rows.append({"arm": SHORT[arm], "L": L, "window": w, "fills_day": len(x) / d,
                     "delta_median": x["delta"].median(), "share_delta<5": low.mean(),
                     "lowdelta_fills_day": low.sum() / d,
                     "c_usd_low": 100 * x.loc[low, "mk10v"].sum() / max(x.loc[low, "cost"].sum(), 1e-9) if low.any() else np.nan,
                     "c_usd_rest": 100 * x.loc[~low, "mk10v"].sum() / x.loc[~low, "cost"].sum()})
    return pd.DataFrame(rows)


def comp_check() -> pd.DataFrame:
    """Test3 run 1 at L = 0 under the frozen 50 ms competition sensitivity (final_comp: survive
    50 ms, half of each level) vs the base run (final): markout by delta bin."""
    from scipy.special import ndtri

    from .. import ARMS, POUT, SEALED
    from ..data import state
    mk = pd.read_csv(POUT / "markets-final_comp.csv")
    assert mk["start"].max() < SEALED
    rows = []
    for tag in ("final", "final_comp"):
        f = pd.read_pickle(POUT / f"fills-{tag}.pkl")
        f = f[f["arm"].isin(ARMS) & (f["L"] == 0) & f["m"].isin(mk["m"])]
        parts = []
        for i, g in f.groupby("m"):
            tb = state.tab(int(i))
            j = np.searchsorted(tb["t"].to_numpy(), g["t"].to_numpy(), side="right") - 1
            mid = tb["pm_mid"].to_numpy(float)[j]
            zq = ndtri(np.clip(np.where(g["side"] > 0, mid, 1 - mid), 0.02, 0.98))
            parts.append(g.assign(delta=100 * np.exp(-zq ** 2 / 2) / np.sqrt(2 * np.pi)
                                  * tb["zs"].to_numpy(float)[j] * 1e-4))
        f = pd.concat(parts).assign(bin=lambda d: pd.cut(d["delta"], [0, 5, 12, 40, 1e9]).astype(str))
        for (arm, b), x in f.groupby(["arm", "bin"]):
            rows.append({"run": tag, "arm": SHORT[arm], "delta_bin": b, "fills": len(x),
                         "c_usd": 100 * x["mk10v"].sum() / x["cost"].sum(),
                         "usd_day": x["mk10v"].sum() / (len(mk) / 288)})
    return pd.DataFrame(rows)
