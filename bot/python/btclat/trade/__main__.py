"""Small-money live test on the Polymarket CLOB. Sends REAL orders: needs --i-approve, the
credentials file (~/.config/btclat/polymarket.env, chmod 600) and an unlocked UTC day.

    python3 -m btclat.trade probe --i-approve [--zero] [--every 30] [--n N] [--hours H] [--warm both]
    python3 -m btclat.trade micro --i-approve [--veto] [--hours H] [--ntp amazon] [--conns 4]
        [--max-orders-hour N] [--loss-cap X] [--max-exposure X] [--max-notional X]  (lower only)
    python3 -m btclat.trade holdtest --i-approve [--n 24] [--every 30] [--ask-band 0.02,0.08]
    python3 -m btclat.trade holdtest --i-approve --dup [--dup-reps 5]
    python3 -m btclat.trade maker --dry [--hours H] [--record] [--dry-ms 50] [--hold 0.27]   (no orders, no keys)
    python3 -m btclat.trade maker --i-approve [--hours H] [--fanout 3] [--max-open X] [--market-cap X]
    python3 -m btclat.trade maker ... --rule inside [--hyst 0.005]      (default --rule frozen, no --hyst)
    python3 -m btclat.trade maker --i-approve --far --sender ab ...     (latency test: every insert at 0.01)

Kill: `touch ~/.config/btclat/KILL` (stops within one loop, cancel-all, blocks restarts).
Writes data/trade/<run>/. Report: python3 -m btclat.trade.report --run <run>."""
from __future__ import annotations

import argparse
import asyncio
import json
import socket
import sys
import time
from pathlib import Path

from recorder.live.clock import SERVERS
from recorder.live.sink import Sink
from btclat.paper.feeds.clock import AMAZON, PaperClock

from .gate import preflight
from .risk.book import RiskBook
from .risk.limits import Limits
from .risk.session import Session, install_signals

TRADE = Path(__file__).resolve().parents[2] / "data" / "trade"


def parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="python3 -m btclat.trade")
    ap.add_argument("mode", choices=("probe", "micro", "holdtest", "maker"))
    ap.add_argument("--i-approve", action="store_true", help="the user approved real orders for this run")
    ap.add_argument("--run", default=None)
    ap.add_argument("--hours", type=float, default=None)
    ap.add_argument("--ntp", default="amazon", choices=("public", "amazon"))
    ap.add_argument("--every", type=float, default=30.0, help="probe: s between orders (floor 5)")
    ap.add_argument("--n", type=int, default=None, help="probe: number of cycles")
    ap.add_argument("--zero", action="store_true",
                    help="probe with $0 pUSD: every order is rejected at the balance check, which proves "
                         "signing, auth and wallet type and still times the POST round trip")
    ap.add_argument("--warm", default="both", choices=("both", "warm", "idle"))
    ap.add_argument("--warm-n", type=int, default=5, help="probe: keep-warm pings (1/s) before a warm cycle")
    ap.add_argument("--veto", action="store_true", help="micro: also trade vt_v1_m0.02_trigger")
    ap.add_argument("--conns", type=int, default=4)
    ap.add_argument("--latency-ms", type=float, default=0.0)
    ap.add_argument("--model-L", type=int, default=0, choices=(-40, 0, 50))
    ap.add_argument("--ask-band", default=None, help="holdtest: lo,hi best ask of the side bought (<= 0.30)")
    ap.add_argument("--dup", action="store_true", help="holdtest: duplicate-send test (unfillable orders)")
    ap.add_argument("--dup-reps", type=int, default=5, help="holdtest --dup: repetitions per copy count (<= 10)")
    ap.add_argument("--dry", action="store_true", help="maker: no orders; fills inferred from the live tape")
    ap.add_argument("--record", action="store_true", help="maker: also record the raw feeds (replay sim)")
    ap.add_argument("--dry-ms", type=float, default=50.0, help="maker --dry: decision-to-venue latency (sim L)")
    ap.add_argument("--order-type", default="GTD", choices=("GTD", "GTC"),
                    help="maker: post-only GTD (expires server now + 185 s) or GTC (cancels + cancel-all only)")
    ap.add_argument("--hold", type=float, default=0.27, help="maker: venue hold of a crossing order (inferred fills)")
    ap.add_argument("--rule", default="frozen", choices=("frozen", "inside"),
                    help="maker: frozen vm_fair0.03_p-0.03, or the pre-registered inside gate vi_fair0.04_p-0.02")
    ap.add_argument("--hyst", type=float, default=0.0,
                    help="maker --rule inside: insert hysteresis h (enter at pred < pull - h); refused with frozen")
    ap.add_argument("--sender", default="thread", choices=("thread", "proc", "ab"),
                    help="maker live: inserts / cancels from the event loop's pool threads, from a separate "
                         "sender process, or each op at random from one of the two (A/B latency test)")
    ap.add_argument("--far", action="store_true",
                    help="maker live: every insert a post-only BUY at 0.01 at the rule's decision instants "
                         "(latency test under live load; cannot fill above 0.01, $0.05 per order at most)")
    for k in ("max-orders-hour", "loss-cap", "max-exposure", "max-notional", "max-open", "market-cap",
              "inserts-hour", "fanout"):
        ap.add_argument(f"--{k}", type=int if k in ("max-orders-hour", "inserts-hour", "fanout") else float, default=None,
                        help="lower the hard limit (cannot raise it)")
    return ap


