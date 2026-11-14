"""Parse one hour of Binance recordings into compact arrays (npz).

Spot (`binance-<h>`): trades (`st_*`: receipt t, trade time T, price, qty, buyer-is-maker)
and bookTicker (`sb_*`: t, bid, ask, bid qty, ask qty; no venue stamp on spot).
USD-M perp (`binance_fut-<h>`, run 2 only): bookTicker (`fb_*`: t, transaction time T,
bid, ask, bid qty, ask qty). Every update is kept (queue sizes feed the imbalance signal)."""
from __future__ import annotations

import json

import numpy as np

from .clob import _lines


def spot(path) -> dict[str, np.ndarray]:
    trs, bks = [], []
    for t, raw in _lines(path):
        j = json.loads(raw)
        d = j["data"]
        if j["stream"].endswith("@trade"):
            trs.append((t, d["T"] / 1e3, float(d["p"]), float(d["q"]), float(d["m"])))
        elif "b" in d:
            bks.append((t, float(d["b"]), float(d["a"]), float(d["B"]), float(d["A"])))
    a = np.array(trs, dtype=float).reshape(-1, 5)
    b = np.array(bks, dtype=float).reshape(-1, 5)
    return {"st_t": a[:, 0], "st_T": a[:, 1], "st_px": a[:, 2], "st_q": a[:, 3].astype(np.float32),
            "st_m": a[:, 4].astype(np.int8),
            "sb_t": b[:, 0], "sb_b": b[:, 1], "sb_a": b[:, 2],
            "sb_bq": b[:, 3].astype(np.float32), "sb_aq": b[:, 4].astype(np.float32)}


def perp(path) -> dict[str, np.ndarray]:
    rows = []
    for t, raw in _lines(path):
        d = json.loads(raw)["data"]
        if "b" not in d or "a" not in d:
            continue
        rows.append((t, d["T"] / 1e3, float(d["b"]), float(d["a"]), float(d["B"]), float(d["A"])))
    a = np.array(rows, dtype=float).reshape(-1, 6)
    return {"fb_t": a[:, 0], "fb_T": a[:, 1], "fb_b": a[:, 2], "fb_a": a[:, 3],
            "fb_bq": a[:, 4].astype(np.float32), "fb_aq": a[:, 5].astype(np.float32)}
