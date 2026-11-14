"""Cancel-all on every exit path, the kill file, and no signing library at import."""
import os
import signal
import subprocess
import sys
from pathlib import Path

import pytest

from btclat.trade.risk.session import Session, Stop, install_signals

from .fakes import FakeVenue

ROOT = Path(__file__).resolve().parents[2]


def test_cancel_all_on_normal_exit(tmp_path):
    v = FakeVenue()
    with Session(v, tmp_path / "KILL") as s:
        pass
    assert v.n("cancel_all") == 1 and s.cancel_all_ok and s.exit_reason == "normal"


def test_cancel_all_on_exception(tmp_path):
    v = FakeVenue()
    with pytest.raises(RuntimeError):
        with Session(v, tmp_path / "KILL"):
            raise RuntimeError("boom")
    assert v.n("cancel_all") == 1


def test_kill_file(tmp_path):
    v = FakeVenue()
    with Session(v, tmp_path / "KILL") as s:
        s.check()
        (tmp_path / "KILL").touch()
        assert s.killed()
        s.check()
        raise AssertionError("not reached")
    assert "kill file" in s.exit_reason and v.n("cancel_all") == 1


def test_cancel_all_retried(tmp_path):
    v = FakeVenue()
    v.cancel_all = lambda: (_ for _ in ()).throw(ConnectionError("down"))
    with Session(v, tmp_path / "KILL", sleep=lambda x: None) as s:
        pass
    assert s.cancel_all_ok is False


def test_sigterm_cancels(tmp_path):
    v = FakeVenue()
    old = signal.getsignal(signal.SIGTERM)
    try:
        install_signals()
        with pytest.raises(SystemExit):
            with Session(v, tmp_path / "KILL"):
                os.kill(os.getpid(), signal.SIGTERM)
                for _ in range(10_000):
                    pass
    finally:
        signal.signal(signal.SIGTERM, old)
    assert v.n("cancel_all") == 1


def test_no_signing_library_at_import():
    """The live package loads the official client only inside a live session."""
    code = ("import sys, btclat.trade, btclat.trade.__main__, btclat.trade.micro.run, btclat.trade.probe.run, "
            "btclat.trade.report.__main__, btclat.trade.venue.client\n"
            "bad = [m for m in sys.modules if m.split('.')[0] in ('py_clob_client', 'py_clob_client_v2', "
            "'eth_account', 'eth_keys', 'coincurve', 'web3')]\n"
            "assert not bad, bad\n")
    r = subprocess.run([sys.executable, "-c", code], cwd=ROOT, capture_output=True, text=True, timeout=120)
    assert r.returncode == 0, r.stderr[-2000:]


def test_paper_package_untouched_by_trade():
    """btclat/paper never imports btclat.trade (its guard and source scan stay valid)."""
    hits = [p for p in (ROOT / "btclat" / "paper").rglob("*.py") if "btclat.trade" in p.read_text()
            or "from ..trade" in p.read_text()]
    assert not hits
