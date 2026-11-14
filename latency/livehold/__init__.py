"""Live taker hold: why missed FAK orders were the good ones (reports/live-hold.md).

Joins the live micro runs' order logs (data/trade/<run>/) with the Dublin paper box's CLOB
tape (same region, same NTP source) to replay each order's book from send to ack and after.
Asks: does a wider or edge-scaled limit turn the missed winners into fills, and what does
the surviving depth look like. Read-only research: no orders.

    python3 -m latency.livehold.tape      # filter the tape to our tokens (once)
    python3 -m latency.livehold.run       # sweep limits, write data/out/livehold/"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUNS = ("dublin-micro-20261013", "dublin-micro-20261013b")
TRADE = ROOT / "data" / "trade"
TAPE = TRADE / "tape"            # clob_5m-<hour>.tsv.gz copied from the paper box raw/
OUT = ROOT / "data" / "out" / "livehold"
