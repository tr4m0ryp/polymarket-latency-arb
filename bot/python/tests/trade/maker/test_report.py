"""The maker report on a synthetic run: fills per hour, 10 s and resolution markouts, the
adverse-selection split, ack round trips (first copy and every copy), real vs inferred fills,
the simulator reference row."""
import json

import pytest

from recorder.live.sink import Sink
from btclat.trade.report import __main__ as rep
from btclat.trade.report.maker import load, section

T0 = 1_791_800_000


def _write(root, name, rows, t=lambda r: T0):
    s = Sink(name, root=root, flush_s=0)
    for r in rows:
        s.write(int(t(r) * 1e9), json.dumps(r))
    s.close()


def _run(root, n=20, dry=False):
    slug = lambda i: f"btc-updown-5m-{T0 + 300 * (i // 5)}"          # noqa: E731
    fills = [{"t_fill": T0 + 60 * i, "slug": slug(i), "side": "bid" if i % 2 else "ask", "up": bool(i % 2),
              "cid": f"m{i}", "shares": 5.0, "px": 0.40, "cost": 2.0, "fee": 0.0, "mk10": 0.45 if i % 4 else 0.30,
              "pull_1s": i % 4 == 0, "src": "lookup:trade", "dry": dry, "final": True, "end": T0 + 300} for i in range(n)]
    _write(root, "fills", fills, lambda r: r["t_fill"])
    _write(root, "settle", [{"slug": slug(i), "outcome": 1.0, "end": 0} for i in range(0, n, 5)])
    orders = []
    for i in range(n):
        base = {"cid": f"m{i}", "slug": slug(i), "side": "bid", "tick": 40, "t_dec": T0 + 60 * i}
        orders += [dict(base, kind="insert"),
                   dict(base, kind="insert_ack", ok=i != 3, err_kind=None if i != 3 else "post_only_crosses", ms=40.0 + i,
                        t_send_ns=int((T0 + 60 * i + 0.002) * 1e9)),
                   dict(base, kind="cancel"), dict(base, kind="cancel_ack", confirmed=True, ms=30.0 + i)]
    orders.append({"kind": "skip", "cid": "x", "reason": "market_cap", "slug": slug(0)})
    _write(root, "ops", orders)
    _write(root, "quotes", [{"t": T0 + 60 * i, "slug": slug(i), "side": "bid", "tick": 40, "cause": "rule"} for i in range(n)])
    _write(root, "infer", [{"cid": f"m{i}", "shares": 5.0, "how": "trade"} for i in range(0, n, 2)])
    feed = [{"kind": "trade_start", "dry": dry, "arm": "vm_fair0.03_p-0.03", "model": "v1_L50"},
            {"kind": "copies", "what": "insert", "cid": "m0", "copies": [{"ms": 41.0}, {"ms": 90.0}, {"ms": 300.0}]},
            {"kind": "trade_stop"}]
    s = Sink("feed", root=root, flush_s=0)
    for i, r in enumerate(feed):
        s.write(int((T0 + i * 1800) * 1e9), json.dumps(r))
    s.close()


def test_maker_report(tmp_path):
    _run(tmp_path / "r1")
    text = rep.main(["--run", "r1", "--no-gamma"], root=tmp_path)
    assert "## Maker" in text and "live, arm vm_fair0.03_p-0.03, model v1_L50, 1.00 h" in text
    assert "inserts 20 (20/h), accepted 19, rejected: post_only_crosses 1" in text
    assert "skipped quotes (caps): market_cap 1" in text
    assert "pull <= 1 s" in text and "no pull" in text
    assert "orders filled: real 20, inferred 10, both 10" in text
    assert "sim reference" in text or not load.__name__        # reference row when the research table exists
    assert (tmp_path / "r1" / "report.md").exists()


def test_markout_and_split_numbers(tmp_path):
    _run(tmp_path / "r2", dry=True)
    f = load.fills(tmp_path / "r2", gamma=False)
    t = section.fills_table(f, 1.0).set_index("side")
    # 15 fills at mid 0.45 and 5 at 0.30 on 0.40 cost: (15 * 0.25 - 5 * 0.5) / 40 = +3.125 c/$
    assert t.loc["all", "fills_h"] == 20 and t.loc["all", "mk10_cpd"] == pytest.approx(100 * (15 * 0.25 - 5 * 0.5) / 40)
    a = section.adverse_table(f).set_index("after fill")
    assert a.loc["pull <= 1 s", "fills"] == 5 and a.loc["pull <= 1 s", "mk10_cpd"] == pytest.approx(-25.0)
    assert a.loc["no pull", "mk10_cpd"] == pytest.approx(12.5)
    lat = section.latency_table(load.frame(tmp_path / "r2", "ops"), load.copies(load.notes(tmp_path / "r2")))
    lat = lat.set_index("ms")
    assert lat.loc["insert ack (every copy)", "n"] == 3 and lat.loc["cancel ack (first copy)", "p50"] == pytest.approx(39.5)
    assert "dry (no orders)" in "\n".join(section.section(tmp_path / "r2", gamma=False))


def test_dry_would_skips_reported(tmp_path):
    root = tmp_path / "r3"
    _run(root, dry=True)
    _write(root, "ops", [{"kind": "would_skip", "cid": f"w{i}", "reason": "loss_headroom", "slug": "s"} for i in range(2)])
    s = Sink("events", root=root / "raw", flush_s=0)
    s.write(int((T0 + 10) * 1e9), json.dumps({"kind": "would_stop", "reason": "loss cap: pnl -10.50 <= -10.0"}))
    s.close()
    text = "\n".join(section.section(root, gamma=False))
    assert "would-skip (caps, dry only): loss_headroom 2" in text and "skipped quotes (caps): market_cap 1" in text
    assert "would-stop (dry only, not applied): loss cap" in text
    _run(tmp_path / "r4")                          # an old log (no would-skips): no such line
    old = "\n".join(section.section(tmp_path / "r4", gamma=False))
    assert "would-skip" not in old and "would-stop" not in old
