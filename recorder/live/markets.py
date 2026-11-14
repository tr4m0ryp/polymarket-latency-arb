"""Resolve the 5m/15m BTC up/down markets by slug (`btc-updown-<fam>-<start_ts>`)."""
from __future__ import annotations

import json
import urllib.request

GAMMA = "https://gamma-api.polymarket.com"
FAMILIES = {"5m": 300, "15m": 900}


def fetch(fam: str, start: int) -> dict | None:
    slug = f"btc-updown-{fam}-{start}"
    req = urllib.request.Request(f"{GAMMA}/markets?slug={slug}",
                                 headers={"User-Agent": "btclat/0.1"})
    with urllib.request.urlopen(req, timeout=10) as r:
        rows = json.loads(r.read())
    if not rows:
        return None
    m = rows[0]
    outcomes = json.loads(m["outcomes"])
    tokens = json.loads(m["clobTokenIds"])
    return {"fam": fam, "slug": slug, "start": start, "end": start + FAMILIES[fam],
            "condition_id": m["conditionId"], "up": tokens[outcomes.index("Up")],
            "down": tokens[outcomes.index("Down")],
            "tick": float(m.get("orderPriceMinTickSize") or 0.01),
            "taker_base_fee": m.get("takerBaseFee")}


def wanted(now: float, lead_s: int = 90) -> list[tuple[str, int]]:
    """(family, start) of every market that is open now or opens within lead_s,
    so the book is recorded through the pre-open strike window."""
    out = []
    for fam, dur in FAMILIES.items():
        cur = int(now) // dur * dur
        out.append((fam, cur))
        if cur + dur - now <= lead_s:
            out.append((fam, cur + dur))
    return out
