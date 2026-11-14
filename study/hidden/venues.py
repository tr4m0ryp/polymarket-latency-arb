"""Short side recorder for venues the main recorder lacks (read-only, public feeds).

    python3 study/hidden/venues.py --hours 4

Streams, same line format as recorder.live (`<recv_ns>\\t<raw json>`, SNTP-corrected receipt):
  perp      Binance USD-M BTCUSDT raw trades + bookTicker (the fixed /public endpoint)
  coinbase  Coinbase Exchange BTC-USD matches + ticker
  okx       OKX BTC-USDT-SWAP and BTC-USDT trades + tick-by-tick best bid/offer
  bybit     Bybit linear BTCUSDT trades + top of book
Files: data/cache/hidden/venues/<day>/<stream>-<hour>.tsv.gz. Tests hypothesis 3 of
reports/hidden-trigger.md: does another venue lead the 5m leaders' no-move fires?"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

import websockets

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from recorder.live.clock import Clock  # noqa: E402
from recorder.live.sink import Sink  # noqa: E402

VROOT = ROOT / "data" / "cache" / "hidden" / "venues"
FEEDS = {
    "perp": ("wss://fstream.binance.com/public/stream?streams=btcusdt@trade/btcusdt@bookTicker",
             None, None),
    "coinbase": ("wss://ws-feed.exchange.coinbase.com",
                 {"type": "subscribe", "product_ids": ["BTC-USD"], "channels": ["matches", "ticker"]},
                 None),
    "okx": ("wss://ws.okx.com:8443/ws/v5/public",
            {"op": "subscribe", "args": [{"channel": "trades", "instId": "BTC-USDT-SWAP"},
                                         {"channel": "bbo-tbt", "instId": "BTC-USDT-SWAP"},
                                         {"channel": "trades", "instId": "BTC-USDT"}]},
            "ping"),
    "bybit": ("wss://stream.bybit.com/v5/public/linear",
              {"op": "subscribe", "args": ["publicTrade.BTCUSDT", "orderbook.1.BTCUSDT"]},
              json.dumps({"op": "ping"})),
}


async def pinger(ws, payload: str, every: float = 15.0) -> None:
    while True:
        await asyncio.sleep(every)
        await ws.send(payload)


async def pump(name: str, clock: Clock, until: float, events: Sink) -> None:
    url, hello, ping = FEEDS[name]
    sink, backoff = Sink(name, root=VROOT), 1.0
    while clock.now() < until:
        task = None
        try:
            async with websockets.connect(url, max_size=2**24, max_queue=4096, ping_interval=20) as ws:
                events.write(clock.now_ns(), json.dumps({"kind": "connect", "feed": name}))
                if hello:
                    await ws.send(json.dumps(hello))
                if ping:
                    task = asyncio.create_task(pinger(ws, ping))
                backoff = 1.0
                while clock.now() < until:
                    try:
                        msg = await asyncio.wait_for(ws.recv(), timeout=max(0.1, until - clock.now()))
                    except asyncio.TimeoutError:
                        break
                    t = clock.now_ns()
                    if isinstance(msg, bytes):
                        msg = msg.decode()
                    if msg not in ("pong", "PONG", ""):
                        sink.write(t, msg)
        except Exception as e:  # log, back off, retry
            events.write(clock.now_ns(), json.dumps({"kind": "error", "feed": name, "err": repr(e)[:300]}))
            await asyncio.sleep(backoff)
            backoff = min(30.0, backoff * 2)
        finally:
            if task:
                task.cancel()


async def clock_loop(clock: Clock, events: Sink) -> None:
    while True:
        ok = await asyncio.to_thread(clock.sync)
        events.write(clock.now_ns(), json.dumps({"kind": "clock", "ok": ok, "offset_ns": clock.offset_ns}))
        await asyncio.sleep(60)


async def main(hours: float) -> None:
    clock = Clock()
    events = Sink("venue_events", root=VROOT, flush_s=0)
    until = clock.now() + hours * 3600
    ck = asyncio.create_task(clock_loop(clock, events))
    await asyncio.gather(*(pump(n, clock, until, events) for n in FEEDS))
    ck.cancel()
    Sink.close_all()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--hours", type=float, default=4.0)
    asyncio.run(main(ap.parse_args().hours))
