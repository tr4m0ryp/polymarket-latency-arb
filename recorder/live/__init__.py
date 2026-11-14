"""Live, read-only recorder: Binance BTCUSDT, Chainlink BTC/USD (Polymarket RTDS)
and the Polymarket CLOB market feed for the current 5m/15m BTC markets.
Research only: nothing here signs, places or cancels orders."""
from .clock import Clock
from .sink import Sink, read_stream

__all__ = ["Clock", "Sink", "read_stream"]
