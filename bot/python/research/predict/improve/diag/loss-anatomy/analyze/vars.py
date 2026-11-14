"""State variables scored for "fill loses", grouped by what they describe. Signed variables are
oriented toward the side bought (> 0 = moving / leaning our way). `POST` are known only after
the fill (diagnostic, not usable as a gate)."""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.special import ndtri

from research.strategy import fee

GROUPS = {
    "binance vol": ["sigma", "rv60", "rv300", "abs_dmid5", "abs_dmid1"],
    "binance rate": ["p_lam", "s_lam", "st_tn", "rows10", "p_tsm", "s_tsm"],
    "binance signal (signed)": ["p_dmic0.1", "s_dmic0.1", "p_dmic1", "p_dmid5", "p_imb", "s_imb",
                                "p_ofi0.4", "mic_dev", "basis_dev", "st_sv1", "pm_stale"],
    "polymarket book": ["pm_spr", "pm_tsc", "pm_chg10", "v_top", "v_dep", "v_opp", "v_near",
                        "v_imb", "bk0", "bk1", "bk2", "gap", "fair_edge"],
    "price level": ["seen", "abs_mid"],
    "time to expiry": ["secs_left"],
    "strike distance": ["abs_z", "dist_bp", "delta"],
    "own history": ["burst_pos", "own_prev5", "fill_idx", "log_since_own"],
    "model": ["pred", "pred_other", "pred_gap", "pred_x_rv", "exc", "pred_proj", "pred_over_delta"],
}
POST = ["fill_frac", "v_dep_m", "v_top_m", "post_burst_n", "post_mkt_n", "d_hold"]


def add_vars(f: pd.DataFrame) -> pd.DataFrame:
    f["abs_dmid5"] = f["p_dmid5"].abs()
    f["abs_dmid1"] = f["p_dmid1"].abs()
    f["v_imb"] = (f["v_opp"] - f["v_top"]) / (f["v_opp"] + f["v_top"])
    f["pred_gap"] = f["pred"] - f["pred_other"]
    f["pred_x_rv"] = f["pred"] / np.maximum(f["rv60"], 0.05)   # edge per unit of recent vol
    # settlement delta (model/derive.py): cents of the bought token per bp of BTC at this price
    zq = ndtri(np.clip(f["tok_mid"], 0.02, 0.98))
    f["delta"] = 100 * np.exp(-zq ** 2 / 2) / np.sqrt(2 * np.pi) * f["zs"] * 1e-4
    f["pred_over_delta"] = 100 * f["pred"] / f["delta"]          # predicted value in bp of BTC
    # two-side coherence: value_up + value_dn = -(spread + both fees) at the match, whatever
    # the mark, so any excess of pred + pred_other over that floor is model error
    other_ask = 1 - f["seen"] + f["pm_spr"] / 100
    floor = -(f["pm_spr"] / 100 + fee(f["seen"]) + fee(other_ask))
    f["exc"] = f["pred"] + f["pred_other"] - floor
    f["pred_proj"] = f["pred"] - f["exc"] / 2                     # projected onto the identity
    f["key"] = f["m"]
    return f


def all_vars() -> list[str]:
    return [v for g in GROUPS.values() for v in g]


def group_of(v: str) -> str:
    return next((g for g, vs in GROUPS.items() if v in vs), "post hoc")
