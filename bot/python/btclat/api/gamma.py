"""Gamma API: series (recurring market families), events and markets."""
from __future__ import annotations

import json

from .http import GAMMA, get


def all_series(closed: bool = False) -> list[dict]:
    out, off = [], 0
    while True:
        page = get(GAMMA, "/series", {"limit": 50, "offset": off,
                                      "closed": str(closed).lower()})
        if not page:
            return out
        out += page
        off += 50


def closed_events(series_id: str | int, n: int) -> list[dict]:
    """Most recent `n` closed events of a series, newest first."""
    out, off = [], 0
    while len(out) < n:
        page = get(GAMMA, "/events", {"series_id": series_id, "closed": "true",
                                      "limit": min(100, n - len(out)), "offset": off,
                                      "order": "endDate", "ascending": "false"})
        if not page:
            break
        out += page
        off += len(page)
    return out


def parse_market(m: dict) -> dict | None:
    """Flatten a resolved binary market; None if unresolved or not binary."""
    try:
        outcomes = json.loads(m["outcomes"])
        prices = [float(p) for p in json.loads(m["outcomePrices"])]
        tokens = json.loads(m["clobTokenIds"])
    except (KeyError, TypeError, ValueError):
        return None
    if len(outcomes) != 2 or max(prices) < 0.99:
        return None
    return {
        "condition_id": m["conditionId"],
        "question": m.get("question"),
        "outcomes": outcomes,
        "tokens": tokens,
        "winner": prices.index(max(prices)),
        "window_start": m.get("eventStartTime") or m.get("startDate"),
        "window_end": m.get("endDate"),
        "created": m.get("startDate") or m.get("createdAt"),
        "volume": float(m.get("volume") or 0),
    }
