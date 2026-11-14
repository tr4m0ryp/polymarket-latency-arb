"""Rust bot report: loader tolerance, order join, hold table, report text, CLI."""
import math

import numpy as np
import pandas as pd
import pytest

from btclat.trade.report.rust import __main__ as rep
from btclat.trade.report.rust import hold, load, orders

from .rust_fakes import events, write_run


@pytest.fixture
def run(tmp_path):
    return write_run(tmp_path / "run1")


def test_loader_tolerates_truncation(run):
    ev = load.events(run)
    full = events()
    assert len(ev) == len(full)          # torn last line and trailer-less gzip lose nothing complete
    assert [e["seq"] for e in ev] == sorted(e["seq"] for e in ev)
    assert "log_stats" in {e["kind"] for e in ev} and "stop" in {e["kind"] for e in ev}
    fr = load.frames(run)
    assert len(fr["order"]) == 2 and len(fr["ack"]) == 4


def test_loader_dedupes_and_empty(tmp_path, run):
    import shutil
    shutil.copy(run / f"bot-{490000}.jsonl.gz", run / "bot-490000.1.jsonl.gz")
    assert len(load.events(run)) == len(events())
    assert load.events(tmp_path / "nothing") == []


def test_order_join(run):
    df = orders.build(load.frames(run)).set_index("cid")
    a, b = df.loc["r:0"], df.loc["r:1"]
    assert a["sent"] and a["filled"] and not b["filled"]
    assert a["fill_sh"] == 5.0 and a["fill_cost"] == pytest.approx(2.1) and a["px"] == pytest.approx(0.42)  # deduped by trade_id
    assert a["fee"] == pytest.approx(0.07 * 0.42 * 0.58 * 5)
    assert a["fill_src"] == "post"
    assert a["first_ack_ms"] == pytest.approx(100.0, rel=1e-3)                # copy 0 answered first
    assert a["copy_lat_ms"] == pytest.approx([100.0, 130.0], rel=1e-3)
    assert pd.isna(a["err_kind"]) and b["err_kind"] == "fak_no_match"  # main ack, not the duplicate reject
    assert (a["t_ack_ns"] - a["t_send_ns"]) / 1e6 == pytest.approx(100.0, rel=1e-3)
    assert a["sign_us"] == pytest.approx(1400.0) and a["t_event_venue"] == pytest.approx(a["t_signal"] - 0.11)
    assert a["bk_ack_ba"] == 0.42 and a["bk_a10_mid"] == 0.5 and a["outcome"] == 1.0 and a["won"] == 1.0
    assert a["live_v10"] == pytest.approx(5 * 0.5 - 2.1 - a["fee"])
    assert df["p_filled"].sum() == 0 and np.isnan(df["p_px"]).all()


def test_hold_table(run):
    t = hold.table(orders.build(load.frames(run))).set_index("cid")
    a, b = t.loc["r:0"], t.loc["r:1"]
    fee = 0.07 * 0.42 * 0.58 * 5
    assert a["ask_match"] == 0.42 and a["ask_send"] == 0.41 and a["ask_move_c"] == pytest.approx(1.0)
    assert a["seen_to_match_c"] == pytest.approx(2.0)
    assert a["depth_send"] == 100 and a["depth_ack"] == 60 and a["depth_survival"] == pytest.approx(0.6)
    assert a["mk10_cpd"] == pytest.approx(100 * (2.5 - 2.1 - fee) / 2.1)
    assert math.isnan(a["miss_mk10_cpd"])
    assert b["depth_survival"] == 0.0 and not b["filled"] and math.isnan(b["mk10_cpd"])
    assert b["miss_mk10_cpd"] == pytest.approx(100 * (0.40 - 0.45 - 0.07 * 0.45 * 0.55) / 0.45)
    s = hold.summary(t.reset_index(), "i").iloc[0]
    assert s["n"] == 2 and s["fills"] == 1 and s["fill_rate"] == 0.5
    assert s["mk10_cpd"] == pytest.approx(100 * (2.5 - 2.1 - fee) / 2.1)


def test_report_text_and_cli(tmp_path, run):
    text = rep.main(["--run", "run1", "--root", str(tmp_path)])
    assert (run / "report.md").read_text() == text
    for needle in ("Start: mode live", "Stop: sigterm; cancel-all ok True", "Vetoes by reason: margin 1",
                   "Skips by reason: max_orders_hour 1", "Orders 2 (dry 0)", "live_mk10_cpd", "## Hold",
                   "depth_survival", "fak_no_match 1", "duplicate 2", "feed:pm", "Ack latency per copy",
                   "binance_event_to_ack", "dropped 0"):
        assert needle in text, needle
    assert "Traceback" not in text


def test_empty_run(tmp_path):
    (tmp_path / "e").mkdir()
    assert "no bot-" in rep.build(tmp_path / "e")
