"""Money caps in a dry run are logged, not applied: a breached loss headroom, market cap, max
open, balance or day lock still sends the quote to the simulated venue and logs a would-skip;
live, the same breach skips the quote exactly as before. Non-money guards apply in both."""
import json

import pytest

from btclat.trade.maker.log import MakerLog
from btclat.trade.maker.ops.dry import DryOps
from btclat.trade.maker.orders.manager import OrderManager
from btclat.trade.maker.orders.risk import MakerLimits, MakerRisk
from btclat.trade.micro.run import watch
from btclat.trade.risk.book import RiskBook, lock_path
from btclat.trade.risk.limits import Limits

from ..fakes import ListSink
from .fakes import Clock, book, lines, manager, market, q


def _breach(cap: str, rb: RiskBook) -> MakerLimits:
    """Break one money cap for a 5-share quote at 0.47 ($2.35); returns the maker limits to use."""
    if cap == "loss_headroom":
        rb.realised = -9.0
    elif cap == "balance":
        rb.balance = 1.0
    elif cap == "day_locked":
        lock_path(rb.state, rb.day).write_text("{}")
    return MakerLimits(**({"market_cap": 2.0} if cap == "market_cap" else {"max_open": 2.0} if cap == "max_open" else {}))


def _dry(tmp_path, cap: str | None, inserts_hour: int = 3600):
    clock, later = Clock(), []
    rb = RiskBook(Limits(), tmp_path / "drystate", now=clock.now())
    lim = _breach(cap, rb) if cap else MakerLimits()
    lim = MakerLimits(**{**lim.__dict__, "inserts_hour": inserts_hour})
    m = market()
    ops = DryOps(lambda dt, cb: later.append(cb), clock.now, lambda slug: m.book)
    sinks = {n: ListSink() for n in ("quotes", "ops", "fills", "infer")}
    log = MakerLog(sinks, clock.now_ns, lambda slug: m.book, dry=True)
    mgr = OrderManager(ops, MakerRisk(rb, lim, dry=True), log, clock.now)
    mgr.book_of = lambda slug: m.book
    return mgr, sinks, later, m, clock


CAPS = ("loss_headroom", "market_cap", "max_open", "balance", "day_locked")


@pytest.mark.parametrize("cap", CAPS)
def test_dry_cap_breached_still_quotes(tmp_path, cap):
    mgr, sinks, later, m, clock = _dry(tmp_path, cap)
    mgr.on_quote(m, q(clock.t, ask=0))
    ops = lines(sinks["ops"])
    assert [(r["kind"], r.get("reason")) for r in ops] == [("would_skip", cap), ("insert", None)]
    assert mgr.n["would_skips"] == 1 and mgr.n["skips"] == 0
    for cb in later:                              # the simulated venue acks it: the quote rests
        cb()
    assert [o.state for o in mgr.working()] == ["live"]


@pytest.mark.parametrize("cap", CAPS)
def test_live_cap_breached_skips_as_before(tmp_path, cap):
    w = manager(tmp_path)
    w.mgr.risk.limits = _breach(cap, w.risk)
    w.mgr.on_quote(w.m, q(w.clock.t, ask=0))
    ops = lines(w.sinks["ops"])
    assert w.ops.n("insert") == 0 and [(r["kind"], r["reason"]) for r in ops] == [("skip", cap)]
    assert w.mgr.n["skips"] == 1 and w.mgr.n["would_skips"] == 0 and not w.mgr.risk.dry


def test_dry_keeps_non_money_guards(tmp_path):
    mgr, sinks, later, m, clock = _dry(tmp_path, "loss_headroom", inserts_hour=1)
    mgr.on_quote(m, q(clock.t))                    # bid goes out (would-skip logged); ask hits inserts_hour
    kinds = [(r["kind"], r.get("reason"), r["side"]) for r in lines(sinks["ops"])]
    assert kinds == [("would_skip", "loss_headroom", "bid"), ("insert", None, "bid"), ("skip", "inserts_hour", "ask")]
    mgr2, sinks2, _, m2, clock2 = _dry(tmp_path / "x", None)
    m2.book = book(45, 47)                         # our bid 47 would cross the 47 ask
    mgr2.on_quote(m2, q(clock2.t, ask=0))
    assert [(r["kind"], r["reason"]) for r in lines(sinks2["ops"])] == [("skip", "would_cross")]


class _Sess:
    kill = "KILL"

    def killed(self):
        return False


def test_dry_loss_cap_never_stops_or_locks(tmp_path):
    mgr, sinks, later, m, clock = _dry(tmp_path, None)
    rb, notes = mgr.risk.book, []
    rb.realised = -20.0
    for _ in range(3):
        assert mgr.risk.dry_watch(_Sess(), mgr, clock.now(), lambda kind, **kw: notes.append((kind, kw))) is None
    assert len(notes) == 1 and notes[0][0] == "would_stop" and "loss cap" in notes[0][1]["reason"]
    assert not rb.locked() and rb.stop_reason is None
    w = manager(tmp_path / "live")                 # live: the same PnL stops the run and locks the day
    w.risk.realised = -20.0
    assert "loss cap" in watch(w.risk, _Sess(), w.mgr, w.clock.now()) and w.risk.locked()
    assert json.loads(lock_path(w.risk.state, w.risk.day).read_text())["realised"] == -20.0
