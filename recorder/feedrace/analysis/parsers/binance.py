"""Binance spot and USD-M JSON: trade, bookTicker, depthUpdate (combined or raw)."""
from __future__ import annotations

import numpy as np

from .common import _us


def binance(m: dict, out: list, st: dict) -> None:
    d = m.get("data", m)
    e = d.get("e")
    if e == "trade":
        if d.get("X", "MARKET") != "MARKET" or float(d["p"]) <= 0:
            return  # USD-M non-market prints (insurance fund, ADL, NA) carry price 0
        out.append((0, d["t"], -1, float(d["p"]), _us(d.get("E")), _us(d.get("T"))))
    elif e == "depthUpdate":
        out.append((2, d["u"], d["U"], np.nan, _us(d.get("E")), _us(d.get("T"))))
    elif "u" in d and "b" in d and "a" in d:
        out.append((1, d["u"], -1, (float(d["b"]) + float(d["a"])) / 2, _us(d.get("E")),
                    _us(d.get("T"))))
