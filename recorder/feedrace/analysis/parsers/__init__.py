"""Per-venue message parsers: f(msg, out, state) appends (kind, key, key2, px, vts, vts2) rows."""
from __future__ import annotations

from .asia import bybit, coinbase, okx
from .binance import binance
from .pm import pm
from .west import bitstamp, bullish, deribit, kraken_fut, kraken_spot, lmax

_BY_PREFIX = (("coinbase", coinbase), ("bybit", bybit), ("okx", okx), ("deribit", deribit),
              ("bitstamp", bitstamp), ("kraken_spot", kraken_spot), ("kraken_fut", kraken_fut),
              ("lmax", lmax), ("bullish", bullish), ("pm", pm))


def parser(name: str):
    for pre, f in _BY_PREFIX:
        if name.startswith(pre):
            return f
    return binance
