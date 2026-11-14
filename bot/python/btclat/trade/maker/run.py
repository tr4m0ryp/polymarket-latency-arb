"""Maker mode's event loop: the paper bot's feeds, state, features and frozen model (imported
from btclat.paper) drive the maker rule (decide.py; `--rule` / `--hyst`: rules.py); its targets
go to the order manager, which quotes through live hedged ops or dry simulated ones.

Every 50 ms: the manager's guards (time left, stale decisions, socket gaps, retries, GTD
expiry), crossing fills (dry), fill lookups (live), due 10 s marks, position marks, then the
stops: kill file, loss cap (locks the UTC day; dry: logged as a would-stop only), a manager
stop (fatal reject, unknown insert, unconfirmed cancel), the run's end. Any stop ends the loop:
the manager cancels each quote, the caller's Session sends cancel-all. Live runs settle every
order's fills from lookups, the trade records and the user channel (fills/settle.py) and end
with a `reconcile` line (booked vs the venue's trades). `--record` also writes
the raw feeds (raw/, recorder format) so the replay simulator can run on the same markets
(report/maker/sim.py)."""
from __future__ import annotations

import asyncio
import time

from recorder.live import feeds as lf
from recorder.live.sink import Sink
from btclat.paper.feeds import live
from btclat.paper.model.load import ValueModel

from ..micro.run import mark_positions, settle, watch
from ..risk.session import Stop
from . import arm, rules
from .decide import MakerEngine
from .fills.infer import Infer
from .fills import userws
from .fills.live import LiveFills
from .fills.reconcile import reconcile
from .fills.settle import Settle
from .fills.trades import TradeTap
from .log import MakerLog
from .ops.dry import DryOps
from .ops.hedge import Hedge
from .ops.live import LiveOps
from .orders.manager import OrderManager
from .orders.risk import MakerRisk

STREAMS = ("quotes", "ops", "fills", "infer")
FINAL_WAIT_S = 2.0          # after the last cancels: matches racing them reach the trade records


def build(a, venue, risk_book, limits, root, clock, loop, events, hedge=None) -> dict:
    """Engine, manager, ops, fills and log wired together (no sockets)."""
    sinks = {n: Sink(n, root=root, flush_s=1.0) for n in STREAMS}

    def note(kind, **kw):
        loop.call_soon_threadsafe(lambda: lf.note(events, clock, kind, **kw))

    model = ValueModel(arm.MODEL)
    rule = rules.of(getattr(a, "rule", "frozen"), getattr(a, "hyst", 0.0))
    w: dict = {}

    def book_of(slug: str):
        m = w["eng"].world.mkts.get(slug)
        return m.book if m is not None else None
    sender = getattr(a, "sender", "thread")
    if a.dry:
        ops = DryOps(loop.call_later, clock.now, book_of, L=a.dry_ms / 1000)
    elif sender == "thread":
        ops = LiveOps(venue, hedge or Hedge(clock.now_ns, limits.fanout), loop.call_soon_threadsafe, note)
    else:                                   # the sender process (send/): sign + send off this GIL
        from .send import RemoteOps
        from .send.child import live_spec
        ops = RemoteOps(venue, hedge or Hedge(clock.now_ns, limits.fanout), loop.call_soon_threadsafe, note, loop,
                        live_spec(venue, clock, limits.fanout), mode=sender)
    log = MakerLog(sinks, clock.now_ns, book_of, note=lambda kind, **kw: lf.note(events, clock, kind, **kw), dry=a.dry)
    mrisk = MakerRisk(risk_book, limits, dry=a.dry)
    mgr = OrderManager(ops, mrisk, log, clock.now, otype=a.order_type)
    mgr.gaps, mgr.book_of, mgr.far = events.gaps, book_of, bool(getattr(a, "far", False))
    log.pulled = mgr.pulled
    infer = Infer(mgr.fill if a.dry else log.infer, book_of, xhold=a.hold)
    settle = None
    if a.dry:
        mgr.watchers = [infer]
    else:
        fl = LiveFills(ops, mgr, clock.now, log)
        settle = Settle(ops, mgr, fl, clock.now, note=log.note)
        mgr.watchers = [infer, fl, settle]
    eng = w["eng"] = MakerEngine(model, mgr.on_quote, on_book=infer.on_book, now=clock.now, rule=rule)
    tap = TradeTap(lambda tr: [x.on_trade(tr) for x in mgr.watchers],
                   raw=Sink("clob_5m", root=root / "raw") if a.record else None)
    return {"model": model, "rule": rule, "mrisk": mrisk, "ops": ops, "log": log, "mgr": mgr, "infer": infer, "eng": eng, "tap": tap,
            "sinks": sinks, "settle": settle}


