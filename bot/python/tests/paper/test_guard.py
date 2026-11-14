"""No order path: forbidden imports are blocked and the package source has no order calls."""
import re
from pathlib import Path

import pytest

from btclat.paper import guard

SRC = Path(__file__).resolve().parents[2] / "btclat" / "paper"
PATTERNS = [r"\bPOST\b", r"/orders?\b(?!-)", r"post_order", r"create_order", r"\bsign\(", r"private_key",
            r"api_key", r"api_secret", r"passphrase", r"cancel_(order|all|market)", r"https://clob\."]


def test_forbidden_imports_blocked():
    guard.install()
    for name in ("py_clob_client", "eth_account", "web3", "coincurve"):
        with pytest.raises(ImportError):
            __import__(name)


def test_no_order_calls_in_source():
    hits = []
    for p in SRC.rglob("*"):
        if p.suffix not in (".py", ".sh", ".service") or p.name == "guard.py":
            continue
        text = p.read_text()
        for pat in PATTERNS:
            for m in re.finditer(pat, text):
                hits.append(f"{p.relative_to(SRC)}: {m.group(0)}")
    assert not hits, hits
