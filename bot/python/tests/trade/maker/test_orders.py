"""Maker order manager: one working order per side per market, cancel-before-replace, pulls and
guards cancel at once, rejects, unconfirmed cancels, caps, GTD expiry, stop."""
import pytest

from btclat.trade.maker.orders.risk import MakerLimits

from .fakes import START, lines, live_per_slot, manager, q


def test_quotes_both_sides_post_only_prices(tmp_path):
    w = manager(tmp_path)
    w.mgr.on_quote(w.m, q(w.clock.t))
    ins = [c for c in w.ops.calls if c[0] == "insert"]
    assert [(c[2], c[3]) for c in ins] == [(47, "bid"), (53, "ask")]
    o_bid = w.ops.ack("insert")
    o_ask = w.ops.ack("insert")
    assert (o_bid.token, o_bid.price, o_bid.size, o_bid.otype) == ("UP", 0.47, 5.0, "GTD")
    assert (o_ask.token, o_ask.price) == ("DN", 0.47)          # Up ask 53 = BUY Down at 0.47
    assert o_bid.state == o_ask.state == "live"


def test_requote_cancels_first_never_two_live(tmp_path):
    w = manager(tmp_path)
    t = w.clock.t
    w.mgr.on_quote(w.m, q(t, ask=0))
    w.mgr.on_quote(w.m, q(t + 0.01, bid=48, ask=0))     # target moves while the insert is in flight
    assert w.ops.n("insert") == 1 and w.ops.n("cancel") == 0
    w.ops.ack("insert")                                 # live at 47, target 48: cancel at once
    assert w.ops.n("cancel") == 1 and w.ops.n("insert") == 1
    w.mgr.on_quote(w.m, q(t + 0.02, bid=49, ask=0))     # cancelling: wait, no second order
    assert w.ops.n("insert") == 1 and max(live_per_slot(w.mgr).values()) == 1
    w.ops.ack("cancel")                                 # confirmed: the replacement at the latest target
    ins = [c for c in w.ops.calls if c[0] == "insert"]
    assert len(ins) == 2 and ins[-1][2] == 49 and max(live_per_slot(w.mgr).values()) == 1


def test_pull_cancels_in_the_same_call(tmp_path):
    w = manager(tmp_path)
    w.mgr.on_quote(w.m, q(w.clock.t, ask=0))
    w.ops.ack("insert")
    w.mgr.on_quote(w.m, q(w.clock.t + 0.02, bid=0, ask=0, pull_bid=True))
    assert w.ops.n("cancel") == 1
    qs = lines(w.sinks["quotes"])
    assert qs[-1]["cause"] == "pull" and qs[-1]["tick"] == 0


@pytest.mark.parametrize("dt,why", [(240.0 - 30 + 1, "tleft"), (2.0, "stale")])
def test_guards_cancel(tmp_path, dt, why):
    w = manager(tmp_path)
    w.mgr.on_quote(w.m, q(w.clock.t, ask=0))
    w.ops.ack("insert")
    w.clock.t += dt
    w.mgr.on_tick(w.clock.t)
    assert w.ops.n("cancel") == 1 and lines(w.sinks["quotes"])[-1]["cause"] == why


def test_socket_gap_cancels(tmp_path):
    w = manager(tmp_path)
    w.mgr.gaps[w.m.meta["slug"]] = [[w.clock.t, None]]
    w.mgr.on_quote(w.m, q(w.clock.t, ask=0))
    w.ops.ack("insert")
    w.mgr.on_tick(w.clock.t + 0.05)
    assert w.ops.n("cancel") == 1 and lines(w.sinks["quotes"])[-1]["cause"] == "gap"


def test_post_only_reject_backs_off_then_retries(tmp_path):
    w = manager(tmp_path)
    w.mgr.on_quote(w.m, q(w.clock.t, ask=0))
    w.ops.ack("insert", ok=False, err_kind="post_only_crosses", err="crosses")
    w.mgr.on_tick(w.clock.t + 0.1)
    assert w.ops.n("insert") == 1 and w.mgr.stop_reason is None
    w.clock.t += 0.25
    w.mgr.on_quote(w.m, q(w.clock.t, ask=0))
    w.mgr.on_tick(w.clock.t)
    assert w.ops.n("insert") == 2


@pytest.mark.parametrize("res,stop", [({"ok": False, "err_kind": "geoblock", "err": "region"}, "geoblock"),
                                      ({"ok": False, "unknown": True, "err_kind": "transport"}, "unknown")])
def test_fatal_or_unknown_insert_stops(tmp_path, res, stop):
    w = manager(tmp_path)
    w.mgr.on_quote(w.m, q(w.clock.t, ask=0))
    w.ops.ack("insert", **res)
    assert stop in w.mgr.stop_reason
    if res.get("unknown"):
        assert live_per_slot(w.mgr) == {(w.m.meta["slug"], "bid"): 1}   # the slot is never freed


