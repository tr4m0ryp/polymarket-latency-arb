"""Row-level calibration tables from data/calib.py: predicted vs realized best-level value of
the side the 1 s model prefers, by settlement-delta bin (and quiet vs busy windows), on the
rows the deployed taker could fire on (pred >= 3 c) and the band just under its margin."""
from __future__ import annotations

import numpy as np
import pandas as pd

from .. import WORK

DBINS = [0, 3, 5, 8, 12, 20, 40, 1e9]


def _agg(g: pd.DataFrame) -> pd.Series:
    return pd.Series({"rows": len(g), "mkts": g["m"].nunique(), "share_ext": (g["window"] == "ext").mean(),
                      "pred_c": 100 * g["pred"].mean(), "real_1s_c": 100 * g["v1"].mean(),
                      "real_10s_c": 100 * np.nanmean(g["v10"]), "pos_1s": (g["v1"] > 0).mean()})


def tables() -> dict[str, pd.DataFrame]:
    c = pd.read_pickle(WORK / "calib_rows.pkl")
    c = c[np.isfinite(c["v1"])]
    c["delta_bin"] = pd.cut(c["delta"], DBINS).astype(str)
    c["regime"] = np.where(c["window"] == "ext", "ext (busy)", "select+dev3+test3r1")
    out = {}
    fire = c[c["pred"] >= 0.03]
    out["calib_delta"] = (fire.groupby(["L", "delta_bin"], sort=False).apply(_agg, include_groups=False)
                          .reset_index().sort_values(["L", "delta_bin"], key=_key))
    out["calib_regime"] = (fire.groupby(["L", "regime", "delta_bin"], sort=False).apply(_agg, include_groups=False)
                           .reset_index().sort_values(["L", "regime", "delta_bin"], key=_key))
    under = c[(c["pred"] >= 0.02) & (c["pred"] < 0.03)]
    out["calib_under_margin"] = (under.groupby(["L", "delta_bin"], sort=False).apply(_agg, include_groups=False)
                                 .reset_index().sort_values(["L", "delta_bin"], key=_key))
    return out


def _key(s: pd.Series):
    if s.name == "delta_bin":
        return s.map(lambda x: float(x.split(",")[0].strip("(")))
    return s
