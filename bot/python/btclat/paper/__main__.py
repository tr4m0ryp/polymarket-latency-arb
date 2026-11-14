"""Run the read-only paper bot on live feeds.

    nice -n 10 python3 -m btclat.paper [--hours H] [--latency-ms 0] [--model-L 0] [--conns 4]
        [--run NAME] [--ntp amazon|public] [--no-record]

Writes data/paper/<run>/: orders-<hour>.tsv.gz (one JSON line per would-be order, final
after ~35 s), settle-*.tsv.gz (Gamma outcome per market), raw/ (the received Binance and
5m CLOB messages, markets and events in the recorder's format, for the replay simulator).
Sends nothing: no keys, no signing, no order client (guard.py)."""
from __future__ import annotations

import argparse
import asyncio
import json
import socket
import time

from . import guard

guard.install()

from recorder.live import feeds as lf  # noqa: E402
from recorder.live.clock import SERVERS  # noqa: E402
from recorder.live.sink import Sink  # noqa: E402
from research.strategy.ingest.markets import _gamma_outcome  # noqa: E402

from .arms.defs import ARM_NAMES  # noqa: E402
from .engine.core import Engine  # noqa: E402
from .feeds import live  # noqa: E402
from .feeds.clock import AMAZON, PaperClock  # noqa: E402
from .model.load import ValueModel  # noqa: E402
from .replay.source import LIVE  # noqa: E402

PAPER = LIVE.parent / "paper"


def rss_mb() -> float:
    with open("/proc/self/status") as fh:
        for line in fh:
            if line.startswith("VmRSS:"):
                return int(line.split()[1]) / 1024
    return float("nan")


async def every(s: float, fn) -> None:
    while True:
        await asyncio.sleep(s)
        try:
            fn()
        except Exception as e:  # a failed periodic job must not end the run silently
            print("periodic job failed:", repr(e), flush=True)


async def settle_loop(clock, mkts: dict, sink, events) -> None:
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
                done.add(slug)
            elif clock.now() > m["end"] + 7200:
                done.add(slug)


async def main(a) -> None:
    clock = PaperClock(AMAZON if a.ntp == "amazon" else SERVERS)
    run = a.run or time.strftime("%Y%m%d-%H%M", time.gmtime()) + "-" + socket.gethostname()
    root = PAPER / run
    raw = root / "raw"
    events = live.EventsTap(Sink("events", root=raw, flush_s=0))
    orders, settle = Sink("orders", root=root, flush_s=1.0), Sink("settle", root=root, flush_s=0)
    model = ValueModel(f"v1_L{a.model_L}")
    eng = Engine(model, orders, run, L=a.latency_ms / 1000, now=clock.now)
    rec = (lambda name: None) if a.no_record else (lambda name: Sink(name, root=raw))
    mkts: dict = {}

    def on_market(m: dict) -> None:
        eng.world.add_market(m).gaps = events.gaps.setdefault(m["slug"], [])
        mkts[m["slug"]] = m

    fans = [live.FanIn(p, eng.on_event, rec("binance_fut" if p else "binance"), a.conns) for p in (False, True)]
    lf.note(events, clock, "paper_start", run=run, model=model.name, sha16=model.sha16, arms=ARM_NAMES,
            L_ms=a.latency_ms, conns=a.conns, ntp=a.ntp, offset_ns=clock.offset_ns, hours=a.hours,
            tree_compile_s=model.compile_s)

    lag = {"last": time.monotonic(), "max_ms": 0.0}

    def tick() -> None:   # paper jobs, and the event loop's lag (blocked loop -> socket backlog)
        now = time.monotonic()
        lag["max_ms"] = max(lag["max_ms"], (now - lag["last"] - 0.05) * 1e3)
        lag["last"] = now
        eng.paper.advance(clock.now())

    def stats() -> None:
        lf.note(events, clock, "stats", rss_mb=rss_mb(), loop_lag_max_ms=lag["max_ms"],
                cpu_s=time.process_time(), clock_offset_ns=clock.offset_ns,
                wins_spot=fans[0].wins, wins_perp=fans[1].wins, dups=[f.dups for f in fans],
                markets=len(eng.world.mkts), pending=len(eng.paper.jobs), **eng.stats())
        lag["max_ms"] = 0.0

    def sync() -> None:
        clock.sync()

    tasks = [asyncio.create_task(c) for c in (
        live.binance(clock, events, fans[0], a.conns), live.binance(clock, events, fans[1], a.conns),
        live.markets(clock, events, on_market, eng.on_event, rec("clob_5m"),
                     None if a.no_record else Sink("markets", root=raw, flush_s=0)),
        every(0.05, tick), every(60, stats),
        every(300, lambda: asyncio.get_running_loop().run_in_executor(None, sync)),
        settle_loop(clock, mkts, settle, events))]
    try:
        if a.hours:
            await asyncio.sleep(a.hours * 3600)
        else:
            await asyncio.gather(*tasks)
    finally:
        stats()
        for t in tasks:
            t.cancel()
        eng.paper.flush()
        lf.note(events, clock, "paper_stop")
        Sink.close_all()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--hours", type=float, default=None)
    ap.add_argument("--latency-ms", type=float, default=0.0, help="assumed receipt-to-CLOB latency")
    ap.add_argument("--model-L", type=int, default=0, choices=(-40, 0, 50))
    ap.add_argument("--conns", type=int, default=4)
    ap.add_argument("--run", default=None)
    ap.add_argument("--ntp", default="public", choices=("public", "amazon"))
    ap.add_argument("--no-record", action="store_true")
    asyncio.run(main(ap.parse_args()))
