"""Entry points of `python3 -m btclat.trade maker` (wired in btclat/trade/__main__.py).

- live (--i-approve): after the shared preflight (credentials, kill file, day lock, geoblock,
  exchange version, balance) inside the session shell (cancel-all on any exit);
- dry (--dry): no credentials, no venue client, no signing library: the paper bot's import
  guard is installed first, so the process cannot load one. Its risk ledger lives in the run
  directory (drystate/), never in the real day's state; the kill file still stops it. The money
  caps are logged as would-skips, not applied (orders/risk.py)."""
from __future__ import annotations

import asyncio
import json
import socket
import time
from pathlib import Path

from recorder.live.clock import SERVERS
from recorder.live.sink import Sink
from btclat.paper.feeds.clock import AMAZON, PaperClock

from ..gate import preflight
from ..risk.book import RiskBook
from ..risk.session import Session, install_signals
from . import rules
from .ops.dry import NullVenue
from .orders.risk import MakerLimits

GUARD = True        # tests switch it off: the guard would block signing imports for the whole test process


def maker_limits(a) -> MakerLimits:
    return MakerLimits().lowered(max_open=a.max_open, market_cap=a.market_cap, inserts_hour=a.inserts_hour,
                                 fanout=a.fanout)


def live(a, venue, session, risk, out: Path, clock, run: str, hedge_factory=None) -> None:
    from . import run as mrun
    hedge = hedge_factory(venue) if hedge_factory is not None else None
    asyncio.run(mrun.main(a, venue, session, risk, out, clock, run, maker_limits(a), hedge))


def dry(a, limits, config: Path, clock, root: Path) -> int:
    if GUARD:
        from btclat.paper import guard
        guard.install()
    ml = maker_limits(a)
    kill = preflight.paths(config)["kill"]
    if kill.exists():
        raise preflight.Refused(f"refusing: kill file {kill} exists (remove it to allow a start)")
    clock = clock or PaperClock(AMAZON if a.ntp == "amazon" else SERVERS)
    run = a.run or f"{time.strftime('%Y%m%d-%H%M', time.gmtime())}-maker-dry-{socket.gethostname()}"
    out = root / run
    try:
        out.mkdir(parents=True, exist_ok=False)
    except FileExistsError:
        raise preflight.Refused(f"refusing: run directory {out} exists (another or earlier run)") from None
    events = Sink("events", root=out, flush_s=0)

    def note(kind, **kw):
        events.write(clock.now_ns(), json.dumps({"kind": kind, **kw}, default=str))

    risk = RiskBook(limits, out / "drystate")
    rule = rules.of(a.rule, a.hyst)
    note("preflight", mode="maker", dry=True, run=run, clock_offset_ns=clock.offset_ns, limits=ml.__dict__,
         rule=rule.kind, h=rule.h, arm=rule.name, money_caps="would-skip (dry)")
    print(f"maker --dry: run {run}, rule {rule.name}, no orders, money caps logged not applied, logs {out}",
          flush=True)
    install_signals()
    from . import run as mrun
    v = NullVenue()
    s = Session(v, kill, note)
    try:
        with s:
            asyncio.run(mrun.main(a, v, s, risk, out, clock, run, ml))
    finally:
        Sink.close_all()
    print(f"stopped: {s.exit_reason}; logs {out}", flush=True)
    return 0
