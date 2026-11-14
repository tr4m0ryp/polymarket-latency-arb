"""No matched order goes unseen: the 2026-10-14 $1.65 fill (order m34) replayed offline.

The venue matched m34 while its cancel was in flight; the cancel came back "can't be found -
already canceled or matched" and every GET /data/order answered 200 without the order. The bot
booked 0. Now: a not-found lookup is `unknown`, a "gone" cancel frees the slot but leaves the
order unsettled (its notional still counts), and the trade records (REST poll, user channel)
book the fill once. No network."""
import json

import pytest

from btclat.trade.maker.fills import userws
from btclat.trade.maker.fills.ledger import Ledger
from btclat.trade.maker.fills.live import LiveFills
from btclat.trade.maker.fills.settle import DEADLINE_S, STEPS_S, Settle
from btclat.trade.maker.ops.hedge import Hedge
from btclat.trade.maker.ops.live import LiveOps
from btclat.trade.venue import parse

from ..fakes import resp
from .fakes import lines, manager, q
from .test_ops import MakerVenue, Sess, order, run_op

OID = "0xabababababababababababababababababababababababababababababababab"
GONE = {"not_canceled": {OID: "order can't be found - already canceled or matched"}, "canceled": []}


def trade(oid, sh=5.0, tid="t1", status="MATCHED", px="0.33"):
    """A GET /data/trades object: someone took our resting order (a maker leg)."""
    return {"id": tid, "taker_order_id": "0xtaker", "size": "22.7", "price": "0.67", "status": status,
            "match_time": "1791986958", "market": "0x76ff", "asset_id": "DN",
            "maker_orders": [{"order_id": "0xother", "matched_amount": "17.7", "price": px},
                             {"order_id": oid, "matched_amount": str(sh), "price": px}]}


def test_parse_not_found_and_gone():
    assert parse.lookup(resp(body=None))["found"] is False
    assert parse.lookup(resp(body="null"))["found"] is False
    assert parse.lookup(resp(body={"status": "CANCELED", "size_matched": "0"}))["found"] is True
    assert parse.gone(resp(body=GONE), OID).startswith("order can't be found")
    assert parse.gone(resp(body={"canceled": [OID], "not_canceled": {}}), OID) is None
    assert parse.gone(resp(code=500, body=GONE), OID) is None


def test_live_ops_not_found_is_unknown_and_cancel_gone():
    o = order()
    o.oid = OID
    v = MakerVenue()
    ops = LiveOps(v, Hedge(None, 2, sessions=[Sess(body=GONE), Sess(body=GONE)]), lambda fn, *a: fn(*a))
    v.lookups = [resp(body=None)]
    assert run_op(ops, "lookup", o)["unknown"] is True
    res = run_op(ops, "cancel", o)
    assert res["confirmed"] is False and "can't be found" in res["gone"]
    ops.close()


def test_ledger_counts_each_trade_once_and_drops_failed():
    led, mine = Ledger(), {"0xa"}.__contains__
    assert led.add(trade("0xa"), mine) == ["0xa"] and led.total("0xa") == 5.0
    assert led.add(dict(trade("0xa"), status="CONFIRMED"), mine) == []          # same trade id again
    led.add(trade("0xa", sh=2.0, tid="t2"), mine)
    assert led.total("0xa") == 7.0
    assert led.add(trade("0xa", tid="t2", status="FAILED"), mine) == ["0xa"] and led.total("0xa") == 5.0
    assert led.add(trade("0xnotours", tid="t3"), mine) == [] and led.foreign == {"t3"}


def _m34(tmp_path):
    """Insert, pull while inserting, ack, cancel answered "gone", lookups without the order."""
    w = manager(tmp_path)
    w.ops.settles_late = True
    polls = []
    w.ops.trades = lambda after, cb: polls.append(cb)
    fl = LiveFills(w.ops, w.mgr, w.clock.now, w.log)
    st = Settle(w.ops, w.mgr, fl, w.clock.now, note=lambda kind, **kw: w.notes.append((kind, kw)))
    w.notes, w.st, w.polls = [], st, polls
    w.mgr.watchers = [fl, st]
    t = w.clock.t
    w.mgr.on_quote(w.m, q(t, bid=0, ask=67))
    w.mgr.on_quote(w.m, q(t + 0.1, bid=0, ask=0, pull_ask=True))      # pull fires; no order id yet
    o = w.ops.ack("insert", order_id=OID)                                # ack: cancel goes at once
    assert o.state == "cancelling"
    w.ops.ack("cancel", confirmed=False, gone="order can't be found - already canceled or matched")
    return w, o


