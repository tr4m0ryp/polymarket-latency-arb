"""Data API: complete fill history of one market.

The /trades endpoint stops answering past offset ~9000, so long histories are
walked backwards in time with the `end` parameter instead of deep offsets."""
from __future__ import annotations

from .http import DATA, get

PAGE = 500
MAX_OFFSET = 8500


def _key(t: dict) -> tuple:
    return (t["transactionHash"], t["proxyWallet"], t["asset"], t["side"],
            t["size"], t["price"])


def market_trades(condition_id: str, taker_only: bool, cache: bool = True) -> list[dict]:
    seen: dict[tuple, dict] = {}
    end = None
    while True:
        off, oldest = 0, None
        while off <= MAX_OFFSET:
            page = get(DATA, "/trades", {"market": condition_id, "limit": PAGE,
                                         "offset": off, "end": end,
                                         "takerOnly": str(taker_only).lower()},
                       cache=cache)
            for t in page:
                seen.setdefault(_key(t), t)
                oldest = t["timestamp"] if oldest is None else min(oldest, t["timestamp"])
            if len(page) < PAGE:
                return list(seen.values())
            off += PAGE
        # offset cap reached: restart the walk at the oldest second seen
        if oldest is None or oldest == end:
            return list(seen.values())  # >9k fills in a single second: give up
        end = oldest
