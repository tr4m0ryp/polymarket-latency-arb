"""Our matched shares per order id, from the venue's trade records: the authoritative fill
source (GET /data/trades and the user websocket channel carry the same trade objects).

A trade lists the taker order (`taker_order_id`, `size`) and every maker order it hit
(`maker_orders`: `order_id`, `matched_amount`, `price`). Our post-only quotes are makers, so
an order's matched total is the sum of its `matched_amount` over distinct trade ids. A trade
that comes back FAILED (settlement rolled back) is taken out again. Each trade id counts once,
whichever source saw it first: replaying a trade changes nothing."""
from __future__ import annotations

FAILED = ("FAILED",)


def _f(x) -> float:
    try:
        return float(x)
    except (TypeError, ValueError):
        return 0.0


def legs(tr: dict) -> list[tuple[str, float, float]]:
    """(order id, shares, price) of every order in one trade object (taker leg first)."""
    out = []
    if tr.get("taker_order_id"):
        out.append((tr["taker_order_id"], _f(tr.get("size")), _f(tr.get("price"))))
    for m in tr.get("maker_orders") or []:
        if isinstance(m, dict) and m.get("order_id"):
            out.append((m["order_id"], _f(m.get("matched_amount")), _f(m.get("price"))))
    return out


def stamp(tr: dict) -> float | None:
    """Match time of a trade, unix s (REST `match_time`, websocket `matchtime` / `timestamp`)."""
    for k in ("match_time", "matchtime", "timestamp", "last_update"):
        v = _f(tr.get(k))
        if v > 0:
            return v / 1e3 if v > 1e11 else v
    return None


class Ledger:
    def __init__(self):
        self.by_oid: dict[str, dict[str, float]] = {}
        self.t_first: dict[str, float] = {}
        self.foreign: set[str] = set()         # trade ids of our wallet with no order of ours
        self.failed: set[str] = set()

    def add(self, tr: dict, ours) -> list[str]:
        """Apply one trade object; `ours(oid)` says which order ids are ours. Returns the order
        ids whose total changed."""
        tid = str(tr.get("id") or tr.get("trade_id") or "")
        if not tid:
            return []
        status = str(tr.get("status") or "").upper()
        hit = [(oid, sh) for oid, sh, _ in legs(tr) if ours(oid)]
        if not hit:
            self.foreign.add(tid)
            return []
        changed = []
        for oid, sh in hit:
            seen = self.by_oid.setdefault(oid, {})
            if status in FAILED:
                self.failed.add(tid)
                if seen.pop(tid, None) is not None:
                    changed.append(oid)
            elif tid not in seen and tid not in self.failed and sh > 0:
                seen[tid] = sh
                t = stamp(tr)
                if t is not None:
                    self.t_first.setdefault(oid, t)
                changed.append(oid)
        return changed

    def total(self, oid: str) -> float:
        return sum(self.by_oid.get(oid, {}).values())

    def trades(self, oid: str) -> list[str]:
        return sorted(self.by_oid.get(oid, {}))
