"""The loss cap stops the run, locks the UTC day, and a restart that day is refused."""
import pytest

from btclat.trade.gate import preflight
from btclat.trade.micro.run import watch
from btclat.trade.risk.book import Intent, RiskBook, lock_path
from btclat.trade.risk.limits import Limits
from btclat.trade.risk.session import Session

from .fakes import FakeVenue, write_creds

NOW = 1_791_800_000.0          # 2026-10-12 UTC


def it(slug, token="UP", up=True):
    return Intent("vt_v1_m0.03_any", slug, token, up, 0.55, 5.0, NOW + 200)


class _Lx:
    stop_reason = None


def _lose(rb, n):
    for i in range(n):
        rb.fill(it(f"x{i}"), 5, 2.75, 0.0866)
        rb.resolve(f"x{i}", 0.0)


def test_realised_loss_locks_day(tmp_path):
    state = tmp_path / "state"
    rb = RiskBook(Limits(), state, now=NOW)
    _lose(rb, 3)
    assert not rb.breach() and not rb.locked()          # -8.51
    _lose(rb, 1)                                          # -11.35
    assert rb.breach() and rb.locked()
    assert lock_path(state, "2026-10-12").exists()
    assert rb.check(it("y"), NOW) == "stopped"
    again = RiskBook(Limits(), state, now=NOW + 60)       # restart, same day: ledger replayed
    assert again.realised == pytest.approx(rb.realised)
    assert again.check(it("y"), NOW + 60) == "day_locked"


def test_marked_loss_trips(tmp_path):
    rb = RiskBook(Limits(), tmp_path, now=NOW)
    for i in range(4):
        rb.fill(it(f"m{i}"), 5, 2.75, 0.0866)
        rb.mark["UP"] = 0.01                              # our book: the side is nearly worthless
    assert rb.realised == 0 and rb.pnl() < -10
    assert rb.breach() and rb.locked()


def test_preflight_refuses_locked_day_until_next_day(tmp_path):
    write_creds(tmp_path)
    rb = RiskBook(Limits(), preflight.paths(tmp_path)["state"], now=NOW)
    _lose(rb, 4)
    assert rb.breach()
    with pytest.raises(preflight.Refused, match="locked by the loss cap"):
        preflight.offline(True, tmp_path, now=NOW + 3600)
    assert preflight.offline(True, tmp_path, now=NOW + 86400).sig_type == 3


def test_watch_stops_on_breach_and_kill(tmp_path):
    rb = RiskBook(Limits(), tmp_path / "s", now=NOW)
    s = Session(FakeVenue(), tmp_path / "KILL")
    assert watch(rb, s, _Lx(), NOW) is None
    _lose(rb, 4)
    assert "loss cap" in watch(rb, s, _Lx(), NOW)
    rb2 = RiskBook(Limits(), tmp_path / "s2", now=NOW)
    (tmp_path / "KILL").touch()
    assert "kill file" in watch(rb2, s, _Lx(), NOW)


def test_roll_carries_positions(tmp_path):
    rb = RiskBook(Limits(), tmp_path, now=NOW)
    _lose(rb, 2)
    rb.fill(it("open"), 5, 2.75, 0.0866)
    assert rb.roll(NOW + 86400) and rb.realised == 0 and rb.exposure() == pytest.approx(2.8366)
    nxt = RiskBook(Limits(), tmp_path, now=NOW + 86400)
    assert nxt.exposure() == pytest.approx(2.8366) and nxt.realised == 0
