"""Why does Deribit arrive first? Split each move by who moved first on the venues' own clocks.

For moves where both the Deribit quote and the Binance perp book fire (move.market_moves), the
venue time of each onset (Deribit quote timestamp, Binance perp bookTicker T, both ms) gives
venue_lead = Binance onset - Deribit onset (> 0: Deribit moved first at the source). The local
lead (Binance best receipt - Deribit receipt) is reported for both groups: a Deribit receipt lead
on moves Binance started shows the geography (Deribit's ~95 ms shorter path) beating the
reaction delay of Deribit's makers."""
from __future__ import annotations

import numpy as np

from ids import q
from moves import market_moves
from signals import VTS

A, B = "deribit_book", "bn_perp_book"


def _vt(name: str, t_on: int) -> int:
    t, v = VTS[name]
    i = int(np.searchsorted(t, t_on))
    return int(v[i]) if i < len(v) and t[i] == t_on else -1


def split(sigs: dict, x: float) -> dict:
    if A not in sigs or B not in sigs:
        return {}
    moves, _ = market_moves(sigs, x)
    rows = []
    for m in (m["on"] for m in moves):
        if A in m and B in m and "bn_best" in m:
            va, vb = _vt(A, m[A]), _vt(B, m[B])
            if va > 0 and vb > 0:
                rows.append(((vb - va) / 1e3, (m["bn_best"] - m[A]) / 1e6))
    if not rows:
        return {}
    r = np.array(rows)
    first = r[:, 0] > 0
    return {"moves": len(r), "deribit_first_on_venue_clock_share": round(float(first.mean()), 3),
            "venue_lead_ms": q(r[:, 0], (10, 25, 50, 75, 90)),
            "local_lead_when_deribit_first": {**q(r[first, 1], (25, 50, 75)), "earlier_share": round(
                float((r[first, 1] > 0).mean()), 3) if first.any() else None},
            "local_lead_when_binance_first": {**q(r[~first, 1], (25, 50, 75)), "earlier_share": round(
                float((r[~first, 1] > 0).mean()), 3) if (~first).any() else None}}