def default_venue(creds, clock):
    from .venue.client import LiveClob
    return LiveClob(creds, now_ns=clock.now_ns)


def _mode(a) -> str:
    if a.mode == "holdtest":
        return "holddup" if a.dup else "holdtest"
    return "probe0" if a.mode == "probe" and a.zero else a.mode


def start(argv=None, venue_factory=None, config: Path = preflight.CONFIG, clock=None, root: Path = TRADE,
          fanout_factory=None) -> int:
    a = parser().parse_args(argv)
    limits = Limits().lowered(max_orders_hour=a.max_orders_hour, loss_cap=a.loss_cap,
                              max_exposure=a.max_exposure, max_notional=a.max_notional)
    if a.mode == "maker":
        from .maker import rules as maker_rules
        maker_rules.of(a.rule, a.hyst)                     # refuse a bad --rule / --hyst before anything else
    if a.mode == "maker" and a.dry and (a.far or a.sender != "thread"):
        raise SystemExit("refusing: --far / --sender are for live maker runs (a dry run sends nothing)")
    if a.mode == "maker" and a.dry:
        from .maker import cli as maker_cli
        return maker_cli.dry(a, limits, config, clock, root)
    creds = preflight.offline(a.i_approve, config)          # no network before this passes
    p = preflight.paths(config)
    clock = clock or PaperClock(AMAZON if a.ntp == "amazon" else SERVERS)
    venue = (venue_factory or default_venue)(creds, clock)
    try:
        venue.connect()
        info = preflight.online(venue, _mode(a))
    except BaseException:
        venue.close()
        raise
    run = a.run or f"{time.strftime('%Y%m%d-%H%M', time.gmtime())}-{a.mode}-{socket.gethostname()}"
    out = root / run
    try:   # atomic: a second process on the same run would interleave the gzip logs
        out.mkdir(parents=True, exist_ok=False)
    except FileExistsError:
        venue.close()
        raise preflight.Refused(f"refusing: run directory {out} exists (another or earlier run)") from None
    events = Sink("events", root=out, flush_s=0)

    def note(kind, **kw):
        events.write(clock.now_ns(), json.dumps({"kind": kind, **kw}, default=str))

    risk = RiskBook(limits, p["state"])
    risk.balance = info["balance"]
    rule = {"rule": a.rule, "h": a.hyst} if a.mode == "maker" else {}
    note("preflight", mode=a.mode, run=run, venue=venue.info(), clock_offset_ns=clock.offset_ns, **rule, **info)
    print(f"{a.mode}: run {run}, balance ${info['balance']:.2f}, geoblock {info['geoblock']}", flush=True)
    install_signals()
    try:
        with Session(venue, p["kill"], note) as s:
            if a.mode == "probe":
                from .probe import run as probe
                n = probe.run(venue, s, probe.logger(Sink("probe", root=out, flush_s=1.0), clock.now_ns), a, limits)
                note("probe_done", **n)
            elif a.mode == "holdtest":
                _hold(a, venue, s, out, clock, note, fanout_factory)
            elif a.mode == "maker":
                from .maker import cli as maker_cli
                maker_cli.live(a, venue, s, risk, out, clock, run, fanout_factory)
            else:
                from .micro import run as micro
                asyncio.run(micro.main(a, venue, s, risk, out, clock, run))
    finally:
        venue.close()
        Sink.close_all()
    print(f"stopped: {s.exit_reason}; cancel-all ok: {s.cancel_all_ok}; logs {out}", flush=True)
    return 0


def _hold(a, venue, s, out: Path, clock, note, fanout_factory) -> None:
    from .hold import dup, run as hold
    from .probe.run import logger
    if not a.dup:
        note("hold_done", **hold.run(venue, s, logger(Sink("hold", root=out, flush_s=1.0), clock.now_ns), a))
        return
    if fanout_factory is None:
        from .venue.fanout import Fanout as fanout_factory
    f = fanout_factory(venue)
    try:
        note("dup_done", **dup.run(venue, s, logger(Sink("dup", root=out, flush_s=1.0), clock.now_ns), a, f))
    finally:
        f.close()


if __name__ == "__main__":
    sys.exit(start())
