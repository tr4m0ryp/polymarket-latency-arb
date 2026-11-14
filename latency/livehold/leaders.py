"""Leaders A and B on the same day and tape: taker share, match timing, price vs book, markout.

Pulls their Data API trades (all, and taker-only) for the hours our live runs covered, joins
each fill to the tape's `last_trade_price` by transaction hash for the venue match time, and
replays their token's book there. Needs the tape re-filtered to their tokens (`--tape`).

    PYTHONPATH=. python3 -m latency.livehold.leaders [--fetch] [--tape]"""
from __future__ import annotations

import argparse
import gzip
import json
import subprocess
import time
import urllib.request

import pandas as pd

from . import OUT, TAPE

LEADERS = {"A": "0xc53375ff94e96100f2b30a4b5775db35218d69a9", "B": "0x3048d65321be3497164cdfc2996f94f98a2e7537"}
T0, T1 = 1791900000, 1791921600          # 2026-10-13 14:00-20:00 UTC, the tape we hold
API = "https://data-api.polymarket.com/trades?user={u}&limit=500&offset={o}&takerOnly={t}"


def fetch() -> pd.DataFrame:
    rows = []
    for name, w in LEADERS.items():
        for taker in ("true", "false"):
            for off in range(0, 10000, 500):
                req = urllib.request.Request(API.format(u=w, o=off, t=taker), headers={"User-Agent": "btclat-research"})
                a = json.load(urllib.request.urlopen(req, timeout=30))
                if not isinstance(a, list) or not a:
                    break
                rows += [dict(x, who=name, taker_only=taker == "true") for x in a if T0 - 600 <= x["timestamp"] <= T1]
                if min(x["timestamp"] for x in a) < T0 - 600:
                    break
                time.sleep(0.3)
    df = pd.DataFrame(rows)
    keep = ["who", "taker_only", "slug", "asset", "outcome", "side", "price", "size", "timestamp", "transactionHash"]
    df = df[keep].drop_duplicates()
    OUT.mkdir(parents=True, exist_ok=True)
    df.to_pickle(OUT / "leaders_trades.pkl")
    return df


def tape(df: pd.DataFrame):
    """Keep tape messages for the leaders' tokens (all hours), as data/trade/tape/leaders.tsv.gz."""
    toks = sorted(set(df["asset"]))
    tf = TAPE / "leader_tokens.txt"
    tf.write_text("\n".join(toks) + "\n")
    srcs = " ".join(str(p) for p in sorted(TAPE.glob("clob_5m-*.tsv.gz")))
    subprocess.run(f"zcat {srcs} | grep -F -f {tf} | gzip -1 > {TAPE / 'leaders.tsv.gz'}", shell=True, check=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fetch", action="store_true")
    ap.add_argument("--tape", action="store_true")
    a = ap.parse_args()
    df = fetch() if a.fetch else pd.read_pickle(OUT / "leaders_trades.pkl")
    print(df.groupby(["who", "taker_only"]).size())
    if a.tape:
        tape(df)


if __name__ == "__main__":
    main()
