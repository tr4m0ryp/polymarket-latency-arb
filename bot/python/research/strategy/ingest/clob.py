"""Parse one hour of the 5m CLOB recording into compact arrays (npz).

Only the Up token's book is kept: Polymarket shows every order on both books, mirrored
(an Up bid at p is a Down ask at 1 - p), so the Up book carries both sides. Levels off the
0.01 grid (sub-tick prices near 0 / 1) are dropped; the strategy never trades there.

Arrays (one row per book change, `ev_*`): market index, receipt t (s, SNTP-corrected),
venue ts (s), side (+1 bid, -1 ask, 0 = snapshot start: clear the book), tick (price * 100),
size. Trades (`tr_*`): market index, t, ts, is_up, side (+1 taker BUY), price, size."""
from __future__ import annotations

import gzip
import json
import zlib

import numpy as np


def _lines(p):
    try:
        with gzip.open(p, "rt") as fh:
            for line in fh:
                t, _, raw = line.rstrip("\n").partition("\t")
                if raw:
                    yield int(t) / 1e9, raw
    except (EOFError, zlib.error, gzip.BadGzipFile):
        return


def _tick(price: str) -> int:
    x = float(price) * 100
    k = round(x)
    return k if abs(x - k) < 1e-6 and 1 <= k <= 99 else -1


def parse(path, assets: dict[str, tuple[int, bool]]) -> dict[str, np.ndarray]:
    """assets: token id -> (market index, is_up) for the 5m markets we study."""
    ev, tr = [], []
    for t, raw in _lines(path):
        if '"best_bid_ask"' in raw and '"price_changes"' not in raw and '"book"' not in raw:
            continue
        j = json.loads(raw)
        for x in (j if isinstance(j, list) else [j]):
            kind = x.get("event_type")
            if kind == "price_change":
                ts = float(x.get("timestamp") or "nan") / 1e3
                for c in x["price_changes"]:
                    a = assets.get(c["asset_id"])
                    if a is None or not a[1]:
                        continue
                    k = _tick(c["price"])
                    if k > 0:
                        ev.append((a[0], t, ts, 1 if c["side"] == "BUY" else -1, k, float(c["size"])))
            elif kind == "book":
                a = assets.get(x.get("asset_id"))
                if a is None or not a[1]:
                    continue
                ts = float(x.get("timestamp") or "nan") / 1e3
                ev.append((a[0], t, ts, 0, 0, 0.0))
                for s, key in ((1, "bids"), (-1, "asks")):
                    for lv in x[key]:
                        k = _tick(lv["price"])
                        if k > 0:
                            ev.append((a[0], t, ts, s, k, float(lv["size"])))
            elif kind == "last_trade_price":
                a = assets.get(x.get("asset_id"))
                if a is None:
                    continue
                ts = float(x.get("timestamp") or "nan") / 1e3
                tr.append((a[0], t, ts, int(a[1]), 1 if x["side"] == "BUY" else -1,
                           float(x["price"]), float(x["size"])))
    e = np.array(ev, dtype=float).reshape(-1, 6)
    r = np.array(tr, dtype=float).reshape(-1, 7)
    return {"ev_m": e[:, 0].astype(np.int32), "ev_t": e[:, 1], "ev_ts": e[:, 2],
            "ev_side": e[:, 3].astype(np.int8), "ev_tick": e[:, 4].astype(np.int8),
            "ev_size": e[:, 5].astype(np.float32),
            "tr_m": r[:, 0].astype(np.int32), "tr_t": r[:, 1], "tr_ts": r[:, 2],
            "tr_up": r[:, 3].astype(np.int8), "tr_side": r[:, 4].astype(np.int8),
            "tr_px": r[:, 5].astype(np.float32), "tr_size": r[:, 6].astype(np.float32)}
