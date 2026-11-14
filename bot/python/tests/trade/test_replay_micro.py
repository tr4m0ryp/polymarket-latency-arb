"""End to end on a recorded hour (no network): the paper engine's real signals drive the live
leg against a fake CLOB. Every sent order is 5 shares at the arm's limit, inside every cap, and
every signal's line carries the paper prediction for the same 5-share order."""
import json

import pytest

from btclat.paper.engine.core import Engine
from btclat.paper.model.load import ValueModel
from btclat.paper.replay import source
from btclat.trade.micro.executor import LiveExec, make_send
from btclat.trade.micro.run import PRIMARY, mark_positions
from btclat.trade.micro.shadow import ShadowExec
from btclat.trade.risk.book import RiskBook
from btclat.trade.risk.limits import Limits

from .fakes import FakeVenue, InlineWorker, ListSink, resp

HOURS = (497697,)
STOP = HOURS[0] * 3600 + 2100           # markets from :15 on have 300 s of history: ~20 min of trading


class Matched(FakeVenue):
    def post(self, signed):
        self.calls.append(("post", signed))
        sh, cost = signed.size, round(signed.size * (signed.price - 0.01), 4)
        return resp(body={"success": True, "orderID": "0x1", "status": "matched",
                          "makingAmount": str(cost), "takingAmount": str(sh)})


@pytest.mark.skipif(not list(source.LIVE.glob(f"*/clob_5m-{HOURS[0]}.tsv.gz")), reason="recording not present")
def test_replay_drives_live_leg(tmp_path):
    clock = {"t": 0.0}
    v = Matched()
    rb = RiskBook(Limits(), tmp_path, now=HOURS[0] * 3600)
    rb.balance = 40.0
    orders, paper = ListSink(), ListSink()
    eng = Engine(ValueModel("v1_L0"), paper, "t", arms=[PRIMARY])
    lx = LiveExec(rb, InlineWorker(), make_send(v), orders, lambda: clock["t"])
    eng.paper = ShadowExec(paper, "t", lx.on_signal, lx.on_paper_final, 5.0)
    mk = source.markets(source.LIVE, HOURS)
    for ev in source.events(source.LIVE, HOURS, quantize=False, mk=mk):
        clock["t"] = ev[1]
        if ev[1] > STOP:
            break
        eng.on_event(ev)
        lx.advance(ev[1])
        mark_positions(rb, eng.world)
    eng.paper.flush()
    lx.flush()
    recs = [json.loads(r) for _, r in orders.lines]
    sent = [r for r in recs if r["decision"] == "sent"]
    assert len(recs) == len(paper.lines) > 0                        # one line per signal, both legs
    assert all(r["arm"] == PRIMARY for r in recs)
    assert 0 < len(sent) <= 40 and sum('"k": "send"' in x for x in rb.ledger.read_text().splitlines()) == len(sent)
    signs = [c for c in v.calls if c[0] == "sign"]
    assert len(signs) == len(sent)
    assert all(c[3] == 5.0 and c[5] == "FAK" and c[2] * 5 <= 3.0 + 1e-9 and c[2] * 5 >= 1.0 - 1e-9 for c in signs)
    for r in sent:
        assert r["limit"] == pytest.approx(round(r["seen"] + 0.02, 2))
        assert "paper" in r and r["paper"]["fill_sh"] <= 5.0
    skips = {r["decision"] for r in recs} - {"sent"}
    assert skips <= {"skip:max_notional", "skip:below_venue_min_notional", "skip:max_exposure",
                     "skip:max_orders_hour", "skip:balance", "skip:loss_headroom"}
    assert rb.exposure() <= 15.0 + 1e-9
