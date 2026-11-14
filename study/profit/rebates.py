"""Rebate payouts from the Data API, matched to the fees the fills imply.

/activity?user=<w>&type=TAKER_REBATE|MAKER_REBATE lists daily payouts (paid
at ~00:10 UTC for the previous UTC day). For the days fully covered by the
fill data the implied taker-rebate rate is
    payout(day) / sum of our computed taker fees(day, all BTC families).
A rate that matches a tier (3/8/18/32/44/50 %) says the wallet's fees are all
in the BTC families; a rate above 50 % says it also pays fees elsewhere."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "bot" / "python"))  # btclat.api lives under bot/python
from btclat.api.http import DATA, get  # noqa: E402

CACHE = ROOT / "data" / "cache" / "latency_profit" / "activity"
TYPES = ("TAKER_REBATE", "MAKER_REBATE", "REWARD")
DAY = 86400


def payouts(wallet: str, refresh: bool = False) -> pd.DataFrame:
    CACHE.mkdir(parents=True, exist_ok=True)
    p = CACHE / f"{wallet}.json"
    if p.exists() and not refresh:
        rows = json.loads(p.read_text())
    else:
        rows = []
        for t in TYPES:
            rows += get(DATA, "/activity", {"user": wallet, "type": t, "limit": 500}) or []
        p.write_text(json.dumps(rows))
    if not rows:
        return pd.DataFrame(columns=["wallet", "type", "day", "usdc"])
    d = pd.DataFrame(rows)
    # payout at ~00:10 UTC belongs to the UTC day before it
    d["day"] = (d["timestamp"] - 3600) // DAY * DAY
    return pd.DataFrame({"wallet": wallet, "type": d["type"], "day": d["day"],
                         "usdc": d["usdcSize"].astype(float)})


def daily_costs(fills: pd.DataFrame) -> pd.DataFrame:
    """fills: concatenated per-family frames (wallet, ts, fee, maker_rebate, usd, taker)."""
    x = fills.assign(day=fills["ts"] // DAY * DAY,
                     taker_usd=fills["usd"] * fills["taker"],
                     wv=fills["size"] * (1 - fills["price"]) * 2.3 * fills["taker"])
    return (x.groupby(["wallet", "day"])
            .agg(fee=("fee", "sum"), maker_rebate_est=("maker_rebate", "sum"),
                 taker_usd=("taker_usd", "sum"), wv=("wv", "sum"), gross=("pnl", "sum"))
            .reset_index())


def match(costs: pd.DataFrame, days: list[int]) -> pd.DataFrame:
    pay = pd.concat([payouts(w) for w in costs["wallet"].unique()], ignore_index=True)
    piv = (pay.pivot_table(index=["wallet", "day"], columns="type", values="usdc",
                           aggfunc="sum").reset_index())
    m = costs[costs["day"].isin(days)].merge(piv, on=["wallet", "day"], how="left")
    for t in TYPES:
        if t not in m:
            m[t] = 0.0
    m[list(TYPES)] = m[list(TYPES)].fillna(0.0)
    m["taker_rebate_rate"] = m["TAKER_REBATE"] / m["fee"].clip(lower=1e-9)
    m["maker_rebate_ratio"] = m["MAKER_REBATE"] / m["maker_rebate_est"].clip(lower=1e-9)
    return m
