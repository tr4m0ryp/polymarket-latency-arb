"""Shared stamp helpers: everything becomes integer microseconds since the epoch."""
from __future__ import annotations

from datetime import datetime


def _us(x) -> int:
    if x is None:
        return -1
    x = int(x)
    return x if x > 10**14 else x * 1000


def _iso_us(s: str) -> int:
    return int(datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp() * 1e6)