def test_unconfirmed_cancel_retries_then_stops(tmp_path):
    w = manager(tmp_path)
    w.mgr.on_quote(w.m, q(w.clock.t, ask=0))
    w.ops.ack("insert")
    w.mgr.on_quote(w.m, q(w.clock.t, bid=0, ask=0))
    for _ in range(3):
        w.ops.ack("cancel", confirmed=False)
        w.ops.ack("lookup", status="LIVE")
    assert w.ops.n("cancel") == 3 and "not confirmed" in w.mgr.stop_reason


def test_unconfirmed_cancel_of_a_filled_order_records_the_fill(tmp_path):
    w = manager(tmp_path)
    w.mgr.on_quote(w.m, q(w.clock.t, ask=0))
    o = w.ops.ack("insert")
    w.mgr.on_quote(w.m, q(w.clock.t, bid=0, ask=0))
    w.ops.ack("cancel", confirmed=False)
    w.ops.ack("lookup", status="MATCHED", fill_sh=5.0)
    assert o.state == "done" and w.mgr.n["fills"] == 1 and w.mgr.stop_reason is None
    p = w.risk.pos[(w.m.meta["slug"], "UP")]
    assert p.sh == 5.0 and p.cost == pytest.approx(5 * 0.47) and p.fee == 0.0


def test_market_cap_and_max_open(tmp_path):
    w = manager(tmp_path, limits=MakerLimits(market_cap=4.0, max_open=25.0))
    w.mgr.on_quote(w.m, q(w.clock.t))                 # 2.35 + 2.35 > 4: only the bid goes out
    assert w.ops.n("insert") == 1
    skips = [r for r in lines(w.sinks["ops"]) if r["kind"] == "skip"]
    assert skips[0]["reason"] == "market_cap"
    w2 = manager(tmp_path / "b", limits=MakerLimits(market_cap=10.0, max_open=3.0))
    w2.mgr.on_quote(w2.m, q(w2.clock.t))
    assert w2.ops.n("insert") == 1 and lines(w2.sinks["ops"])[-1]["reason"] == "max_open"


def test_limits_cannot_be_raised():
    with pytest.raises(SystemExit):
        MakerLimits().lowered(max_open=30.0)
    with pytest.raises(SystemExit):
        MakerLimits().lowered(fanout=4)
    assert MakerLimits().lowered(max_open=10.0).max_open == 10.0


def test_gtd_expiry_at_least_180_s_ahead(tmp_path):
    w = manager(tmp_path)
    w.mgr.on_quote(w.m, q(w.clock.t, ask=0))
    o = w.ops.pending[0][1]
    assert o.expiration == int(w.clock.t) + 185 and o.expiration - w.clock.t >= 181
    w2 = manager(tmp_path / "b")
    w2.clock.t = START + 300 - 60                     # late in the market: still >= 180 s (venue minimum)
    w2.mgr.on_quote(w2.m, q(w2.clock.t, ask=0))
    assert w2.ops.pending[0][1].expiration - w2.clock.t >= 181
    w3 = manager(tmp_path / "c")
    w3.mgr.otype = "GTC"
    w3.mgr.on_quote(w3.m, q(w3.clock.t, ask=0))
    assert w3.ops.pending[0][1].expiration == 0 and w3.ops.pending[0][1].otype == "GTC"


def test_quote_crossing_our_book_is_not_sent(tmp_path):
    w = manager(tmp_path)
    w.mgr.book_of = lambda slug: w.m.book
    w.m.book.apply(START + 61, START + 61, False, [(-1, 47, 10.0)])    # ask now at our bid
    w.mgr.on_quote(w.m, q(w.clock.t, bid=47, ask=0))
    assert w.ops.n("insert") == 0 and lines(w.sinks["ops"])[-1]["reason"] == "would_cross"


def test_stop_cancels_everything(tmp_path):
    w = manager(tmp_path)
    w.mgr.on_quote(w.m, q(w.clock.t))
    w.ops.ack("insert")
    w.mgr.stop("kill")
    assert w.ops.n("cancel") == 1                      # the live one; the other cancels on its ack
    w.ops.ack("insert")
    assert w.ops.n("cancel") == 2 and w.mgr.stop_reason == "kill"
    w.mgr.on_quote(w.m, q(w.clock.t + 0.1))
    assert w.ops.n("insert") == 2


def test_tick_size_other_than_one_cent_never_quotes(tmp_path):
    w = manager(tmp_path)
    w.m.meta["tick"] = 0.001
    w.mgr.on_quote(w.m, q(w.clock.t))
    assert w.ops.n("insert") == 0
