"""Hold test: cheap-side choice, order-type rotation, unfillable controls, caps and stops."""
from types import SimpleNamespace

import pytest

from btclat.trade.hold import run as hold
from btclat.trade.risk.limits import HARD_HOLD_BUDGET
from btclat.trade.risk.session import Session

from .fakes import resp
from .hold_fakes import SERVER_NOW, Clock, HoldVenue, Markets


def args(**kw):
    d = {"every": 30.0, "n": 4, "hours": None, "ask_band": None}
    d.update(kw)
    return SimpleNamespace(**d)


def go(v, tmp_path, a=None):
    c, log = Clock(), []
    s = Session(v, tmp_path / "KILL", sleep=lambda x: None)
    with s:
        n = None
        n = hold.run(v, s, log.append, a or args(), now=c.now, sleep=c.sleep, markets=Markets())
    return n, log, s


def _b(ba):
    return {"bb": ba - 0.01, "ba": ba}


def test_pick_and_band():
    assert hold.pick({"A": _b(0.05), "B": _b(0.95)}, 0.02, 0.08) == "A"
    assert hold.pick({"A": _b(0.07), "B": _b(0.03)}, 0.02, 0.08) == "B"
    assert hold.pick({"A": _b(0.10), "B": _b(float("nan"))}, 0.02, 0.08) is None
    assert hold.band(None) == (0.02, 0.08) and hold.band("0.20,0.30") == (0.2, 0.3)
    for bad in ("0.20,0.40", "0.01,0.05", "0.08,0.02"):
        with pytest.raises(SystemExit):
            hold.band(bad)


def test_rotation_controls_and_follow_up(tmp_path):
    v = HoldVenue()
    n, log, s = go(v, tmp_path)
    mk = [r for r in log if r["role"] == "marketable"]
    ct = [r for r in log if r["role"] == "control"]
    assert [r["type"] for r in mk] == ["FAK", "FOK", "GTC", "GTD"] and len(ct) == 4
    signs = [c for c in v.calls if c[0] == "sign"]
    assert all(c[2] == 0.05 and c[3] == 21.0 and c[6] is False for c in signs if c[1] == "DN")   # $1.05
    assert all(c[2] == 0.01 and c[3] == 5.0 and c[5] == "GTC" and c[6] is True for c in signs if c[1] == "UP")
    gtd = next(c for c in signs if c[5] == "GTD")
    assert gtd[7] == int(SERVER_NOW) + hold.GTD_S
    assert [r["status_ack"] for r in mk] == ["matched", "fok_killed", "delayed", "live"]
    gtc = mk[2]
    assert gtc["hold_ms"] is not None and len(gtc["polls"]) == 2 and gtc["cancelled"] and gtc["fill_sh"] == 2.0
    assert mk[3]["cancelled"] and all(r["cancelled"] for r in ct)
    assert log[0]["role"] == "control" and log[2]["role"] == "marketable"     # order alternates by cycle
    assert n["spent"] == pytest.approx(mk[0]["spent"] + gtc["spent"]) and mk[0]["spent"] == pytest.approx(1.05 + 0.07 * 0.05 * 0.95 * 21)
    assert s.cancel_all_ok


def test_budget_caps_spend(tmp_path):
    v = HoldVenue(ask=0.30, fill_all=True)
    n, log, s = go(v, tmp_path, args(n=40, ask_band="0.20,0.30"))
    assert n["spent"] <= HARD_HOLD_BUDGET and n["marketable"] == 3
    assert log[-1]["decision"] == "stop:budget"


@pytest.mark.parametrize("ask,sh", [(0.02, 53), (0.05, 21), (0.07, 15), (0.08, 14), (0.20, 6), (0.30, 5)])
def test_size_just_over_one_dollar(ask, sh):
    assert hold.size_for(ask) == sh and 1.05 - 1e-9 <= sh * ask <= hold.HARD_HOLD_MAX_NOTIONAL


def test_budget_at_default_band(tmp_path):
    v = HoldVenue(ask=0.05, fill_all=True)
    n, log, _ = go(v, tmp_path, args(n=40))
    assert n["marketable"] == 4 and n["spent"] <= HARD_HOLD_BUDGET and log[-1]["decision"] == "stop:budget"


def test_skips_without_cheap_side(tmp_path):
    v = HoldVenue(ask=0.50)
    n, log, _ = go(v, tmp_path, args(hours=0.01))
    assert n["marketable"] == 0 and v.n("post") == 0 and log[0]["decision"] == "skip:no_cheap_side"


def _reject(code, msg):
    return lambda s, oid: None if s.post_only else resp(code=code, body={"error": msg})


@pytest.mark.parametrize("code,msg,stop", [
    (400, "invalid amount for a marketable BUY order ($0.25), min size: $1", "minimum notional"),
    (403, "Trading restricted in your region", "geoblock")])
def test_stops_on_min_notional_and_region(tmp_path, code, msg, stop):
    v = HoldVenue(post_fn=_reject(code, msg))
    n, log, s = go(v, tmp_path)
    assert stop in s.exit_reason and v.n("cancel_all") == 1
    assert len([r for r in log if r["role"] == "marketable"]) == 1


def test_stops_on_control_fill(tmp_path):
    fill = resp(body={"success": True, "orderID": "0xc", "status": "matched", "makingAmount": "0.05", "takingAmount": "5"})
    v = HoldVenue(post_fn=lambda s, oid: fill if s.post_only else None)
    _, log, s = go(v, tmp_path)
    assert "control" in s.exit_reason and v.n("cancel_all") == 1


def test_stops_on_unconfirmed_cancel(tmp_path):
    v = HoldVenue(cancel_ok=False)
    _, log, s = go(v, tmp_path)
    assert "not confirmed" in s.exit_reason and len(log) == 1
