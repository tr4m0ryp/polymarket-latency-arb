"""Price-trigger study of the latency_arb bots in BTC 5m and 15m.

    python3 study/trigger/run.py

Reuses the Binance 1 s cache (data/cache/prices/binance_btcusdt_1s/). Writes
one CSV per table to data/out/latency/trigger/ and the write-up to
data/out/latency/trigger.md (report.py)."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import edge  # noqa: E402
import lag  # noqa: E402
import rule  # noqa: E402
from frame import ROOT, bots, fill_frame, second_grid  # noqa: E402
from report import write_report  # noqa: E402

OUT = ROOT / "data" / "out" / "latency"
FAMILIES = ["btc-up-or-down-5m", "btc-up-or-down-15m"]
TOP = 6


def study(slug: str) -> dict:
    f, mk, sp = fill_frame(slug)
    B = bots(slug)
    g = second_grid(f, mk, sp, slug, set(B))
    tk = f[(f["taker"] == 1) & f["live"]]
    who = {w: tk["wallet"].eq(w) for w in B[:TOP]}
    who["all_bots"] = tk["wallet"].isin(B)
    who["other_takers"] = ~tk["wallet"].isin(B)
    T, ret, ys = lag.series(f, g, sp, B, B[:3])
    ev_tab, ev_stats = lag.event_study(T, sp, ys, g)
    fc, gc = rule.fire_curve(g, sp, tk[tk["wallet"].isin(B[:5])])
    r = {"bots": B, "markets": len(mk),
         "spot_outcome_agree": f.attrs["spot_outcome_agree"],
         "btc_level": float(np.nanmedian(f["spot"])),
         "bot_table": edge.bot_table(tk, who),
         "decompose": edge.decompose(f, mk, B[:TOP]),
         "edge_by_move": edge.edge_by_move(tk[who["all_bots"]]),
         "feature_accuracy": rule.feature_accuracy(tk, who),
         "lag_accuracy": rule.lag_accuracy(tk, who, sp),
         "fire_curve": fc, "gap_curve": gc,
         "xcorr": lag.xcorr(ret, ys), "event_study": ev_tab, "event_stats": ev_stats}
    d = OUT / "trigger"
    d.mkdir(parents=True, exist_ok=True)
    tag = slug.removeprefix("btc-up-or-down-")
    for k, v in r.items():
        if hasattr(v, "to_csv"):
            v.to_csv(d / f"{tag}_{k}.csv", float_format="%.6g")
    print(f"{slug}: {len(B)} bots, {len(tk)} live taker fills, events {ev_stats['n_events']}", flush=True)
    return r


def main() -> None:
    res = {slug: study(slug) for slug in FAMILIES}
    write_report(res, OUT / "trigger.md")


if __name__ == "__main__":
    main()
