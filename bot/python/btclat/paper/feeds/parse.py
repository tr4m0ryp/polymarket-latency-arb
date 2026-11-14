"""Raw websocket message -> normalized events, shared by the live feeds and the replay.

Mirrors the research ingest (research/strategy/ingest/binance.py, clob.py) so live state is
built from the same numbers: queue and trade sizes are rounded to float32 as the converted
hours store them, Polymarket levels off the 0.01 grid are dropped, only the Up token's book
is kept (it carries both sides, mirrored).

Event tuples (t = SNTP-corrected receipt time, s):
  ("pb", t, T, b, a, bq, aq)        perp bookTicker (T = Binance transaction time, s)
  ("sb", t, nan, b, a, bq, aq)      spot bookTicker (no venue stamp)
  ("st", t, T, px, q, m)            spot trade (m = 1 if the buyer is the maker)
  ("pt", t, T, px, q, m)            perp trade (recorded, not read by the v1 model)
  ("pm", t, ts, slug, snap, chg)    Up-token book change: snap = full book (clear first),
                                    chg = [(side +1 bid / -1 ask, tick, size)], ts = venue s
Dedupe keys: bookTicker update id `u`, trade id `t`."""
from __future__ import annotations

import json
import math
import struct

NAN = math.nan
_F = struct.Struct("f")


def f32(x: str | float) -> float:
    """Round to float32 like the research npz arrays."""
    return _F.unpack(_F.pack(float(x)))[0]


def tick(price: str) -> int:
    x = float(price) * 100
    k = round(x)
    return k if abs(x - k) < 1e-6 and 1 <= k <= 99 else -1


def binance(t: float, raw: str, perp: bool) -> tuple[tuple | None, tuple | None]:
    """(event, dedupe key) of one combined-stream message; (None, None) if not ours."""
    j = json.loads(raw)
    d = j.get("data")
    if not d:
        return None, None
    if j["stream"].endswith("@trade"):
        T = d["T"] / 1e3
        ev = ("pt" if perp else "st", t, T, float(d["p"]), f32(d["q"]), 1.0 if d["m"] else 0.0)
        return ev, ("t", d["t"])
    if "b" in d and "a" in d:
        T = d["T"] / 1e3 if perp and "T" in d else NAN
        ev = ("pb" if perp else "sb", t, T, float(d["b"]), float(d["a"]), f32(d["B"]), f32(d["A"]))
        return ev, ("u", d["u"])
    return None, None


def clob(t: float, raw: str, ups: dict[str, str]) -> list[tuple]:
    """ups: Up token id -> market slug. One event per (message, market) touching an Up book."""
    if '"best_bid_ask"' in raw and '"price_changes"' not in raw and '"book"' not in raw:
        return []
    j = json.loads(raw)
    out = []
    for x in (j if isinstance(j, list) else [j]):
        kind = x.get("event_type")
        if kind == "price_change":
            ts = float(x.get("timestamp") or "nan") / 1e3
            per: dict[str, list] = {}
            for c in x["price_changes"]:
                slug = ups.get(c["asset_id"])
                k = tick(c["price"]) if slug else -1
                if k > 0:
                    per.setdefault(slug, []).append((1 if c["side"] == "BUY" else -1, k, f32(c["size"])))
            out += [("pm", t, ts, s, False, chg) for s, chg in per.items()]
        elif kind == "book":
            slug = ups.get(x.get("asset_id"))
            if slug is None:
                continue
            ts = float(x.get("timestamp") or "nan") / 1e3
            chg = [(s, k, f32(lv["size"])) for s, key in ((1, "bids"), (-1, "asks"))
                   for lv in x[key] if (k := tick(lv["price"])) > 0]
            out.append(("pm", t, ts, slug, True, chg))
    return out
