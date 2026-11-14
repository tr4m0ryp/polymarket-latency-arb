"""Run the recorder: `python3 -m recorder.live [--hours H]`.

Streams (data/live/<day>/<stream>-<hour>.tsv.gz): binance, binance_fut, chainlink,
clob_5m, clob_15m, markets (one JSON row per market subscribed), events
(connects, errors, clock syncs). Read-only: no keys, no orders."""
from __future__ import annotations

import argparse
import asyncio
import json
import time

from . import feeds, markets
from .clock import Clock
from .sink import Sink


async def clock_loop(clock: Clock, events: Sink, every: float = 60.0) -> None:
    while True:
        ok = await asyncio.to_thread(clock.sync)
        feeds.note(events, clock, "clock", ok=ok, offset_ns=clock.offset_ns, rtt_s=clock.rtt_s)
        await asyncio.sleep(every)


async def market_loop(clock: Clock, events: Sink, every: float = 5.0) -> None:
    started: set[tuple[str, int]] = set()
    meta = Sink("markets", flush_s=0)
    sinks = {fam: Sink(f"clob_{fam}") for fam in markets.FAMILIES}
    while True:
        for key in markets.wanted(clock.now()):
            if key in started:
                continue
            try:
                m = await asyncio.to_thread(markets.fetch, *key)
            except Exception as e:  # Gamma hiccup: retry on the next pass
                feeds.note(events, clock, "error", feed="gamma", key=list(key), err=repr(e)[:200])
                continue
            if m is None:
                continue
            started.add(key)
            meta.write(clock.now_ns(), json.dumps(m))
            asyncio.create_task(feeds.clob(m, clock, events, sinks[key[0]]))
        await asyncio.sleep(every)


async def main(hours: float | None) -> None:
    clock = Clock()
    events = Sink("events", flush_s=0)
    feeds.note(events, clock, "start", offset_ns=clock.offset_ns, hours=hours)
    tasks = [asyncio.create_task(c) for c in (
        clock_loop(clock, events), market_loop(clock, events),
        feeds.binance(clock, events), feeds.binance_fut(clock, events),
        feeds.chainlink(clock, events))]
    if hours:
        await asyncio.sleep(hours * 3600)
        feeds.note(events, clock, "stop")
        for t in tasks:
            t.cancel()
        await asyncio.sleep(0.5)
        Sink.close_all()
    else:
        await asyncio.gather(*tasks)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--hours", type=float, default=None)
    a = ap.parse_args()
    try:
        asyncio.run(main(a.hours))
    finally:
        Sink.close_all()