async def main(a, venue, session, risk, root, clock, run: str, limits, hedge=None) -> None:
    loop = asyncio.get_running_loop()
    raw = root / "raw"
    events = live.EventsTap(Sink("events", root=raw, flush_s=0) if a.record else Sink("feed", root=root, flush_s=0))
    w = build(a, venue, risk, limits, root, clock, loop, events, hedge)
    eng, mgr, ops, log, tap = w["eng"], w["mgr"], w["ops"], w["log"], w["tap"]
    settle_sink = Sink("settle", root=root, flush_s=0)
    meta_sink = Sink("markets", root=raw, flush_s=0) if a.record else None
    mkts: dict = {}

    def on_market(m: dict) -> None:
        eng.world.add_market(m).gaps = events.gaps.setdefault(m["slug"], [])
        mkts[m["slug"]] = m
        tap.add_market(m)

    rec = (lambda name: Sink(name, root=raw)) if a.record else (lambda name: None)
    fans = [live.FanIn(p, eng.on_event, rec("binance_fut" if p else "binance"), a.conns) for p in (False, True)]
    rule, mrisk = w["rule"], w["mrisk"]
    lf.note(events, clock, "trade_start", run=run, mode="maker", dry=a.dry, arm=rule.name, params=rule.params,
            rule=rule.kind, h=rule.h, money_caps="would-skip (dry)" if a.dry else "applied",
            model=w["model"].name, sha16=w["model"].sha16, limits=limits.__dict__, loss_cap=risk.limits.loss_cap,
            pnl=risk.pnl(), exposure=risk.exposure(), balance=risk.balance, hours=a.hours, dry_ms=a.dry_ms,
            hold=a.hold, record=a.record, order_type=a.order_type, venue=venue.info(),
            sender=getattr(a, "sender", "thread"), far=bool(getattr(a, "far", False)))
    stop: asyncio.Future = loop.create_future()

    async def ticker() -> None:
        while not stop.done():
            await asyncio.sleep(0.05)
            try:
                now = clock.now()
                mgr.on_tick(now)
                for x in mgr.watchers:
                    x.on_tick(now)
                log.advance(now)
                mark_positions(risk, eng.world)
                why = (mrisk.dry_watch(session, mgr, now, lambda kind, **kw: lf.note(events, clock, kind, **kw))
                       if a.dry else watch(risk, session, mgr, now))
            except Exception as e:  # the stops must never go unchecked: fail closed
                why = f"ticker error: {e!r}"[:300]
            if why and not stop.done():
                stop.set_result(why)

    async def every(s: float, fn, first: bool = False) -> None:
        while True:
            if not first:
                await asyncio.sleep(s)
            first = False
            try:
                await fn()
            except Exception as e:  # a periodic job's failure is logged, the stops still run
                lf.note(events, clock, "periodic_error", err=repr(e)[:200])

    async def warm() -> None:
        ms = await asyncio.to_thread(ops.keep_warm)
        if ms:
            w["warm"] = ms

    async def balance() -> None:
        b = await asyncio.to_thread(ops.balance)
        if b.get("balance") is not None:
            risk.balance = b["balance"]
            lf.note(events, clock, "balance", **b)

    async def stats() -> None:
        lf.note(events, clock, "stats", pnl=risk.pnl(), realised=risk.realised, exposure=risk.exposure(),
                resting=mgr.resting(), working=len(mgr.working()), balance=risk.balance, mgr=mgr.n,
                infer=w["infer"].n, log=log.n, trades=tap.n, eng=eng.stats(), warm_ms=w.get("warm"),
                fills=[x.n for x in mgr.watchers[1:]])

    async def sync() -> None:
        await asyncio.to_thread(clock.sync)
        if hasattr(ops, "set_offset"):
            ops.set_offset(clock.offset_ns)

    tasks = [asyncio.create_task(c) for c in (
        live.binance(clock, events, fans[0], a.conns), live.binance(clock, events, fans[1], a.conns),
        live.markets(clock, events, on_market, eng.on_event, tap, meta_sink), ticker(),
        every(60, stats), every(300, sync), every(0.5, warm, first=True), every(60, balance),
        settle(clock, mkts, settle_sink, risk, events))]
    if w["settle"] is not None and getattr(venue, "api", None):
        tasks.append(asyncio.create_task(userws.run(venue.api, w["settle"].on_user,
                                                    lambda kind, **kw: lf.note(events, clock, kind, **kw))))
    why = "exception"
    try:
        why = await (asyncio.wait_for(asyncio.shield(stop), a.hours * 3600) if a.hours else stop)
    except asyncio.TimeoutError:
        why = None
    finally:
        for t in tasks:
            t.cancel()
        mgr.stop(why or "run end")                  # cancel each quote; the session's cancel-all follows
        await asyncio.sleep(max(a.dry_ms / 1000, 0.0) + 0.05 if a.dry else 0)
        if w["settle"] is not None:
            await reconcile(w["settle"], venue, mgr, FINAL_WAIT_S)
        if hasattr(ops, "detach"):
            ops.detach()
        await asyncio.to_thread(ops.close)
        await asyncio.sleep(0)                      # run the acks the closing pool posted
        log.flush()
        lf.note(events, clock, "trade_stop", reason=why, pnl=risk.pnl(), exposure=risk.exposure(),
                mgr=mgr.n, working=[o.brief() for o in mgr.working()], t=time.time())
        for sk in (*w["sinks"].values(), settle_sink, events.sink):
            sk.close()
    if why:
        raise Stop(why)

