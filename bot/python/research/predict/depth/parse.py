"""Rebuild the near-touch perp book from the side recorder's diff depth (@depth@0ms, sizes
are absolute per level, so levels fill in within seconds without a REST snapshot) and the
bookTicker on the same clock. Per depth message (receipt t): queue at the 2nd level and
summed within 2-5 and 2-10 ticks behind the touch, each side.

    python3 -m research.predict.depth.parse   -> data/cache/predict/depth.npz"""
from __future__ import annotations

import json

import numpy as np

from .. import CACHE, ROOT
from ...strategy.ingest.clob import _lines

SIDE = ROOT / "data" / "live_side"
TICK = 0.1


def _behind(book: dict, best: float, sign: int, k0: int, k1: int) -> float:
    s = 0.0
    for k in range(k0, k1 + 1):
        s += book.get(round(best - sign * k * TICK, 1), 0.0)
    return s


def parse() -> dict:
    bids, asks = {}, {}
    bb = ba = None
    rows = []
    for p in sorted(SIDE.glob("*/fut_depth-*.tsv.gz")):
        for t, raw in _lines(p):
            j = json.loads(raw)
            d = j["data"]
            if j["stream"].endswith("bookTicker"):
                bb, ba = float(d["b"]), float(d["a"])
                continue
            for px, q in d["b"]:
                x, q = round(float(px), 1), float(q)
                if q == 0:
                    bids.pop(x, None)
                else:
                    bids[x] = q
            for px, q in d["a"]:
                x, q = round(float(px), 1), float(q)
                if q == 0:
                    asks.pop(x, None)
                else:
                    asks[x] = q
            if bb is None:
                continue
            rows.append((t, _behind(bids, bb, 1, 1, 1), _behind(asks, ba, -1, 1, 1),
                         _behind(bids, bb, 1, 1, 4), _behind(asks, ba, -1, 1, 4),
                         _behind(bids, bb, 1, 1, 9), _behind(asks, ba, -1, 1, 9)))
            if len(bids) > 5000:
                for x in [x for x in bids if x < bb - 100]:
                    bids.pop(x)
                for x in [x for x in asks if x > ba + 100]:
                    asks.pop(x)
    a = np.array(rows, dtype=float)
    names = ["t", "b2", "a2", "b2_5", "a2_5", "b2_10", "a2_10"]
    return {n: a[:, i] for i, n in enumerate(names)}


if __name__ == "__main__":
    d = parse()
    np.savez(CACHE / "depth.npz", **d)
    print("rows", len(d["t"]), "span h", (d["t"][-1] - d["t"][0]) / 3600)
