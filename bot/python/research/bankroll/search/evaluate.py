"""Full evaluation of one cap set on one pool: 24 h bootstrap, 24 h rotations, 7 d bootstrap."""
from __future__ import annotations

import numpy as np

from .. import START
from ..sim import bootstrap, encode, rotations, simulate
from .stats import summary

N24, N7 = 2000, 1000


def evaluate(pool, caps, start: float = START, n24: int = N24, n7: int = N7, seed: int = 2) -> dict:
    cfg = encode(caps)
    b = simulate(pool, bootstrap(pool.n_markets, n24, 288, seed), cfg, start, seed=seed)
    r = simulate(pool, rotations(pool.n_markets, 288), cfg, start, seed=seed)
    w = simulate(pool, bootstrap(pool.n_markets, n7, 288 * 7, seed + 1), cfg, start, seed=seed + 1)
    out = {f"b_{k}": v for k, v in summary(b, start, 24.0, start / 2).items()}
    out |= {f"r_{k}": v for k, v in summary(r, start, 24.0, start / 2).items()}
    s7 = summary(w, start, 168.0, start / 4)
    out |= {"w_med": s7["median"], "w_p10": s7["p10"], "w_p90": s7["p90"], "w_mean": s7["mean"],
            "w_p_below_quarter": s7["p_ruin"], "w_p_loss": s7["p_loss"], "w_maxdd_p90": s7["maxdd_p90"],
            "w_worst_mkt_frac": s7["worst_mkt_frac"], "w_med_log": s7["med_log"]}
    out["feasible"] = bool(out["b_p_ruin"] <= 0.05 and out["r_p_ruin"] <= 0.05 and out["w_p_below_quarter"] <= 0.01)
    return out
