"""Write backrun/results.json: window, per-delay tables per arm, live calibration, bounds.

    python -m backrun.report.run"""
from __future__ import annotations

import json

import pandas as pd

from .. import (ARMS, CLIP, DELAYS, DUBLIN, FEE_CPD, G_README, GATE, LONDON, OUT, PRIMARY, RESULTS,
                TIERS, VOLUME)
from .bounds import bounds
from .live import live
from .tables import arm_table, by_day

LEDGER = {  # quoted from the private ledger (notes/btc-latency.md), after-fee 10 s markouts
    "run_b": "155 FAK orders, 22 fills (14% live vs 61% paper on the same orders)",
    "markout": "Live 10 s markout -4.1 c/$ [-13, +8]; paper on all sent +11.6 [+5.7, +16.9]",
    "pooled": "orders that missed live would have earned +16.8 c/$, orders that filled -5.2",
    "hold": "crypto taker delay = 150 ms; decision-to-match 330 (Dublin) / 165 (London) ms"}


def main():
    df = pd.read_parquet(OUT / "rows.parquet")
    win = json.loads((OUT / "window.json").read_text())
    lv = live()
    arms = {a: arm_table(g) for a, g in df.groupby("arm")}
    prim = {r["delay_ms"]: r for r in arms[PRIMARY]}
    b = lv["dublin-micro-20261013b"]
    d_row = prim[DUBLIN]
    calib = {
        "replay_delay_ms": DUBLIN,
        "replay_fill_rate_count": d_row["fill_rate_count"]["est"],
        "replay_fill_rate_dollars": d_row["fill_rate_dollars"]["est"],
        "replay_mk10_filled_gross_cpd": d_row["mk10_filled_cpd"],
        "live_fill_rate_count_limit_seen_plus_2c": b["fill_rate_count"],
        "live_fill_rate_count_limit_seen": b["fill_rate_count_limit_seen"],
        "live_fill_rate_dollars": b["fill_rate_dollars"]["est"],
        "live_mk10_filled_gross_cpd": b["gross_mk10_cpd"],
        "live_mk10_filled_net_cpd": b["net_mk10_cpd"],
        "replay_over_live_fill_count": round(d_row["fill_rate_count"]["est"] / b["fill_rate_count"], 2),
        "replay_over_live_fill_dollars": round(
            d_row["fill_rate_dollars"]["est"] / b["fill_rate_dollars"]["est"], 2),
        "caveat": "live arm = model-veto taker (vt_v1_m0.03_any), 5 shares, limit seen + 2 c; "
                  "replay arm = plain spot-move trigger, $12, limit = seen"}
    res = {
        "data": {"recording": "48 h Dublin paper recording (paper/dublin-20261012)",
                 "t_first_unix": win["t_first"], "t_last_unix": win["t_last"],
                 "hours": round(win["hours_span"], 2), "markets_5m_listed": int(win["markets_listed"]),
                 "markets_with_orders": int(df[df["arm"] == PRIMARY]["slug"].nunique()),
                 "book": "CLOB L2 events, venue stamps at 1 ms, replayed on a 5 ms grid",
                 "btc_feed": "Binance spot trades + bookTicker, USD-M perp bookTicker (receipt clock)",
                 "outcomes": "Gamma resolved outcomes"},
        "trigger": {"primary": PRIMARY, "arms": {k: dict(zip(("src", "win_s", "thr_bp", "refr_s"), v))
                                                 for k, v in ARMS.items()},
                    "gate": GATE, "clip_dollars": CLIP, "limit": "ask seen at the decision (i = 0)",
                    "source": "bot/python/research/strategy/eval/arms/sweep1.py (theirs_spot)"},
        "delays_ms": list(DELAYS), "london_ms": LONDON, "dublin_ms": DUBLIN,
        "tables": arms, "by_day_primary_165": by_day(df[df["arm"] == PRIMARY], LONDON),
        "live": lv, "ledger_quotes": LEDGER, "calibration": calib,
        "readme": {"g_cpd": G_README, "fee_cpd": round(FEE_CPD, 3), "volume_30d": VOLUME,
                   "tiers": list(TIERS)},
        "bounds": bounds(prim[LONDON], b),
        "bounds_sensitivity_spot_1bp": bounds({r["delay_ms"]: r for r in arms["spot_1bp"]}[LONDON], b)}
    RESULTS.write_text(json.dumps(res, indent=1))
    for a, rows in arms.items():
        print(a)
        for r in rows:
            f = lambda x: "%+.2f [%+.2f, %+.2f]" % (x["est"], x["lo"], x["hi"])   # noqa: E731
            print(" d=%3d n=%d fill %.3f / $ %.3f | all %s | filled %s | missed %s | adv %s | mk10f %s" % (
                r["delay_ms"], r["orders"], r["fill_rate_count"]["est"], r["fill_rate_dollars"]["est"],
                f(r["edge_all_cpd"]), f(r["edge_filled_cpd"]), f(r["edge_missed_cpd"]),
                f(r["adverse_selection_cpd"]), f(r["mk10_filled_cpd"])))
    print(json.dumps(calib, indent=1))
    for k, v in res["bounds"].items():
        print(k, v["fill_rate_dollars"], v["gross_edge_cpd"], v["net_30d_by_tier_pct"],
              v["order_flow_multiple_for_full_volume"])


if __name__ == "__main__":
    main()
