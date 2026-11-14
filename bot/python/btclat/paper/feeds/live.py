"""Live read-only feeds, built on the recorder's websocket pump (recorder/live/feeds.py).

- Binance spot and USD-M perp (`/public/stream`, raw @trade + @bookTicker): N parallel
  connections per stream, first arrival per update id / trade id wins (1-4 of 5 connections
  run ~100 ms late, reports/infra-plan.md). Wins per connection are counted.
- Polymarket CLOB market channel: one connection per 5m market, opened 90 s before its
  start and closed 30 s after its end (recorder/live/markets.py discovery via Gamma).
Every accepted message is passed to the engine and, when recording, written in the
recorder's format so the replay simulator can run on the same hours."""
from __future__ import annotations

import asyncio
import json
from collections import deque

from recorder.live import feeds as lf
from recorder.live import markets as lm

from . import parse


class FanIn:
    """Dedupe of one Binance stream over several connections."""

    def __init__(self, perp: bool, on_event, raw_sink, n_conns: int):
        self.perp, self.on_event, self.raw = perp, on_event, raw_sink
        self.last_u = -1
        self.seen_t: set = set()
        self.order: deque = deque()
        self.wins = [0] * n_conns
        self.dups = 0

    def tap(self, i: int) -> "_Tap":
        return _Tap(self, i)

    def take(self, i: int, t_ns: int, raw: str) -> None:
        ev, key = parse.binance(t_ns / 1e9, raw, self.perp)
        if ev is None:
            return
        if key[0] == "u":
            if key[1] <= self.last_u:
                self.dups += 1
                return
            self.last_u = key[1]
        else:
            if key[1] in self.seen_t:
                self.dups += 1
                return
            self.seen_t.add(key[1])
            self.order.append(key[1])
            if len(self.order) > 50_000:
                self.seen_t.discard(self.order.popleft())
        self.wins[i] += 1
        if self.raw is not None:
            self.raw.write(t_ns, raw)
        self.on_event(ev)


class _Tap:
    """Sink-shaped adapter handed to the recorder's pump."""

    def __init__(self, fan: FanIn, i: int):
        self.fan, self.i = fan, i

    def write(self, t_ns: int, raw: str) -> None:
        self.fan.take(self.i, t_ns, raw)


class ClobTap:
    def __init__(self, ups: dict, on_event, raw_sink):
        self.ups, self.on_event, self.raw = ups, on_event, raw_sink

    def write(self, t_ns: int, raw: str) -> None:
        if self.raw is not None:
            self.raw.write(t_ns, raw)
        for ev in parse.clob(t_ns / 1e9, raw, self.ups):
            self.on_event(ev)


class EventsTap:
    """Forwards the pumps' connect / error notes and keeps CLOB socket gaps per market."""

    def __init__(self, sink):
        self.sink = sink
        self.gaps: dict[str, list] = {}

    def write(self, t_ns: int, raw: str) -> None:
        self.sink.write(t_ns, raw)
        j = json.loads(raw)
        feed = j.get("feed", "")
        if not feed.startswith("clob:"):
            return
        g = self.gaps.setdefault(feed[5:], [])
        t = t_ns / 1e9
        if j["kind"] == "error" and (not g or g[-1][1] is not None):
            g.append([t, None])
        elif j["kind"] == "connect" and g and g[-1][1] is None:
            g[-1][1] = t


async def binance(clock, events, fan: FanIn, n: int) -> None:
    url = lf.BINANCE_FUT if fan.perp else lf.BINANCE
    name = "binance_fut" if fan.perp else "binance"
    await asyncio.gather(*(lf._pump(url, f"{name}#{i}", fan.tap(i), clock, events) for i in range(n)))


async def markets(clock, events, on_market, on_event, raw_clob, meta_sink, every: float = 5.0) -> None:
    started: set = set()
    ups: dict[str, str] = {}
    tap = ClobTap(ups, on_event, raw_clob)
    while True:
        for key in lm.wanted(clock.now()):
            if key[0] != "5m" or key in started:
                continue
            try:
                m = await asyncio.to_thread(lm.fetch, *key)
            except Exception as e:  # Gamma hiccup: retry on the next pass
                lf.note(events, clock, "error", feed="gamma", key=list(key), err=repr(e)[:200])
                continue
            if m is None:
                continue
            started.add(key)
            ups[m["up"]] = m["slug"]
            if meta_sink is not None:
                meta_sink.write(clock.now_ns(), json.dumps(m))
            on_market(m)
            asyncio.create_task(lf.clob(m, clock, events, tap))
        await asyncio.sleep(every)
