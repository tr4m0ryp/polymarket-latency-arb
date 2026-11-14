"""Calibration of the frozen taker's orders split by fill outcome (censor/orders.py).

    python3 -m research.predict.improve.diag.calibration.censor.table

Per window x L x regime (all rows / busy index >= 1): orders per market-hour, fill share, mean
prediction, best-level realised 1 s value and its gap (realised - pred) on filled and on
unfilled orders (market-bootstrap 95% CI), the seen-to-match ask move, and the simulator's 10 s
markout per filled share. gap_order_value uses the limit-censored 1 s value o1 = r1 when the
best ask at the match is within the limit (seen + 2 c), else 0 (the order does not fill, it
neither earns nor loses). money_gap_filled = simulator 10 s markout per filled share minus the
share-weighted prediction (fill-level calibration in money). Writes OUT/censor.md / censor.csv."""
from __future__ import annotations

import numpy as np
import pandas as pd

from .....report.md import md
from .. import OUT
from ..analyze.common import boot_ratio
from .orders import WINS, orders


def _gap(g: pd.DataFrame, y: str = "r1") -> str:
    if not len(g):
        return ""
    p, lo, hi = boot_ratio(g["m"].to_numpy(), (g[y] - g["pred"]).to_numpy(), np.ones(len(g)))
    return f"{100 * p:+.1f} [{100 * lo:+.1f}, {100 * hi:+.1f}]"


def row(g: pd.DataFrame, nm: int) -> dict:
    f, u = g[g["filled"]], g[~g["filled"]]
    return {"orders_h": len(g) / (nm / 12), "fill_share": len(f) / max(len(g), 1), "pred_c": 100 * g["pred"].mean(),
            "r1_all_c": 100 * g["r1"].mean(), "gap_all": _gap(g), "gap_order_value": _gap(g, "o1"),
            "gap_filled": _gap(f), "gap_unfilled": _gap(u),
            "ask_move_filled_c": 100 * f["ask_move"].mean(), "ask_move_unfilled_c": 100 * u["ask_move"].mean(),
            "r10_filled_c": 100 * f["r10"].mean(), "fill_mk10_c_sh": 100 * f["mk10"].sum() / max(f["fill_sh"].sum(), 1),
            "pred_filled_c": 100 * (f["pred"] * f["fill_sh"]).sum() / max(f["fill_sh"].sum(), 1),
            "money_gap_filled": _money(f)}


def _money(f: pd.DataFrame) -> str:
    """Fill-level calibration: (10 s markout - pred * shares) / shares over filled orders."""
    if not len(f):
        return ""
    p, lo, hi = boot_ratio(f["m"].to_numpy(), (f["mk10"] - f["pred"] * f["fill_sh"]).to_numpy(), f["fill_sh"].to_numpy())
    return f"{100 * p:+.1f} [{100 * lo:+.1f}, {100 * hi:+.1f}]"


def main() -> None:
    p = OUT / "censor_orders.pkl"
    allo = pd.read_pickle(p) if p.exists() else pd.concat([orders(w) for w in WINS], ignore_index=True)
    allo = allo[np.isfinite(allo["r1"]) & np.isfinite(allo["pred"])]
    allo["o1"] = np.where(allo["ask_move"] <= 0.02 + 1e-9, allo["r1"], 0.0)   # limit = seen ask + 2 c
    allo.to_pickle(OUT / "censor_orders.pkl")
    out = []
    for (w, L), g in allo.groupby(["win", "L"], sort=False):
        nm = g["m"].nunique()
        out.append({"win": w, "L": L, "regime": "all", **row(g, nm)})
        out.append({"win": w, "L": L, "regime": "busy>=1", **row(g[g["busy"] >= 1.0], nm)})
    t = pd.DataFrame(out)
    t.to_csv(OUT / "censor.csv", index=False)
    (OUT / "censor.md").write_text("# Frozen 1 s taker orders: calibration by fill outcome\n\n" + md(t.round(2)))
    print(md(t.round(2)))


if __name__ == "__main__":
    main()
