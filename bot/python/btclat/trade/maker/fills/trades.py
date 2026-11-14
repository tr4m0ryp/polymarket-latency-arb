"""The market's trade tape from the CLOB market channel (`last_trade_price`, both tokens), in the
Up frame of research/strategy/sim/maker.py `_flow`: d = +1 when the taker bought Up exposure
(BUY Up or SELL Down), p = Up-frame price, venue stamp ts (s), size in shares.

TradeTap is handed to btclat.paper.feeds.live.markets as its raw CLOB sink: every raw message
passes through it (forwarded to the recorder sink when the run records), trades are parsed."""
from __future__ import annotations

import json
import math


def parse_trades(t: float, raw: str, tokens: dict) -> list[dict]:
    """tokens: token id -> (slug, is_up). One dict per trade of a known token."""
    j = json.loads(raw)
    out = []
    for x in (j if isinstance(j, list) else [j]):
        if not isinstance(x, dict) or x.get("event_type") != "last_trade_price":
            continue
        a = tokens.get(x.get("asset_id"))
        if a is None:
            continue
        slug, up = a
        try:
            px, size = float(x["price"]), float(x["size"])
        except (KeyError, TypeError, ValueError):
            continue
        ts = float(x.get("timestamp") or "nan") / 1e3
        side = 1 if str(x.get("side", "")).upper() == "BUY" else -1
        out.append({"slug": slug, "t": t, "ts": ts if math.isfinite(ts) else t, "d": side if up else -side,
                    "p": round(px if up else 1 - px, 4), "size": size, "up": up})
    return out


class TradeTap:
    def __init__(self, on_trade, raw=None):
        self.on_trade, self.raw = on_trade, raw
        self.tokens: dict[str, tuple[str, bool]] = {}
        self.n = 0

    def add_market(self, m: dict) -> None:
        self.tokens[m["up"]] = (m["slug"], True)
        self.tokens[m["down"]] = (m["slug"], False)

    def write(self, t_ns: int, raw: str) -> None:
        if self.raw is not None:
            self.raw.write(t_ns, raw)
        if '"last_trade_price"' not in raw:
            return
        for tr in parse_trades(t_ns / 1e9, raw, self.tokens):
            self.n += 1
            self.on_trade(tr)
