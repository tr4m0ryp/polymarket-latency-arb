"""Every hard cap trips, and no cap can be loosened."""
import dataclasses

import pytest

from btclat.trade.risk.book import Intent, RiskBook
from btclat.trade.risk.limits import HARD, LimitError, Limits

NOW = 1_791_800_000.0


def it(price=0.50, size=5.0, slug="m1", token="UP"):
    return Intent("vt_v1_m0.03_any", slug, token, True, price, size, NOW + 200)


@pytest.fixture
def rb(tmp_path):
    return RiskBook(Limits(), tmp_path / "state", now=NOW)


def test_base_order_passes(rb):
    assert rb.check(it(), NOW) is None


@pytest.mark.parametrize("name", list(HARD))
def test_limits_cannot_be_raised(name):
    hard, up = HARD[name]
    with pytest.raises(LimitError):
        Limits().lowered(**{name: hard * 2 if up else hard / 2})


def test_limits_can_be_lowered():
    assert Limits().lowered(max_orders_hour=10, loss_cap=5.0).loss_cap == 5.0


def test_tampered_limits_refused(tmp_path):
    L = Limits()
    object.__setattr__(L, "max_exposure", 1000.0)
    with pytest.raises(LimitError):
        RiskBook(L, tmp_path)
    with pytest.raises(dataclasses.FrozenInstanceError):
        Limits().max_shares = 100


def test_max_shares(rb):
    assert rb.check(it(size=6), NOW) == "max_shares"


def test_max_notional(rb):
    assert rb.check(it(price=0.61), NOW) == "max_notional"
    assert rb.check(it(price=0.60), NOW) is None


def test_venue_minimums(rb):
    assert rb.check(it(size=4), NOW) == "below_venue_min_shares"
    assert rb.check(it(price=0.19), NOW) == "below_venue_min_notional"


def test_max_exposure(rb):
    for i in range(5):                                  # 5 x (2.5 + fee) = 12.94 open
        rb.fill(it(slug=f"m{i}"), 5, 2.5, 0.0875)
    assert rb.exposure() == pytest.approx(12.9375)
    assert rb.check(it(price=0.40), NOW) == "max_exposure"


def test_inflight_counts_as_exposure(rb):
    for i in range(5):
        rb.reserve(f"s{i}", it(slug=f"m{i}"), NOW)
    assert rb.check(it(), NOW) == "max_exposure"
    for i in range(5):
        rb.release(f"s{i}")
    assert rb.check(it(), NOW) is None


def test_loss_headroom(rb):
    for i in range(3):                                  # three losers: realised -7.76
        rb.fill(it(slug=f"l{i}"), 5, 2.5, 0.0875)
        rb.resolve(f"l{i}", 0.0)
    assert rb.exposure() == 0
    assert rb.pnl() == pytest.approx(-7.7625)
    assert rb.check(it(), NOW) == "loss_headroom"
    assert rb.check(it(price=0.20), NOW) is None        # worst case 1.11 keeps pnl > -10


def test_max_orders_hour(rb):
    for i in range(40):
        rb.reserve(f"s{i}", it(), NOW - 3000 + i)
        rb.release(f"s{i}")
    assert rb.check(it(), NOW) == "max_orders_hour"
    assert rb.check(it(), NOW + 601) is None            # the oldest left the 3600 s window


def test_orders_hour_survives_restart(tmp_path):
    a = RiskBook(Limits(), tmp_path, now=NOW)
    for i in range(40):
        a.reserve(f"s{i}", it(), NOW - 10)
        a.release(f"s{i}")
    b = RiskBook(Limits(), tmp_path, now=NOW)
    assert b.check(it(), NOW) == "max_orders_hour"


def test_balance(rb):
    rb.balance = 1.0
    assert rb.check(it(), NOW) == "balance"
    rb.balance = 50.0
    assert rb.check(it(), NOW) is None


def test_stopped(rb):
    rb.stop_reason = "x"
    assert rb.check(it(), NOW) == "stopped"
