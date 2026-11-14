"""Run every loss-anatomy table from the built state tables and write CSVs + the markdown.

    python3 research/predict/improve/diag/loss-anatomy analyze"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .. import SEALED, WORK
from ..data.guard import market_ids
from . import calib, cuts, delta, fills, markets
from .report import write
from .rules import DELTA_GRID, RULES
from .vars import add_vars


def load():
    f = add_vars(pd.read_pickle(WORK / "fills_state.pkl"))
    ms = pd.read_pickle(WORK / "markets_state.pkl")
    assert ms["start"].max() < SEALED and f["t"].max() < SEALED
    ids = market_ids()
    nmk = {w: len(v) for w, v in ids.items()}
    ms["hour"] = ((ms["start"] % 86400) // 3600).astype(int)
    nmk_hour = ms.groupby(["window", "hour"]).size()
    f["hour"] = f["m"].map(ms.set_index("m")["hour"])      # market start hour (UTC), as the denominators
    return f, ms, nmk, nmk_hour


def main() -> None:
    f, ms, nmk, nmk_hour = load()
    t = {}
    t["overview"] = fills.overview(f, nmk)
    t["decomp"] = fills.decomposition(f)
    t["auc"] = fills.auc_table(f)
    t["hour"] = fills.by_hour(f, nmk_hour)
    t["delta_bins"] = delta.by_bin(f, nmk)
    t["delta_windows"] = delta.by_window(f, nmk)
    t["delta_comp"] = delta.comp_check()
    pm = markets.per_market(f, ms)
    t["tails"] = markets.tails(pm)
    t["shared"] = markets.shared(pm)
    t["regime_auc"] = markets.regime_auc(pm)
    t["regime_rv"] = markets.regime_terciles(pm, ms, "m_rv")
    t["worst_taker_L0"] = markets.worst(pm, "vt_v1_m0.03_any", 0)
    t["worst_veto_L0"] = markets.worst(pm, "vt_v1_m0.02_trigger", 0)
    t["screen_select"] = cuts.screen(f, nmk, arms=("vt_v1_m0.03_any", "vt_v1_m0.02_trigger"))
    t["rules"] = cuts.fixed_rules(f, nmk, RULES)
    t["delta_grid"] = cuts.grid_pick(f, nmk, "delta", DELTA_GRID)
    t.update(calib.tables())
    top = (t["auc"].assign(s=lambda d: (d["taker1s_L0"] - 0.5).abs() + (d["veto_L0"] - 0.5).abs())
           .query("group != 'post hoc'").nlargest(8, "s")["var"].tolist())
    t["deciles"] = fills.decile_tables(f, top, nmk)
    WORK.mkdir(parents=True, exist_ok=True)
    for k, v in t.items():
        v.to_csv(WORK / f"{k}.csv", index=False)
    pm.to_csv(WORK / "per_market.csv", index=False)
    write(t, f, nmk)
    print("tables:", ", ".join(t), "| fills", len(f), "| venue rows", int(np.isfinite(f["v_top"]).sum()))


if __name__ == "__main__":
    main()
