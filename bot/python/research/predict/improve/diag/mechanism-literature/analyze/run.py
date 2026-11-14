"""Tables of the event study and the calibration rows, printed as markdown and saved as CSV
under data/out/predict/improve/diag-mechanism-literature/ (the write-up is
data/out/predict/improve/diag-mechanism-literature.md, written by hand from these).

    python3 research/predict/improve/diag/mechanism-literature analyze"""
from __future__ import annotations

import numpy as np
import pandas as pd

from research.predict.report.md import md
from .. import OUT, SEALED, WORK
from ..data.guard import assert_allowed
from .calib import calib_tables
from .placebo import placebo_table
from .stats import deciles
from .tables import by, clean, edges, ols, spearman, split

DIR = OUT / "diag-mechanism-literature"
KEEP = ["events", "mkts", "|c0| c", "spread c", "feed lag ms", "feed p90 ms", "requote ms", "P(<150ms)",
        "P(quote alive at our match)", "ended by trade", "rival prints 100-300ms", "rival prints 0.3-1s",
        "pre-flow", "v seen 1s c", "v L0 1s c", "v L0 10s c", "slip L0 c", "persist 1s", "persist 10s",
        "pass-through 3s"]


def show(title: str, t: pd.DataFrame, name: str) -> None:
    t.to_csv(DIR / f"{name}.csv", index=False)
    print(f"\n### {title}\n")
    print(md(t, 3))


def main() -> None:
    np.seterr(all="ignore")
    DIR.mkdir(parents=True, exist_ok=True)
    raw = pd.read_pickle(WORK / "events.pkl")
    assert_allowed(raw["start"], "events")
    assert raw["T0"].max() < SEALED
    if "placebo" not in raw:
        raw["placebo"] = 0
    ev = clean(raw[raw["placebo"] == 0])
    print("events", len(ev), "markets", ev["m"].nunique(), ev.groupby("window").size().to_dict())
    for col, name in (("cvol30", "fair-value churn cvol30 (c / 30 s)"), ("pmsg10", "perp msgs / s"),
                      ("pmtr30", "Polymarket prints / 30 s"), ("lag_feed", "our perp feed lag (s)")):
        b = deciles(ev[col], 5)
        ev[f"q_{col}"] = b
        lab = {k: f"Q{k + 1} {e}" for k, e in zip(sorted(b.unique()), edges(ev, col, b))}
        show(f"by quintile of {name}", by(ev, f"q_{col}", lab)[[f"q_{col}"] + KEEP], f"by_{col}")
    ev["surprise"] = ev["abs_c0"] / np.maximum(ev["cvol30"], 0.5)
    ev["compress"] = ev["Tspan"] / np.maximum(ev["tspan"], 1e-3) if "Tspan" in ev else np.nan
    for col, name in (("size0", "stale-level size (shares)"), ("surprise", "move / 30 s churn"),
                      ("compress", "Binance span / receipt span of the move"), ("lag_spot", "spot feed lag (s)")):
        if col not in ev or ev[col].isna().all():
            continue
        b = deciles(ev[col], 5)
        ev[f"q_{col}"] = b
        lab = {k: f"Q{k + 1} {e}" for k, e in zip(sorted(b.unique()), edges(ev, col, b))}
        show(f"by quintile of {name}", by(ev, f"q_{col}", lab)[[f"q_{col}"] + KEEP], f"by_{col}")
    if raw["placebo"].any():
        for col in ("cvol30", "pmsg10"):
            show(f"events vs matched quiet instants, by {col} quintile (event cut points)",
                 placebo_table(raw, col), f"placebo_{col}")
    order = {"select": 0, "dev3": 1, "test3r1": 2, "ext": 3}
    ev["w"] = ev["window"].map(order)
    show("by window", by(ev, "w", {v: k for k, v in order.items()})[["w"] + KEEP], "by_window")
    lagged = ev["lag_feed"] > 0.13
    show("post-hold value by window, our perp feed lag <= 130 ms vs > 130 ms", split(ev, "window", lagged), "split_window_feed")
    show("post-hold value by cvol30 quintile, feed ok vs lagged", split(ev, "q_cvol30", lagged), "split_cvol_feed")
    ev["size_b"] = pd.cut(ev["abs_c0"], [1, 1.5, 2.5, 5, 1e9], labels=False, right=False)
    show("by event size |c0|", by(ev, "size_b", {0: "1-1.5c", 1: "1.5-2.5c", 2: "2.5-5c", 3: ">5c"})
         [["size_b"] + KEEP], "by_size")
    ev["l_cvol"], ev["l_pmsg"], ev["l_size0"] = np.log1p(ev["cvol30"]), np.log(ev["pmsg10"] + 1), np.log1p(ev["size0"])
    ev["l_abs_c0"], ev["l_pmtr"] = np.log(ev["abs_c0"]), np.log1p(ev["pmtr30"])
    xs = ["l_cvol", "l_pmsg", "l_pmtr", "lag_feed", "l_abs_c0", "spr0", "l_size0", "secs_left"]
    ys = ["lag_q", "snipe", "beat0", "v0_1", "vseen_1", "front", "per10", "rival_early", "lag_feed"]
    sp = spearman(ev, ys, xs)
    sp.insert(0, "y", sp.index)
    show("Spearman, outcome (row) vs state (column)", sp, "spearman")
    for y in ("lag_q", "v0_1", "beat0"):
        r = ols(ev.assign(lag_q=ev["lag_q"].clip(upper=3.0)), y, xs).round(4)
        r.insert(0, "x", r.index)
        show(f"OLS {y} on standardized state (market-bootstrap CI)", r, f"ols_{y}")
    if (WORK / "calib.pkl").exists():
        for title, t, name in calib_tables(pd.read_pickle(WORK / "calib.pkl")):
            show(title, t, name)


if __name__ == "__main__":
    main()
