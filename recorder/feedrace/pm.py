"""Polymarket 5m BTC Up/Down book on the same box and clock as the feed race (read-only).

One CLOB market-channel connection per 5m market, opened 60 s before the start, closed 10 s
after the end; all write to the `pm` sink. Token ids per market go to events-pm.jsonl
(kind=market) so the analysis can tell Up from Down."""
from __future__ import annotations

import asyncio
import json
import time
import urllib.request

import websockets

CLOB = "wss://ws-subscriptions-clob.polymarket.com/ws/market"
GAMMA = "https://gamma-api.polymarket.com/markets?slug="


def resolve(start: int) -> dict | None:
    slug = f"btc-updown-5m-{start}"
    req = urllib.request.Request(GAMMA + slug, headers={"User-Agent": "feedrace/0.1"})
    with urllib.request.urlopen(req, timeout=10) as r:
        rows = json.loads(r.read())
    if not rows:
        return None
    m = rows[0]
    out, tok = json.loads(m["outcomes"]), json.loads(m["clobTokenIds"])
    return {"slug": slug, "start": start, "up": tok[out.index("Up")], "down": tok[out.index("Down")]}


async def market(m: dict, sink, log) -> None:
    hello = json.dumps({"assets_ids": [m["up"], m["down"]], "type": "market",
                        "custom_feature_enabled": True})
    until = m["start"] + 310
    while time.time() < until:
        try:
            async with websockets.connect(CLOB, max_size=2**24, max_queue=None,
                                          compression=None, open_timeout=15) as ws:
                log(kind="connect", feed="pm", slug=m["slug"], ip=str(ws.remote_address[0]))
                await ws.send(hello)
                ping = asyncio.create_task(_ping(ws))
                try:
                    async for msg in ws:
                        sink.add(time.monotonic_ns(), time.time_ns(), msg)
                        if time.time() >= until:
                            break
                finally:
                    ping.cancel()
        except Exception as e:
            log(kind="error", feed="pm", slug=m["slug"], err=repr(e)[:300])
            await asyncio.sleep(1)


async def _ping(ws) -> None:
    while True:
        await asyncio.sleep(10)
        await ws.send("PING")


async def run(sink, log, until: float) -> None:
    started: set[int] = set()
    while time.time() < until:
        nxt = (int(time.time()) // 300 + 1) * 300
        for start in (nxt - 300, nxt):
            if start not in started and start - time.time() <= 60:
                try:
                    m = await asyncio.to_thread(resolve, start)
                except Exception as e:
                    log(kind="error", feed="pm", err="gamma " + repr(e)[:200])
                    continue
                if m:
                    started.add(start)
                    log(kind="market", feed="pm", **m)
                    asyncio.create_task(market(m, sink, log))
        await asyncio.sleep(5)
