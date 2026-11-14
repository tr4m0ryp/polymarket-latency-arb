"""Micro mode's live leg: caps before sending, ack parsing, 10 s mark, join with the paper record."""
import json

import pytest

from btclat.trade.micro.executor import LiveExec, make_send
from btclat.trade.risk.book import RiskBook
from btclat.trade.risk.limits import Limits

from .fakes import FakeVenue, InlineWorker, ListSink, market, resp

NOW = 1_791_800_000.0


def order(sig="r:0", limit=0.52, side=1, t=NOW + 100):
    return {"sig": sig, "arm": "vt_v1_m0.03_any", "t": t, "side": side, "shares": 5.0, "limit": limit,
            "edge": 0.04, "seen": limit - 0.02, "value": 0.04}


def setup(tmp_path, post=None, worker=None):
    v = FakeVenue(post=post)
    rb = RiskBook(Limits(), tmp_path, now=NOW)
    sink = ListSink()
    clock = {"t": NOW + 100.001}
    lx = LiveExec(rb, worker or InlineWorker(), make_send(v, sleep=lambda s: None), sink, lambda: clock["t"])
    return v, rb, sink, lx, clock


MATCHED = resp(body={"success": True, "orderID": "0xo", "status": "matched", "makingAmount": "2.6",
                     "takingAmount": "5", "tradeIDs": ["t1"]}, ms=180.0)


def test_fill_mark_and_join(tmp_path):
    v, rb, sink, lx, clock = setup(tmp_path, post=MATCHED)
    m = market(start=NOW, bb=48, ba=50)
    lx.on_signal(order(), m, "pb", NOW + 99.99, 900.0)
    s = [c for c in v.calls if c[0] == "sign"][0]
    assert s[1:7] == ("UP", 0.52, 5.0, "BUY", "FAK", False)
    assert rb.exposure() == pytest.approx(2.6 + 0.07 * 0.52 * 0.48 * 5)
    assert sink.lines == []                                   # waits for the 10 s mark and the paper record
    m.book.bb, m.book.ba = 54, 56
    lx.advance(MATCHED.t_ack_ns / 1e9 + 10)
    lx.on_paper_final({"sig": "r:0", "fill_sh": 5.0, "px": 0.51, "cost": 2.55, "fee": 0.087, "mk10": 0.55})
    rec = json.loads(sink.lines[0][1])
    assert rec["decision"] == "sent" and rec["fill_sh"] == 5 and rec["px"] == pytest.approx(0.52)
    assert rec["mk10_live"] == pytest.approx(0.55) and rec["book10"]["bb"] == 54
    assert rec["paper"]["px"] == 0.51 and rec["paper_mk10_cpd"] == pytest.approx(100 * (2.75 - 2.55 - 0.087) / 2.55)
    assert rec["live_mk10_cpd"] == pytest.approx(100 * (2.75 - 2.6 - rec["fee"]) / 2.6)
    assert rec["t_send_ns"] and rec["t_ack_ns"] - rec["t_send_ns"] == int(180e6) and rec["sign_us"] == 1400.0


def test_down_side_uses_down_token(tmp_path):
    v, *_ , lx, _ = setup(tmp_path, post=MATCHED)
    lx.on_signal(order(side=-1, limit=0.50), market(start=NOW), "pb", NOW, 1.0)
    assert [c for c in v.calls if c[0] == "sign"][0][1] == "DN"


@pytest.mark.parametrize("limit,reason", [(0.65, "max_notional"), (0.15, "below_venue_min_notional")])
def test_cap_skips_without_sending(tmp_path, limit, reason):
    v, rb, sink, lx, _ = setup(tmp_path)
    lx.on_signal(order(limit=limit), market(start=NOW), "pb", NOW, 1.0)
    lx.on_paper_final({"sig": "r:0", "fill_sh": 0.0})
    assert v.n("post") == 0 and json.loads(sink.lines[0][1])["decision"] == f"skip:{reason}"


def test_busy_worker_skips(tmp_path):
    class Busy(InlineWorker):
        busy = True
    v, rb, sink, lx, _ = setup(tmp_path, worker=Busy())
    lx.on_signal(order(), market(start=NOW), "pb", NOW, 1.0)
    assert v.n("post") == 0 and lx.pending["r:0"]["decision"] == "skip:busy" and rb.sends == type(rb.sends)()


def test_fak_no_match(tmp_path):
    no = resp(code=400, body={"error": "no orders found to match with FAK order. FAK orders are partially "
                                       "filled or killed if no match is found."})
    v, rb, sink, lx, _ = setup(tmp_path, post=no)
    lx.on_signal(order(), market(start=NOW), "pb", NOW, 1.0)
    lx.on_paper_final({"sig": "r:0", "fill_sh": 5.0, "px": 0.5, "cost": 2.5, "fee": 0.08, "mk10": 0.5})
    rec = json.loads(sink.lines[0][1])
    assert rec["err_kind"] == "fak_no_match" and rec["fill_sh"] == 0 and rb.exposure() == 0
    assert lx.stop_reason is None and len(rb.sends) == 1


def test_fatal_error_stops(tmp_path):
    bad = resp(code=400, body={"error": "'0xabc' address in closed only mode"})
    v, rb, sink, lx, _ = setup(tmp_path, post=bad)
    lx.on_signal(order(), market(start=NOW), "pb", NOW, 1.0)
    assert "closed_only" in lx.stop_reason
    lx.on_signal(order(sig="r:1"), market(start=NOW), "pb", NOW, 1.0)
    assert lx.pending["r:1"]["decision"] == "skip:stopped" and v.n("post") == 1


def test_delayed_order_is_looked_up(tmp_path):
    d = resp(body={"success": True, "orderID": "0xd", "status": "delayed", "makingAmount": "0", "takingAmount": "0"})
    v, rb, sink, lx, _ = setup(tmp_path, post=d)
    lx.on_signal(order(), market(start=NOW), "pb", NOW, 1.0)
    rec = lx.pending["r:0"]
    assert v.n("get_order") == 1 and rec["fill_sh"] == 5 and rec["px_src"] == "order_lookup"


def test_flush_writes_unfinished(tmp_path):
    v, rb, sink, lx, _ = setup(tmp_path, post=MATCHED)
    lx.on_signal(order(), market(start=NOW), "pb", NOW, 1.0)
    lx.flush()
    rec = json.loads(sink.lines[0][1])
    assert rec["final"] is False and "paper" not in rec