def test_gone_cancel_frees_slot_but_counts_as_exposure(tmp_path):
    w, o = _m34(tmp_path)
    assert o.state == "done" and not o.settled and w.mgr.n["cancel_gone"] == 1
    assert w.mgr.unsettled() == [o] and o.at_risk == pytest.approx(5 * 0.33)
    assert w.mgr.exposed() == [o]
    w.ops.ack("lookup", status=None, fill_sh=0.0, unknown=True)          # "final": not found
    assert o.matched == 0 and not o.settled                             # never "0 matched"


def test_trade_records_book_the_missed_fill_once(tmp_path):
    w, o = _m34(tmp_path)
    w.ops.ack("lookup", status=None, fill_sh=0.0, unknown=True)
    w.st.on_tick(w.clock.t)                                             # first trades poll
    assert len(w.polls) == 1
    w.polls.pop()([trade(OID)])
    fills = [r for r in lines(w.sinks["fills"])] + [j[2] for j in w.log.jobs]
    assert o.matched == 5.0 and o.settled and len(fills) == 1 and fills[0]["src"] == "trades:rest"
    assert fills[0]["px"] == 0.33 and fills[0]["shares"] == 5.0
    assert w.risk.exposure() == pytest.approx(1.65)                      # the position is on the books
    w.st.on_user(dict(trade(OID), event_type="trade"))                  # the user channel saw it too
    assert o.matched == 5.0 and w.mgr.n["fills"] == 1
    assert [k for k, _ in w.notes] == ["fill_found"]


def test_unsettled_retries_lookups_then_deadline_settles(tmp_path):
    w, o = _m34(tmp_path)
    w.ops.ack("lookup", status=None, fill_sh=0.0, unknown=True)
    t_off = w.clock.t
    for dt in STEPS_S:
        w.clock.t = t_off + dt
        w.st.on_tick(w.clock.t)
        w.ops.ack("lookup", status=None, fill_sh=0.0, unknown=True)
    assert w.ops.n("lookup") == 1 + len(STEPS_S) and not o.settled
    w.polls.pop()([])                                                   # sent before the deadline
    assert not o.settled and not w.polls
    w.clock.t = t_off + DEADLINE_S + 2 * 2.0
    w.st.on_tick(w.clock.t)
    w.polls.pop()([])                                                   # the venue has no trade on it
    assert o.settled and o.matched == 0 and w.mgr.exposed() == []


def test_definitive_lookup_or_ws_cancellation_settles(tmp_path):
    w, o = _m34(tmp_path)
    w.ops.ack("lookup", status="LIVE", fill_sh=0.0)                     # stale read: not final
    assert not o.settled
    w.st.on_tick(w.clock.t + STEPS_S[0])
    w.ops.ack("lookup", status="CANCELED", fill_sh=0.0)
    assert o.settled and o.matched == 0
    w2, o2 = _m34(tmp_path / "b")
    w2.st.on_user({"event_type": "order", "id": OID, "type": "CANCELLATION", "size_matched": "0"})
    assert o2.settled and o2.matched == 0


def test_final_reconcile_reports_mismatch_and_foreign(tmp_path):
    w, o = _m34(tmp_path)
    rec = w.st.final([trade(OID), trade("0xnotours", tid="t9")])
    assert o.matched == 5.0 and rec["matched_sh"] == 5.0 and rec["mismatch"] == {}
    assert rec["foreign_trades"] == ["t9"] and rec["read_ok"] is True
    assert w.st.final(None)["read_ok"] is False


def test_user_channel_frames():
    assert userws.events("PONG") == []
    evs = userws.events(json.dumps([{"event_type": "trade", "id": "t"}, {"x": 1}]))
    assert evs == [{"event_type": "trade", "id": "t"}]
    h = json.loads(userws.hello({"key": "k", "secret": "s", "passphrase": "p"}))
    assert h["type"] == "user" and h["auth"] == {"apiKey": "k", "secret": "s", "passphrase": "p"}


def test_report_reconcile_line():
    from btclat.trade.report.maker.section import reconcile
    ns = [{"kind": "fill_found"}, {"kind": "reconcile", "read_ok": True, "orders": 36, "matched_orders": 1,
                                   "matched_sh": 5.0, "mismatch": {}, "foreign_trades": [], "unsettled": [],
                                   "booked_sh": 5.0, "public": {"trades": 1, "shares": 5.0, "usdc": 1.65}}]
    out = reconcile(ns)
    assert "matched orders 1" in out[0] and "found by the trade records / user channel: 1" in out[0]
    assert "1 trades, 5 sh, $1.65 vs booked 5 sh" in out[1]
    assert reconcile([]) == []
