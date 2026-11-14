"""Probe mode never sends a marketable order and cancels every order it places."""
from types import SimpleNamespace

import pytest

from btclat.trade.probe import run as probe
from btclat.trade.risk.limits import Limits
from btclat.trade.risk.session import Session, Stop

from .fakes import FakeVenue, resp

MKT = {"slug": "btc-updown-5m-1791800100", "up": "UP", "down": "DN", "start": 1791800100}


class Markets:
    def current(self, now, margin=20.0):
        return MKT


class Clock:
    def __init__(self):
        self.t, self.slept = 1791800110.0, []

    def now(self):
        return self.t

    def sleep(self, s):
        self.slept.append(s)
        self.t += s


def args(**kw):
    d = {"every": 30.0, "n": 3, "hours": None, "warm": "both", "warm_n": 2}
    d.update(kw)
    return SimpleNamespace(**d)


def go(v, tmp_path, a=None, limits=None, clock=None):
    c = clock or Clock()
    log = []
    s = Session(v, tmp_path / "KILL", sleep=lambda x: None)
    with s:
        n = None
        n = probe.run(v, s, log.append, a or args(), limits or Limits(), now=c.now, sleep=c.sleep, markets=Markets())
    return n, log, s, c


@pytest.mark.parametrize("bb,ok", [(0.50, True), (0.06, True), (0.05, False), (0.02, False), (float("nan"), False)])
def test_passive_price(bb, ok):
    assert (probe.passive_price(bb) == 0.01) is ok
    if not ok:
        with pytest.raises(probe.Marketable):
            probe.assert_passive(0.01, bb)


def test_probe_posts_post_only_and_cancels(tmp_path):
    v = FakeVenue(bb=0.50)
    n, log, s, c = go(v, tmp_path)
    assert n["sent"] == 3 and n["cancelled"] == 3
    signs = [x for x in v.calls if x[0] == "sign"]
    assert all(x[2] == 0.01 and x[3] == 5.0 and x[4] == "BUY" and x[5] == "GTC" and x[6] is True for x in signs)
    seq = [x[0] for x in v.calls if x[0] in ("post", "cancel")]
    assert seq == ["post", "cancel"] * 3
    assert [r["warm"] for r in log] == [True, False, True] and len(log[0]["ping_ms"]) == 2
    assert s.cancel_all_ok and v.n("cancel_all") == 1


def test_probe_skips_when_book_low(tmp_path):
    v = FakeVenue(bb=0.05)
    n, log, s, _ = go(v, tmp_path)
    assert n["sent"] == 0 and v.n("post") == 0 and v.n("sign") == 0
    assert all(r["decision"] == "skip:book_too_low" for r in log)


def test_probe_rate_floor_and_cap(tmp_path):
    v = FakeVenue()
    n, log, _, c = go(v, tmp_path, a=args(every=1.0, n=4, warm="idle"), limits=Limits().lowered(max_probe_hour=2))
    assert v.n("post") == 2 and log[2]["decision"] == "skip:max_probe_hour"
    assert min(c.slept) >= 5.0 - 1e-9                    # floor of 5 s between cycles


def test_probe_stops_on_fill(tmp_path):
    v = FakeVenue(post=resp(body={"success": True, "orderID": "0xa", "status": "matched",
                                   "makingAmount": "0.05", "takingAmount": "5"}))
    n, log, s, _ = go(v, tmp_path)
    assert len(log) == 1 and "fill" in s.exit_reason and v.n("cancel_all") == 1


def test_probe_stops_on_failed_cancel(tmp_path):
    v = FakeVenue(cancel_ok=False)
    _, log, s, _ = go(v, tmp_path)
    assert len(log) == 1 and "cancel" in s.exit_reason and v.n("cancel_all") == 1


def test_probe_stops_on_region_rejection(tmp_path):
    v = FakeVenue(post=resp(code=403, body={"error": "Trading restricted in your region"}))
    _, log, s, _ = go(v, tmp_path)
    assert log[0]["err_kind"] == "geoblock" and s.exit_reason.startswith("Stop") and v.n("cancel") == 0


def test_probe_rate_limited_backs_off(tmp_path):
    v = FakeVenue(post=resp(code=429, body="Too Many Requests", hdr={"retry-after": "90"}))
    _, log, _, c = go(v, tmp_path, a=args(n=2, warm="idle"))
    assert log[0]["err_kind"] == "rate_limited" and c.slept[0] >= 90


def test_probe_kill_file_mid_run(tmp_path):
    v = FakeVenue()
    c = Clock()

    def sleep(s):
        (tmp_path / "KILL").touch()
        c.t += s
    log = []
    s = Session(v, tmp_path / "KILL", sleep=lambda x: None)
    with s:
        probe.run(v, s, log.append, args(n=10, warm="idle"), Limits(), now=c.now, sleep=sleep, markets=Markets())
    assert len(log) == 1 and "kill file" in s.exit_reason and v.n("cancel_all") == 1


def test_stop_is_clean_exit(tmp_path):
    with Session(FakeVenue(), tmp_path / "KILL", sleep=lambda x: None):
        raise Stop("x")
