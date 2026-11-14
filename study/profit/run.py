"""Profit decomposition of the latency wallets.

    python3 study/profit/run.py [--refresh]

Writes data/out/latency/profit/{summary,buckets,rebate_days}.csv. summary has
one row per wallet x family (latency classes only) with gross/net PnL, cost
and edge components (decompose.py), race position (race.py) and the
wallet-level taker-rebate rate observed on the fully covered UTC days."""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

from decompose import add_dims, buckets, summary
from extract import ROOT, build
from race import race
from rebates import match, daily_costs

OUT = ROOT / "data" / "out" / "latency" / "profit"
FAMILIES = ["btc-up-or-down-5m", "btc-up-or-down-15m", "btc-up-or-down-hourly",
            "btc-up-or-down-4h", "btc-up-or-down-daily"]
FULL_DAYS = [1791331200, 1791417600]  # 2026-10-07, 2026-10-08 UTC: in every family


def main(refresh: bool) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    cls = pd.read_csv(ROOT / "data" / "out" / "latency" / "wallets.csv",
                      usecols=["wallet", "series", "latency_class", "directional"])
    sums, bks, allf = [], [], []
    for slug in FAMILIES:
        f, mk = build(slug, refresh)
        allf.append(f[["wallet", "ts", "fee", "maker_rebate", "usd", "taker", "size",
                       "price", "pnl"]])
        f = add_dims(f)
        s = summary(f, mk).merge(race(f), on="wallet", how="left")
        s.insert(1, "series", slug)
        b = buckets(f)
        b.insert(1, "series", slug)
        sums.append(s)
        bks.append(b)
        print(slug, len(s), flush=True)
    s = pd.concat(sums, ignore_index=True).merge(cls, on=["wallet", "series"], how="left")
    s = s[s["latency_class"].fillna("none") != "none"]
    keep = set(s["wallet"])
    rd = match(daily_costs(pd.concat(allf, ignore_index=True)
                           .query("wallet in @keep")), FULL_DAYS)
    rd.to_csv(OUT / "rebate_days.csv", index=False, float_format="%.6g")
    w = rd.groupby("wallet")[["fee", "TAKER_REBATE", "MAKER_REBATE", "maker_rebate_est"]].sum()
    w["taker_rebate_rate"] = (w["TAKER_REBATE"] / w["fee"].clip(lower=1e-9))
    s = s.merge(w[["taker_rebate_rate"]].reset_index(), on="wallet", how="left")
    rate = s["taker_rebate_rate"].fillna(0).clip(upper=0.5)
    s["taker_rebate_est"] = s["fee"] * rate
    s["net_after_rebate"] = s["net"] + s["taker_rebate_est"]
    s["net_after_rebate_per_usd"] = s["net_after_rebate"] / s["usd"]
    s = s.sort_values(["series", "gross"], ascending=[True, False])
    s.to_csv(OUT / "summary.csv", index=False, float_format="%.6g")
    b = pd.concat(bks, ignore_index=True)
    b = b.merge(s[["wallet", "series"]], on=["wallet", "series"])
    b.to_csv(OUT / "buckets.csv", index=False, float_format="%.6g")
    print(len(s), "rows ->", OUT)


if __name__ == "__main__":
    main("--refresh" in sys.argv)
