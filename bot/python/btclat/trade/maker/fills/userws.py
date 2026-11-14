"""The CLOB user channel: our own trades and order updates, pushed within milliseconds of the
match (docs.polymarket.com, websocket "user" channel). Subscribe with the L2 API credentials;
every `trade` / `order` event goes to `on_msg` (fills/settle.py `Settle.on_user`).

It is the fast path only: the GET /data/trades poll (fills/settle.py) is the backstop, so a
dropped socket costs seconds of fill latency, never a missed fill. Reconnects with backoff;
connects and drops are logged through `note`."""
from __future__ import annotations

import asyncio
import json

USER = "wss://ws-subscriptions-clob.polymarket.com/ws/user"
PING_S = 10.0


def hello(api: dict, markets: list[str] | None = None) -> str:
    return json.dumps({"auth": {"apiKey": api["key"], "secret": api["secret"], "passphrase": api["passphrase"]},
                       "type": "user", "markets": list(markets or [])})


def events(raw: str) -> list[dict]:
    """The event dicts of one frame (a frame may carry one event or a list; PONG carries none)."""
    if not raw or raw[0] not in "[{":
        return []
    try:
        j = json.loads(raw)
    except ValueError:
        return []
    return [x for x in (j if isinstance(j, list) else [j]) if isinstance(x, dict) and x.get("event_type")]


async def run(api: dict, on_msg, note, url: str = USER, connect=None) -> None:
    """Forever (until cancelled): subscribe, hand every event to on_msg, reconnect on error."""
    if connect is None:
        import websockets
        connect = websockets.connect
    backoff = 1.0
    while True:
        try:
            async with connect(url, max_size=2**22, ping_interval=20) as ws:
                await ws.send(hello(api))
                note("user_ws", state="connected")
                backoff = 1.0
                pinger = asyncio.create_task(_ping(ws))
                try:
                    async for raw in ws:
                        for ev in events(raw if isinstance(raw, str) else raw.decode()):
                            on_msg(ev)
                finally:
                    pinger.cancel()
            note("user_ws", state="closed")
        except asyncio.CancelledError:
            raise
        except Exception as e:  # the trade poll covers the gap; keep trying
            note("user_ws", state="error", err=repr(e)[:200])
        await asyncio.sleep(backoff)
        backoff = min(backoff * 2, 30.0)


async def _ping(ws) -> None:
    while True:
        await asyncio.sleep(PING_S)
        await ws.send("PING")
