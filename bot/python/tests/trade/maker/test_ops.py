"""Hedged sends and the live ops: first good copy wins, the most telling bad answer otherwise,
an insert nobody answered is `unknown`, the signed order must be the quote (post-only GTD BUY),
cancels confirmed by order id, every copy reported. No network: sessions are fakes."""
import threading
import time

import pytest

from btclat.trade.maker.ops.hedge import Hedge
from btclat.trade.maker.ops.live import LiveOps
from btclat.trade.maker.orders.slot import Working
from btclat.trade.venue.signer import Signed

from ..fakes import FakeVenue, resp

OK = {"success": True, "orderID": "0xabc", "status": "live", "makingAmount": "0", "takingAmount": "0"}
DUP = {"error": "order 0xabc is duplicated"}
CROSS = {"error": "invalid post-only order: order crosses book"}


class Sess:
    def __init__(self, code=200, body=None, delay=0.0):
        self.code, self.body, self.delay = code, body, delay
        self.reqs, self.last = [], None

    def req(self, method, path, headers=None, body=None, params=None, url=None):
        self.reqs.append((method, path, headers, body))
        time.sleep(self.delay)
        r = resp(code=self.code, body=self.body, path=path)
        if self.code == 0:
            r.err = "ConnectError"
        return r

    def close(self):
        pass


class MakerVenue(FakeVenue):
    def __init__(self, post_only=True, **kw):
        super().__init__(**kw)
        self.post_only = post_only

    def sign(self, token, price, size, side="BUY", order_type="FAK", post_only=False, expiration=0):
        self.calls.append(("sign", token, price, size, side, order_type, post_only, expiration))
        return Signed('{"o":1}', 1400.0, token, price, size, side, order_type, post_only and self.post_only)

    def post_headers(self, signed):
        return {"POLY_SIGNATURE": "h"}

    def cancel_req(self, oid):
        return '{"orderID":"%s"}' % oid, {"POLY_SIGNATURE": "c"}

    def server_now(self):
        return 1_791_800_150.0


def order():
    return Working("m0", "s", "bid", "UP", True, 47, 0.47, 5.0, 1_791_800_400.0, expiration=1_791_800_330)


def run_op(ops, kind, o):
    got, ev = [], threading.Event()
    getattr(ops, kind)(o, lambda res: (got.append(res), ev.set()))
    assert ev.wait(5)
    return got[0]


def test_first_good_copy_wins():
    h = Hedge(None, 2, sessions=[Sess(body=OK, delay=0.5), Sess(body=OK, delay=0.0)])
    t0 = time.monotonic()
    r, futs = h.send("POST", "/order", {}, "{}", lambda x: x.code == 200)
    assert time.monotonic() - t0 < 0.4 and r.code == 200 and len(futs) == 2
    h.close()


def test_all_bad_returns_the_telling_answer():
    h = Hedge(None, 3, sessions=[Sess(code=0), Sess(code=400, body=DUP), Sess(code=400, body=CROSS)])
    r, _ = h.send("POST", "/order", {}, "{}", lambda x: x.code == 200)
    assert r.body == CROSS
    h.close()
    with pytest.raises(ValueError):
        Hedge(None, 4, sessions=[Sess()] * 4)


def test_live_insert_post_only_gtd_on_all_copies():
    v, notes = MakerVenue(), []
    ss = [Sess(body=OK), Sess(code=400, body=DUP), Sess(code=400, body=DUP)]
    ops = LiveOps(v, Hedge(None, 3, sessions=ss), lambda fn, *a: fn(*a), lambda kind, **kw: notes.append((kind, kw)))
    res = run_op(ops, "insert", order())
    sign = [c for c in v.calls if c[0] == "sign"][0]
    assert sign[1:] == ("UP", 0.47, 5.0, "BUY", "GTD", True, 1_791_800_330)
    assert res["ok"] and res["order_id"] == "0xabc" and not res["unknown"] and res["k"] == 3
    ops.close()                                              # the other copies finish in the pool
    assert all(s.reqs[0][:2] == ("POST", "/order") and s.reqs[0][3] == '{"o":1}' for s in ss)
    assert notes and notes[-1][0] == "copies" and len(notes[-1][1]["copies"]) == 3


@pytest.mark.parametrize("sessions,unknown,kind", [
    ([(0, None), (0, None)], True, "transport"),
    ([(400, DUP), (502, {"error": "bad gateway"})], True, None),
    ([(400, CROSS), (400, DUP)], False, "post_only_crosses")])
def test_live_insert_unknown_only_without_a_definite_answer(sessions, unknown, kind):
    ops = LiveOps(MakerVenue(), Hedge(None, 2, sessions=[Sess(code=c, body=b) for c, b in sessions]),
                  lambda fn, *a: fn(*a))
    res = run_op(ops, "insert", order())
    assert not res["ok"] and res["unknown"] is unknown
    if kind:
        assert res["err_kind"] == kind
    ops.close()


def test_signed_order_must_be_post_only():
    ops = LiveOps(MakerVenue(post_only=False), Hedge(None, 1, sessions=[Sess(body=OK)]), lambda fn, *a: fn(*a))
    res = run_op(ops, "insert", order())
    assert "exc" in res and res["unknown"] and not res["ok"]
    ops.close()


def test_live_cancel_confirmed_by_id_and_lookup():
    o = order()
    o.oid = "0xabc"
    ss = [Sess(body={"canceled": ["0xabc"], "not_canceled": {}}), Sess(body={"canceled": [], "not_canceled": {"0xabc": "x"}})]
    v = MakerVenue()
    ops = LiveOps(v, Hedge(None, 2, sessions=ss), lambda fn, *a: fn(*a))
    res = run_op(ops, "cancel", o)
    assert res["confirmed"]
    v.lookups = [resp(body={"status": "LIVE", "size_matched": "2", "price": "0.47"})]
    q = run_op(ops, "lookup", o)
    assert q["fill_sh"] == 2.0 and q["unknown"] is False
    ops.close()
    assert all(s.reqs[0][:2] == ("DELETE", "/order") for s in ss)
    ss2 = [Sess(body={"canceled": [], "not_canceled": {"0xabc": "matched"}})]
    ops2 = LiveOps(v, Hedge(None, 1, sessions=ss2), lambda fn, *a: fn(*a))
    assert run_op(ops2, "cancel", o)["confirmed"] is False
    ops2.close()
