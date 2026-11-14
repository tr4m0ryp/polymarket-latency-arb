"""The quote rule switch (`--rule inside`, `--hyst`): the inside gate on one row, its causes
(outside, hyst), the per-market insert hysteresis through the bot path (decider -> rule ->
order manager), refusals, and the rule in the run notes."""
import pytest

from btclat.trade import __main__ as cli
from btclat.trade.gate.preflight import Refused
from btclat.trade.maker import arm, cli as mcli, decide, rules
from btclat.trade.maker.decide import MakerEngine

from .fakes import START, lines, manager, market
from .test_run import Clock, _events, _stub_feeds

ROW = {"t": 0.0, "pm_bb": 45.0, "pm_ba": 55.0, "pm_mid": 0.5, "secs_left": 100.0, "fair_p": 0.5}


def _ctx(q, r):
    return dict(q, mid=r["pm_mid"], secs_left=r["secs_left"], fair=r["fair_p"], bb=r["pm_bb"], ba=r["pm_ba"])


def test_inside_quote_on_one_row():
    q = rules.Inside().quote(ROW, -0.05, -0.05, "s")
    assert (q["bid"], q["ask"], q["pull_bid"], q["pull_ask"]) == (46, 54, False, False)   # fair -/+ 0.04, inside
    assert q["rule"] == "inside" and q["h"] == 0.0
    r = dict(ROW, fair_p=0.6)                    # bid min(56, ba - 1) = 54 inside; ask 64 >= ba: not inside
    q = rules.Inside().quote(r, -0.05, -0.05, "s")
    assert (q["bid"], q["ask"], q["raw_ask"]) == (54, 0, 64)
    assert arm.cause(_ctx(q, r), "ask") == "outside" and arm.cause(_ctx(q, r), "bid") == "rule"
    q = rules.Inside().quote(ROW, -0.05, -0.019, "s")      # pdn >= pull -0.02 drops the bid
    assert q["bid"] == 0 and q["pull_bid"] and arm.cause(_ctx(q, ROW), "bid") == "pull"
    q = rules.Inside().quote(ROW, -0.025, -0.025, "s")     # -0.025 < -0.02: the frozen -0.03 would pull
    assert q["bid"] == 46 and q["ask"] == 54 and arm.quote(ROW, -0.025, -0.025)["bid"] == 0


def test_names_and_frozen_unchanged():
    assert rules.Inside().name == "vi_fair0.04_p-0.02" and rules.Inside(0.005).name == "vi_fair0.04_p-0.02_h0.005"
    fz = rules.of()
    assert fz.name == arm.NAME == "vm_fair0.03_p-0.03" and fz.quote(ROW, -0.05, -0.05) == arm.quote(ROW, -0.05, -0.05)
    assert "rule" not in fz.quote(ROW, -0.05, -0.05)                        # frozen quotes rows stay as they were
    for bad in (("frozen", 0.005), ("inside", -0.01), ("inside", float("nan"))):
        with pytest.raises(Refused):
            rules.of(*bad)


def _bot(tmp_path, h=0.005):
    """Decider with the inside rule, its row and model scores set by the test, feeding a manager."""
    w = manager(tmp_path)
    pred = {"pu": -0.05, "pdn": -0.05}
    eng = MakerEngine(lambda r: (pred["pu"], pred["pdn"]), w.mgr.on_quote, rule=rules.Inside(h))
    eng.decider._vt_candidate = lambda kind, flag, t, st: True
    return w, eng.decider, pred


def _bid_causes(w):
    return [(r["tick"], r["cause"]) for r in lines(w.sinks["quotes"]) if r["side"] == "bid"]


def test_hysteresis_entry_exit_and_reset(tmp_path, monkeypatch):
    monkeypatch.setattr(decide, "row", lambda t, ctx, m: dict(ROW, t=t))
    w, dec, pred = _bot(tmp_path)
    a, b = w.m, market(START + 300)
    t = START + 10
    for pdn in (-0.022, -0.03, -0.022, -0.019, -0.022, -0.03):
        pred["pdn"] = pdn
        t += 0.1
        w.mgr.on_quote(a, dec.decide("pb", False, t, a))
    # -0.022: in the band [pull - h, pull): held; -0.03 enters; -0.022 stays; -0.019 pulls; -0.022 held
    assert _bid_causes(w) == [(46, "rule"), (0, "pull"), (46, "rule")]
    assert dec.rule.on[a.meta["slug"]]["bid"] is True
    qs = lines(w.sinks["quotes"])
    assert qs[0]["rule"] == "inside" and qs[0]["h"] == 0.005
    pred["pdn"] = -0.022                          # a new market starts idle: held, not carried over
    q = dec.decide("pb", False, START + 310, b)
    assert q["bid"] == 0 and q["in_bid"] == 46 and arm.cause(q, "bid") == "hyst" and q["ask"] == 54
    assert dec.rule.on[b.meta["slug"]] == {"bid": False, "ask": True}
    assert dec.rule.on[a.meta["slug"]]["bid"] is True               # per market: the old one kept its own


def test_hysteresis_cause_logged_by_manager(tmp_path, monkeypatch):
    monkeypatch.setattr(decide, "row", lambda t, ctx, m: dict(ROW, t=t))
    w, dec, pred = _bot(tmp_path)
    pred["pdn"] = -0.03
    w.mgr.on_quote(w.m, dec.decide("pb", False, START + 10, w.m))
    w.ops.ack("insert")
    w.ops.ack("insert")
    w.mgr.on_quote(w.m, dict(dec.decide("pb", False, START + 10.1, w.m)))     # stays on: no change
    assert _bid_causes(w) == [(46, "rule")]


def test_cli_refuses_hyst_with_frozen(tmp_path):
    for argv in (["maker", "--dry", "--run", "x", "--hyst", "0.005"],
                 ["maker", "--i-approve", "--run", "y", "--rule", "frozen", "--hyst", "0.005"]):
        with pytest.raises(Refused, match="frozen arm stays frozen"):
            cli.start(argv, config=tmp_path, clock=Clock(), root=tmp_path / "runs")
    assert not (tmp_path / "runs").exists()


def test_dry_run_notes_the_inside_rule(tmp_path, monkeypatch):
    monkeypatch.setattr(mcli, "GUARD", False)
    _stub_feeds(monkeypatch, kill=tmp_path / "KILL")
    rc = cli.start(["maker", "--dry", "--rule", "inside", "--hyst", "0.005", "--run", "d1", "--hours", "0.01"],
                   config=tmp_path, clock=Clock(), root=tmp_path / "runs")
    out = tmp_path / "runs" / "d1"
    start = [e for e in _events(out, "feed") if e["kind"] == "trade_start"][0]
    pre = [e for e in _events(out) if e["kind"] == "preflight"][0]
    assert rc == 0 and start["arm"] == "vi_fair0.04_p-0.02_h0.005" and start["rule"] == "inside"
    assert start["h"] == 0.005 and start["model"] == "v1_L50" and start["money_caps"] == "would-skip (dry)"
    assert pre["rule"] == "inside" and pre["h"] == 0.005
