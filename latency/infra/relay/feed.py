"""Binance USD-M perp feed over N parallel connections, first arrival per update wins."""
from __future__ import annotations

import asyncio
import json
import time

import websockets

F = "wss://fstream.binance.com/public/stream?streams=btcusdt@bookTicker/btcusdt@trade"


def key_of(d: dict) -> tuple[str, int, int] | None:
    """(kind, id, venue event ms): bookTicker by update id u, trade by trade id t."""
    if d.get("e") == "bookTicker":
        return "B", int(d["u"]), int(d["E"])
    if d.get("e") == "trade":
        return "T", int(d["t"]), int(d["E"])
    return None


async def _conn(i: int, until: float, on_first, seen: set) -> None:
    while time.time() < until:
        try:
            async with websockets.connect(F, max_size=2**22, ping_interval=20) as ws:
                while time.time() < until:
                    raw = await asyncio.wait_for(ws.recv(), timeout=max(0.1, until - time.time()))
                    now = time.time_ns()
                    k = key_of(json.loads(raw).get("data", {}))
                    if k is None or (k[0], k[1]) in seen:
                        continue
                    seen.add((k[0], k[1]))
                    on_first(k, now, i)
        except (asyncio.TimeoutError, OSError, websockets.WebSocketException):
            await asyncio.sleep(0.2)


async def run(secs: float, on_first, n: int = 4) -> None:
    until, seen = time.time() + secs, set()
    await asyncio.gather(*(_conn(i, until, on_first, seen) for i in range(n)))
