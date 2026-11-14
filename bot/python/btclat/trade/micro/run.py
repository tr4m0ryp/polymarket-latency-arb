"""Micro mode's event loop: the paper bot's feeds, engine, arms and model (imported from
btclat.paper, not copied) with the paper executor swapped for the shadow + live pair.

Every 50 ms: run due paper and live jobs, mark open positions on our book, then the stops:
kill file, loss cap (locks the UTC day), a fatal venue error, the run's end. Any stop ends
the loop; the caller's Session sends cancel-all. Writes data/trade/<run>/: orders (joined
live + paper per signal), paper (shadow paper records), settle, feed (socket notes, stats)."""
from __future__ import annotations

import asyncio
import json
import time

from recorder.live import feeds as lf
from recorder.live.sink import Sink
from btclat.paper.engine.core import Engine
from btclat.paper.feeds import live
from btclat.paper.model.load import ValueModel
from research.strategy.ingest.markets import _gamma_outcome

from ..risk.limits import VENUE_MIN_SHARES
from ..risk.session import Stop
from ..venue.worker import Worker
from .executor import LiveExec, make_send
from .shadow import ShadowExec

PRIMARY, VETO = "vt_v1_m0.03_any", "vt_v1_m0.02_trigger"


def mark_positions(risk, world) -> None:
    for (slug, token), p in risk.pos.items():
        m = world.mkts.get(slug)
        if m is not None and m.book.mid() == m.book.mid():
            risk.mark[token] = m.book.mid() if p.up else 1 - m.book.mid()


def watch(risk, session, live_exec, now: float) -> str | None:
    """The reason to stop now, or None. Called every tick on the event loop."""
    if session.killed():
        return f"kill file {session.kill}"
    risk.roll(now)
    if risk.breach():
        return risk.stop_reason
    return live_exec.stop_reason


async def settle(clock, mkts: dict, sink, risk, events) -> None:
    done: set = set()
    while True:
        await asyncio.sleep(30)
        for slug, m in list(mkts.items()):
            if slug in done or clock.now() < m["end"] + 60:
                continue
            try:
                o = await asyncio.to_thread(_gamma_outcome, slug)
            except Exception as e:  # Gamma hiccup: retry next pass
                lf.note(events, clock, "error", feed="gamma_settle", slug=slug, err=repr(e)[:200])
                continue
            if o is not None:
                sink.write(clock.now_ns(), json.dumps({"slug": slug, "outcome": o, "end": m["end"]}))
                risk.resolve(slug, o)
                done.add(slug)
            elif clock.now() > m["end"] + 7200:
                done.add(slug)


async def main(a, venue, session, risk, root, clock, run: str) -> None:
    loop = asyncio.get_running_loop()
    events = live.EventsTap(Sink("feed", root=root, flush_s=0))   # "events" is the session log

    def note(kind, **kw):
        loop.call_soon_threadsafe(lambda: lf.note(events, clock, kind, **kw))

    model = ValueModel(f"v1_L{a.model_L}")
    arms = [PRIMARY] + ([VETO] if a.veto else [])
    paper_sink, orders = Sink("paper", root=root, flush_s=1.0), Sink("orders", root=root, flush_s=1.0)
    settle_sink = Sink("settle", root=root, flush_s=0)
    eng = Engine(model, paper_sink, run, L=a.latency_ms / 1000, arms=arms, now=clock.now)

    def set_balance(b: dict) -> None:
        risk.balance = b["balance"]
        lf.note(events, clock, "balance", **b)

    worker = Worker(venue, warm_s=1.0, balance_s=60.0, on_note=note,
                    on_balance=lambda b: loop.call_soon_threadsafe(set_balance, b))
    lx = LiveExec(risk, worker, make_send(venue), orders, clock.now, post=loop.call_soon_threadsafe,
                  note=note, size=VENUE_MIN_SHARES)
    eng.paper = ShadowExec(paper_sink, run, lx.on_signal, lx.on_paper_final, VENUE_MIN_SHARES, L=a.latency_ms / 1000)
    mkts: dict = {}

    def on_market(m: dict) -> None:
        eng.world.add_market(m).gaps = events.gaps.setdefault(m["slug"], [])
        mkts[m["slug"]] = m

    fans = [live.FanIn(p, eng.on_event, None, a.conns) for p in (False, True)]
    lf.note(events, clock, "trade_start", run=run, mode="micro", arms=arms, model=model.name, sha16=model.sha16,
            limits=risk.limits.__dict__, pnl=risk.pnl(), exposure=risk.exposure(), balance=risk.balance,
            orders_last_hour=risk.orders_last_hour(time.time()), venue=venue.info(), hours=a.hours)
    stop: asyncio.Future = loop.create_future()

    async def ticker() -> None:
        while not stop.done():
            await asyncio.sleep(0.05)
            try:
                now = clock.now()
                eng.paper.advance(now)
                lx.advance(now)
                mark_positions(risk, eng.world)
                why = watch(risk, session, lx, now)
            except Exception as e:  # the stops must never go unchecked: fail closed
                why = f"ticker error: {e!r}"[:300]
            if why and not stop.done():
                stop.set_result(why)

    async def sync() -> None:
        while True:
            await asyncio.sleep(300)
            await asyncio.to_thread(clock.sync)

    async def stats() -> None:
        while True:
            await asyncio.sleep(60)
            lf.note(events, clock, "stats", pnl=risk.pnl(), realised=risk.realised, exposure=risk.exposure(),
                    orders_last_hour=risk.orders_last_hour(time.time()), balance=risk.balance,
                    keepwarm_ms=worker.pings[-60:], live=lx.n, paper=eng.stats())

    worker.start()
    why = "exception"
    tasks = [asyncio.create_task(c) for c in (
        live.binance(clock, events, fans[0], a.conns), live.binance(clock, events, fans[1], a.conns),
        live.markets(clock, events, on_market, eng.on_event, None, None), ticker(), stats(), sync(),
        settle(clock, mkts, settle_sink, risk, events))]
    try:
        why = await (asyncio.wait_for(asyncio.shield(stop), a.hours * 3600) if a.hours else stop)
    except asyncio.TimeoutError:
        why = None
    finally:
        for t in tasks:
            t.cancel()
        worker.stop()
        await asyncio.to_thread(worker.join, 5.0)     # the session's cancel-all reuses its HTTP/2 client
        eng.paper.flush()
        lx.flush()
        lf.note(events, clock, "trade_stop", reason=why, pnl=risk.pnl(),
                exposure=risk.exposure(), **lx.n)
        for sk in (paper_sink, orders, settle_sink, events.sink):
            sk.close()
    if why:
        raise Stop(why)
