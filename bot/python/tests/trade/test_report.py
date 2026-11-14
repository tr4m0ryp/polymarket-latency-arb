"""The report on a synthetic run: fill rates, slippage, latency, markout CI, trades needed."""
import json
import math

import numpy as np
import pytest

from recorder.live.sink import Sink
from btclat.trade.report import __main__ as rep
from btclat.trade.report.stats import boot_cpd, n_needed

T0 = 1_791_800_000


def _write(root, name, rows):
    s = Sink(name, root=root, flush_s=0)
    for r in rows:
        s.write(int(r.get("t_signal", T0) * 1e9), json.dumps(r))
    s.close()


def _orders(n=40):
    rng = np.random.default_rng(1)
    out = []
    for i in range(n):
        slug = f"btc-updown-5m-{T0 + 300 * (i // 4)}"
        filled = i % 5 != 0
        px = 0.40 + 0.01 * (i % 3)
        r = {"sig": f"r:{i}", "arm": "vt_v1_m0.03_any", "slug": slug, "up": bool(i % 2), "side": 1 if i % 2 else -1,
             "t_signal": T0 + 10 * i, "src": "pb", "t_event_venue": T0 + 10 * i - 0.11, "t_decision": T0 + 10 * i + 0.001,
             "seen": 0.40, "limit": 0.42, "size": 5.0, "decision": "sent" if i % 10 else "skip:max_orders_hour",
             "t_send_ns": int((T0 + 10 * i + 0.003) * 1e9), "t_ack_ns": int((T0 + 10 * i + 0.2) * 1e9),
             "sign_us": 1400.0, "err_kind": None if filled else "fak_no_match",
             "fill_sh": 5.0 if filled else 0.0, "fill_cost": 5 * px if filled else 0.0, "px": px if filled else None,
             "fee": 0.07 * px * (1 - px) * 5 if filled else 0.0, "mk10_live": px + 0.03 + 0.05 * rng.standard_normal(),
             "paper": {"fill_sh": 5.0, "px": 0.40, "cost": 2.0, "fee": 0.084, "mk10": 0.45}}
        out.append(r)
    return out


def test_report_micro(tmp_path):
    root = tmp_path / "run1"
    rows = _orders()
    _write(root, "orders", rows)
    _write(root, "settle", [{"slug": s, "outcome": 1.0, "end": 0} for s in {r["slug"] for r in rows}])
    _write(root, "events", [{"kind": "preflight", "geoblock": {"blocked": False, "country": "IE"}, "balance": 40.0}])
    text = rep.main(["--run", "run1", "--no-gamma"], root=tmp_path)
    assert "## Micro" in text and "fak_no_match" in text and "max_orders_hour 4" in text
    assert "send_to_ack" in text and "binance_event_to_ack" in text and "n_at_research" in text
    assert (root / "report.md").exists()


def test_report_probe(tmp_path):
    root = tmp_path / "p"
    cyc = [{"cycle": i, "warm": i % 2 == 0, "decision": "sent", "sign_us": 1500.0, "order_id": f"o{i}",
            "cancelled": True, "err_kind": None, "book_ms": 20.0, "ping_ms": [24.0, 25.0] if i % 2 == 0 else None,
            "post": {"code": 200, "ms": 30.0 + 20 * (i % 2), "http": "HTTP/2", "idle_s": 1.0 + 29 * (i % 2),
                     "pop": "DUB", "hdr": {}},
            "cancel": {"code": 200, "ms": 25.0}} for i in range(10)]
    _write(root, "probe", cyc)
    text = rep.main(["--run", "p", "--no-gamma"], root=tmp_path)
    assert "POST ack (warm)" in text and "POST ack (idle)" in text and "cancel confirmed 10 of 10" in text


def test_boot_and_n_needed():
    num = np.array([1.0, -0.5, 2.0, 0.5])
    den = np.array([10.0, 10.0, 10.0, 10.0])
    p, lo, hi = boot_cpd(num, den, ["a", "b", "c", "d"])
    assert p == pytest.approx(7.5) and lo < p < hi
    assert n_needed(20.0, 5.0) == math.ceil((1.959964 * 4) ** 2) == 62
    assert n_needed(20.0, -1.0) == math.inf
