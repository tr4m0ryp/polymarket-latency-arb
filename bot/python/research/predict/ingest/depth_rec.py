"""Short SIDE recorder for the depth study: Binance USD-M BTCUSDT diff depth at the fastest
speed Binance offers (@depth@0ms: ~26 ms batches, probed 2026-10-11; spot's fastest is
100 ms) plus the perp bookTicker on the same clock. Writes data/live_side/<day>/
fut_depth-<h>.tsv.gz; never touches data/live/ or the main recorder. Read-only, no keys.

    nohup python3 -m research.predict.ingest.depth_rec --hours 3 &"""
from __future__ import annotations

import argparse
import asyncio
import sys

from .. import ROOT

sys.path.insert(0, str(ROOT))
from recorder.live import feeds  # noqa: E402
from recorder.live.clock import Clock  # noqa: E402
from recorder.live.sink import Sink  # noqa: E402

SIDE = ROOT / "data" / "live_side"
URL = "wss://fstream.binance.com/public/stream?streams=btcusdt@depth@0ms/btcusdt@bookTicker"


async def main(hours: float) -> None:
    clock = Clock()
    events = Sink("events", root=SIDE, flush_s=0)
    until = clock.now() + hours * 3600

    async def sync():
        while True:
            ok = await asyncio.to_thread(clock.sync)
            feeds.note(events, clock, "clock", ok=ok, offset_ns=clock.offset_ns)
            await asyncio.sleep(60)
    s = asyncio.create_task(sync())
    await feeds._pump(URL, "fut_depth", Sink("fut_depth", root=SIDE), clock, events, until=until)
    s.cancel()
    Sink.close_all()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--hours", type=float, default=3.0)
    asyncio.run(main(ap.parse_args().hours))
