"""Websocket readers. Each one logs every message with its receipt time and
reconnects on error; gaps are written to the `events` stream."""
from __future__ import annotations

import asyncio
import json

import websockets

from .clock import Clock
from .sink import Sink

BINANCE = "wss://stream.binance.com:9443/stream?streams=btcusdt@trade/btcusdt@bookTicker"
# USD-M routed endpoints (tested 2026-10-10): /public carries @trade and @bookTicker, /market
# carries @aggTrade; the legacy /stream path silently drops @aggTrade. Raw @trade is used: one
# message per fill with E == T, while @aggTrade is stamped ~150 ms after its trade time.
BINANCE_FUT = "wss://fstream.binance.com/public/stream?streams=btcusdt@trade/btcusdt@bookTicker"
RTDS = "wss://ws-live-data.polymarket.com"
CLOB = "wss://ws-subscriptions-clob.polymarket.com/ws/market"


def note(events: Sink, clock: Clock, kind: str, **kw) -> None:
    events.write(clock.now_ns(), json.dumps({"kind": kind, **kw}))


async def _pinger(ws, every: float) -> None:
    while True:
        await asyncio.sleep(every)
        await ws.send("PING")


async def _pump(url: str, name: str, sink: Sink, clock: Clock, events: Sink,
                hello: str | None = None, ping_s: float | None = None,
                until: float | None = None) -> None:
    """Read `url` into `sink` until `until` (corrected epoch s) or forever."""
    backoff = 1.0
    while until is None or clock.now() < until:
        pinger = None
        try:
            async with websockets.connect(url, max_size=2**24, max_queue=4096, ping_interval=20) as ws:
                note(events, clock, "connect", feed=name)
                if hello:
                    await ws.send(hello)
                if ping_s:
                    pinger = asyncio.create_task(_pinger(ws, ping_s))
                backoff = 1.0
                while until is None or clock.now() < until:
                    left = None if until is None else max(0.1, until - clock.now())
                    try:
                        msg = await asyncio.wait_for(ws.recv(), timeout=left)
                    except asyncio.TimeoutError:
                        break
                    t = clock.now_ns()
                    if isinstance(msg, bytes):
                        msg = msg.decode()
                    if msg in ("PONG", ""):
                        continue
                    sink.write(t, msg)
        except Exception as e:  # network errors of any kind: log, back off, retry
            note(events, clock, "error", feed=name, err=repr(e)[:300])
            await asyncio.sleep(backoff)
            backoff = min(30.0, backoff * 2)
        finally:
            if pinger:
                pinger.cancel()
    note(events, clock, "done", feed=name)


async def binance(clock: Clock, events: Sink) -> None:
    await _pump(BINANCE, "binance", Sink("binance"), clock, events)


async def binance_fut(clock: Clock, events: Sink) -> None:
    """USD-M perpetual: tests whether the book follows futures before spot."""
    await _pump(BINANCE_FUT, "binance_fut", Sink("binance_fut"), clock, events)


async def chainlink(clock: Clock, events: Sink) -> None:
    sub = {"action": "subscribe", "subscriptions": [
        {"topic": "crypto_prices_chainlink", "type": "*", "filters": '{"symbol":"btc/usd"}'}]}
    await _pump(RTDS, "chainlink", Sink("chainlink"), clock, events,
                hello=json.dumps(sub), ping_s=5)


async def clob(m: dict, clock: Clock, events: Sink, sink: Sink, tail_s: int = 30) -> None:
    """One connection per market, from discovery until end + tail_s."""
    hello = json.dumps({"assets_ids": [m["up"], m["down"]], "type": "market",
                        "custom_feature_enabled": True})
    await _pump(CLOB, f"clob:{m['slug']}", sink, clock, events, hello=hello,
                ping_s=10, until=m["end"] + tail_s)
