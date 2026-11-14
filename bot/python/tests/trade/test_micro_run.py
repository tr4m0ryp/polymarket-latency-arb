"""Micro mode wired end to end through the CLI with the feeds stubbed out (no network): the
kill file stops the loop within a tick, cancel-all goes out, the session log says why."""
import asyncio
import json
import time

from recorder.live.sink import read_stream
from btclat.trade import __main__ as cli
from btclat.trade.micro import run as micro

from .fakes import FakeVenue, write_creds


class Clock:
    offset_ns = 0

    def now_ns(self):
        return time.time_ns()

    def now(self):
        return time.time()

    def sync(self):
        return True


def test_micro_kill_file_stops_and_cancels(tmp_path, monkeypatch):
    write_creds(tmp_path)
    kill = tmp_path / "KILL"

    async def feed(*a, **k):            # stands in for the Binance sockets: touch the kill file
        await asyncio.sleep(0.3)
        kill.touch()
        await asyncio.sleep(3600)

    async def markets(*a, **k):
        await asyncio.sleep(3600)
    monkeypatch.setattr(micro.live, "binance", feed)
    monkeypatch.setattr(micro.live, "markets", markets)
    v = FakeVenue()
    t0 = time.time()
    rc = cli.start(["micro", "--i-approve", "--run", "t1", "--hours", "0.01"], venue_factory=lambda c, k: v,
                   config=tmp_path, clock=Clock(), root=tmp_path / "runs")
    assert rc == 0 and time.time() - t0 < 20
    assert v.n("cancel_all") == 1 and v.n("post") == 0
    ev = [json.loads(r) for _, r in read_stream("events", root=tmp_path / "runs" / "t1")]
    end = [e for e in ev if e["kind"] == "session_end"][0]
    assert "kill file" in end["reason"] and end["cancel_all_ok"] is True
    feed_notes = [json.loads(r)["kind"] for _, r in read_stream("feed", root=tmp_path / "runs" / "t1")]
    assert "trade_start" in feed_notes and "trade_stop" in feed_notes


def test_micro_hours_end_is_normal(tmp_path, monkeypatch):
    write_creds(tmp_path)

    async def idle(*a, **k):
        await asyncio.sleep(3600)
    monkeypatch.setattr(micro.live, "binance", idle)
    monkeypatch.setattr(micro.live, "markets", idle)
    v = FakeVenue()
    cli.start(["micro", "--i-approve", "--run", "t2", "--hours", "0.0003"], venue_factory=lambda c, k: v,
              config=tmp_path, clock=Clock(), root=tmp_path / "runs")
    ev = [json.loads(r) for _, r in read_stream("events", root=tmp_path / "runs" / "t2")]
    assert [e for e in ev if e["kind"] == "session_end"][0]["reason"] == "normal" and v.n("cancel_all") == 1
