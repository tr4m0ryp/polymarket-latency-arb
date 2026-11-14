"""Maker mode through the CLI with the feeds stubbed (no network): dry needs no credentials and
stops on the kill file; live refuses without --i-approve and, approved, sends cancel-all on the
way out; the engine hands book messages and decision instants to the maker. Plus the rule."""
import asyncio
import json
import math
import time

import pytest

from recorder.live.sink import read_stream
from btclat.trade import __main__ as cli
from btclat.trade.gate.preflight import Refused
from btclat.trade.maker import arm, cli as mcli, run as mrun
from btclat.trade.maker.decide import MakerEngine

from ..fakes import write_creds
from .fakes import START
from .test_ops import MakerVenue, Sess


class Clock:
    offset_ns = 0

    def now_ns(self):
        return time.time_ns()

    def now(self):
        return time.time()

    def sync(self):
        return True


def _stub_feeds(monkeypatch, kill=None):
    async def feed(*a, **k):
        await asyncio.sleep(0.3)
        if kill is not None:
            kill.touch()
        await asyncio.sleep(3600)

    async def idle(*a, **k):
        await asyncio.sleep(3600)
    monkeypatch.setattr(mrun.live, "binance", feed)
    monkeypatch.setattr(mrun.live, "markets", idle)


def _events(root, name="events"):
    return [json.loads(r) for _, r in read_stream(name, root=root)]


def test_rule_on_one_row():
    r = {"t": 0.0, "pm_bb": 45.0, "pm_ba": 55.0, "pm_mid": 0.5, "secs_left": 100.0, "fair_p": 0.6}
    assert arm.quote(r, -0.05, -0.05) == {"bid": 54, "ask": 63, "pull_bid": False, "pull_ask": False}
    assert arm.quote(dict(r, fair_p=0.5), -0.05, -0.01)["bid"] == 0        # pd >= pull drops the Up bid
    assert arm.quote(dict(r, fair_p=0.5), -0.02, -0.05)["ask"] == 0        # pu >= pull drops the Up ask
    for bad, why in ((dict(r, secs_left=29.0), "tleft"), (dict(r, pm_mid=0.95), "band"), (dict(r, fair_p=math.nan), "fair")):
        qq = arm.quote(bad, -0.05, -0.05)
        assert qq["bid"] == qq["ask"] == 0
        qq.update(mid=bad["pm_mid"], secs_left=bad["secs_left"], fair=bad["fair_p"], bb=45, ba=55)
        assert arm.cause(qq, "bid") == why
    assert arm.price("bid", 47) == 0.47 and arm.price("ask", 53) == 0.47 and arm.MODEL == "v1_L50"


def test_engine_routes_book_and_quotes():
    books, quotes = [], []
    eng = MakerEngine(lambda r: (0.0, 0.0), lambda m, q: quotes.append(q), lambda m, t, ts: books.append((t, ts)))
    meta = {"slug": "s", "up": "UP", "down": "DN", "start": START, "end": START + 300, "tick": 0.01}
    eng.on_event(("mk", START - 60, meta))
    eng.on_event(("pm", START + 10, START + 9.99, "s", True, [(1, 45, 10.0), (-1, 55, 10.0)]))
    assert books == [(START + 10, START + 9.99)]
    eng.tradable = lambda m, t: True
    eng.decider.decide = lambda kind, flag, t, m: {"t": t, "kind": kind}
    eng.on_event(("pb", START + 11, START + 11, 1e5, 1e5 + 0.1, 1.0, 1.0))
    eng.on_event(("pb", START + 400, START + 400, 1e5, 1e5 + 0.1, 1.0, 1.0))     # after the market
    assert quotes == [{"t": START + 11, "kind": "pb"}]


def test_dry_needs_no_credentials_and_stops_on_kill(tmp_path, monkeypatch):
    monkeypatch.setattr(mcli, "GUARD", False)
    _stub_feeds(monkeypatch, kill=tmp_path / "KILL")
    rc = cli.start(["maker", "--dry", "--run", "d1", "--hours", "0.01"], config=tmp_path, clock=Clock(),
                   root=tmp_path / "runs")
    out = tmp_path / "runs" / "d1"
    end = [e for e in _events(out) if e["kind"] == "session_end"][0]
    assert rc == 0 and "kill file" in end["reason"] and end["cancel_all_ok"] is True
    feed = [e["kind"] for e in _events(out, "feed")]
    assert "trade_start" in feed and "trade_stop" in feed
    start = [e for e in _events(out, "feed") if e["kind"] == "trade_start"][0]
    assert start["dry"] is True and start["model"] == "v1_L50" and start["arm"] == arm.NAME
    assert (out / "drystate").is_dir() and not (tmp_path / "state").exists()
    with pytest.raises(Refused):                     # the kill file now blocks the next start
        cli.start(["maker", "--dry", "--run", "d2"], config=tmp_path, clock=Clock(), root=tmp_path / "runs")


def test_live_maker_refuses_without_approval(tmp_path):
    write_creds(tmp_path)
    with pytest.raises(Refused):
        cli.start(["maker", "--run", "x"], venue_factory=lambda c, k: MakerVenue(), config=tmp_path, clock=Clock(),
                  root=tmp_path / "runs")


def test_live_maker_kill_cancels_all(tmp_path, monkeypatch):
    write_creds(tmp_path)
    _stub_feeds(monkeypatch, kill=tmp_path / "KILL")
    v, made = MakerVenue(), []

    def hedge(venue):
        from btclat.trade.maker.ops.hedge import Hedge
        made.append(Hedge(None, 3, sessions=[Sess(), Sess(), Sess()]))
        return made[-1]
    rc = cli.start(["maker", "--i-approve", "--run", "l1", "--hours", "0.01"], venue_factory=lambda c, k: v,
                   config=tmp_path, clock=Clock(), root=tmp_path / "runs", fanout_factory=hedge)
    ev = _events(tmp_path / "runs" / "l1")
    end = [e for e in ev if e["kind"] == "session_end"][0]
    assert rc == 0 and "kill file" in end["reason"] and v.n("cancel_all") == 1 and v.n("post") == 0
    assert made and all(s.reqs and s.reqs[0][:2] == ("GET", "/time") for s in made[0].sessions)   # kept warm
    with pytest.raises(SystemExit):
        cli.start(["maker", "--i-approve", "--run", "l2", "--max-open", "40"], venue_factory=lambda c, k: v,
                  config=tmp_path, clock=Clock(), root=tmp_path / "runs")
