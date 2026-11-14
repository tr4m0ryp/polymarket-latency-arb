"""Duplicate-send test, the CLI wiring of holdtest, and the hold / dup report sections."""
import json
import time
from types import SimpleNamespace

import httpx
import pytest

from recorder.live.sink import Sink
from btclat.trade import __main__ as cli
from btclat.trade.hold import dup
from btclat.trade.probe import run as probe
from btclat.trade.report import __main__ as rep
from btclat.trade.risk.session import Session
from btclat.trade.venue.fanout import Fanout
from btclat.trade.venue.http import Http
from btclat.trade.venue.signer import Signed

from .fakes import write_creds
from .hold_fakes import MKT, Clock, FakeFanout, HoldVenue, Markets


def go(v, f, tmp_path, reps=2):
    c, log = Clock(), []
    s = Session(v, tmp_path / "KILL", sleep=lambda x: None)
    with s:
        n = None
        n = dup.run(v, s, log.append, SimpleNamespace(every=30.0, dup_reps=reps), f, now=c.now, sleep=c.sleep,
                    markets=Markets())
    return n, log, s


def test_dup_dedup_safe(tmp_path):
    v, f = HoldVenue(), FakeFanout()
    n, log, s = go(v, f, tmp_path)
    assert f.posts == [1, 1, 2, 2, 3, 3] and n["reps"] == 6 and n["orders"] == 6 and n["copies"] == 12
    assert all(len(r["distinct_ids"]) == 1 and r["accepted"] == 1 for r in log)
    assert v.n("cancel") == 6 and v.n("sign") == 6 and s.exit_reason == "normal"
    signs = [c for c in v.calls if c[0] == "sign"]
    assert all(c[1] == "UP" and c[2] == 0.01 and c[5] == "GTC" and c[6] is True for c in signs)
    assert log[2]["copies"][1]["err_kind"] == "duplicate"


def test_dup_unsafe_aborts_and_cancels_each(tmp_path):
    v, f = HoldVenue(), FakeFanout(unsafe=True)
    n, log, s = go(v, f, tmp_path)
    assert f.posts == [1, 1, 2] and "distinct orders" in s.exit_reason
    assert len(log[-1]["distinct_ids"]) == 2 and v.n("cancel") == 4 and v.n("cancel_all") == 1


def test_cli_holdtest_dup(tmp_path, monkeypatch):
    write_creds(tmp_path)
    monkeypatch.setattr(probe.Markets, "current", lambda self, now, margin=20.0: MKT)
    monkeypatch.setattr(time, "sleep", lambda s: None)
    v, f = HoldVenue(), FakeFanout()
    clock = SimpleNamespace(now_ns=time.time_ns, offset_ns=0)
    cli.start(["holdtest", "--i-approve", "--dup", "--dup-reps", "1", "--every", "5", "--run", "d1"],
              venue_factory=lambda c, k: v, config=tmp_path, clock=clock, root=tmp_path / "runs",
              fanout_factory=lambda venue: f)
    assert f.closed and v.closed and f.posts == [1, 2, 3] and v.n("cancel_all") == 1
    text = rep.main(["--run", "d1", "--no-gamma"], root=tmp_path / "runs")
    assert "## Duplicate send" in text and "deduplicated" in text


def _write(root, name, rows):
    s = Sink(name, root=root, flush_s=0)
    for i, r in enumerate(rows):
        s.write(1_791_800_000_000_000_000 + i, json.dumps(r))
    s.close()


def test_report_hold_section(tmp_path):
    rows = [{"cycle": i // 2, "role": role, "type": t, "decision": "sent", "ack_ms": ms, "status_ack": st,
             "fill_sh": 5.0 if st == "matched" else 0.0, "spent": 0.26 if st == "matched" else 0.0,
             "hold_ms": 300.0 if st == "delayed" else None}
            for i, (role, t, ms, st) in enumerate([("marketable", "FAK", 270.0, "matched"), ("control", "GTC", 56.0, "live"),
                                                   ("marketable", "GTC", 60.0, "delayed"), ("control", "GTC", 57.0, "live")])]
    rows.append({"cycle": 2, "role": "skip", "decision": "skip:no_cheap_side"})
    _write(tmp_path / "h", "hold", rows)
    text = rep.main(["--run", "h", "--no-gamma"], root=tmp_path)
    assert "## Hold test" in text and "FAK: marketable ack p50 270 ms vs control 56 ms (+214 ms)" in text
    assert "skip:no_cheap_side 1" in text and "`delayed` orders" in text


def test_fanout_sends_identical_copies():
    seen = []

    def sess():
        h = Http()
        h.c = httpx.Client(transport=httpx.MockTransport(
            lambda req: (seen.append((req.content, req.headers["POLY_SIGNATURE"])), httpx.Response(200, json={"ok": 1}))[1]))
        return h
    venue = SimpleNamespace(post_headers=lambda s: {"POLY_SIGNATURE": "sig-" + s.body})
    f = Fanout(venue, sessions=[sess(), sess(), sess()])
    s = Signed('{"o":1}', 1.0, "T", 0.01, 5.0, "BUY", "GTC", True)
    rs = f.post(s, 3)
    f.close()
    assert len(rs) == 3 and all(r.code == 200 for r in rs)
    assert seen == [(b'{"o":1}', 'sig-{"o":1}')] * 3
    with pytest.raises(ValueError):
        Fanout(venue, k=4)
