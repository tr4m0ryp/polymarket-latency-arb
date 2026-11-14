"""Feed-race stream table: name -> Stream. Public market data only, no keys, no order paths.

Groups run in separate processes (one asyncio loop each) so a busy venue cannot delay another
venue's receipt stamp. Names ending in _a/_b are duplicate connections of the same stream:
the earlier work found whole connections running ~100 ms late (reports/infra-plan.md, 2)."""
from __future__ import annotations

import json
from dataclasses import dataclass

BS = "wss://stream.binance.com:9443"
BF = "wss://fstream.binance.com"
US = "?timeUnit=MICROSECOND"  # spot JSON streams can stamp E/T in microseconds


@dataclass(frozen=True)
class Stream:
    group: str
    url: str
    hello: str | tuple[str, ...] | None = None  # subscribe message(s) sent after connect
    ping: str | None = None   # app-level keepalive payload (Bybit, OKX)
    every: float = 15.0
    key_env: str | None = None  # needs an API key header from this env var; skipped if unset
    ws_ping: float | None = 20.0  # websocket-level ping interval (LMAX closes on "excessive pings")


def _bybit(cat: str) -> Stream:
    hello = json.dumps({"op": "subscribe", "args": ["publicTrade.BTCUSDT", "orderbook.1.BTCUSDT"]})
    return Stream("venues", f"wss://stream.bybit.com/v5/public/{cat}", hello, json.dumps({"op": "ping"}))


def _okx(inst: str) -> Stream:
    args = [{"channel": c, "instId": inst} for c in ("trades", "bbo-tbt")]
    return Stream("venues", "wss://ws.okx.com:8443/ws/v5/public",
                  json.dumps({"op": "subscribe", "args": args}), "ping", 20.0)


COMBINED = "/stream?streams=btcusdt@trade/btcusdt@bookTicker"
STREAMS: dict[str, Stream] = {
    # Binance spot JSON. spot_comb_* is what the bot reads today (baseline).
    "spot_comb_a": Stream("spot", BS + COMBINED),
    "spot_comb_b": Stream("spot", BS + COMBINED),
    "spot_trade_a": Stream("spot", BS + "/ws/btcusdt@trade" + US),
    "spot_trade_b": Stream("spot", BS + "/ws/btcusdt@trade" + US),
    "spot_book_a": Stream("spot", BS + "/ws/btcusdt@bookTicker"),
    "spot_book_b": Stream("spot", BS + "/ws/btcusdt@bookTicker"),
    "spot_depth": Stream("spot", BS + "/ws/btcusdt@depth@100ms" + US),
    "spot_vision": Stream("spot", "wss://data-stream.binance.vision" + COMBINED),
    "spot_443": Stream("spot", "wss://stream.binance.com:443" + COMBINED),
    # Binance spot SBE: needs an Ed25519 API key in X-MBX-APIKEY (no key on file -> skipped).
    "spot_sbe": Stream("spot", "wss://stream-sbe.binance.com:9443/stream?streams="
                       "btcusdt@trade/btcusdt@bestBidAsk", key_env="BINANCE_ED25519_API_KEY"),
    # Binance USD-M perp. perp_pub_* is the bot's perp feed today.
    "perp_pub_a": Stream("perp", BF + "/public" + COMBINED),
    "perp_pub_b": Stream("perp", BF + "/public" + COMBINED),
    "perp_book": Stream("perp", BF + "/public/ws/btcusdt@bookTicker"),
    # Other venues.
    "coinbase": Stream("venues", "wss://ws-feed.exchange.coinbase.com", json.dumps(
        {"type": "subscribe", "product_ids": ["BTC-USD"], "channels": ["matches", "ticker"]})),
    "bybit_spot": _bybit("spot"),
    "bybit_lin": _bybit("linear"),
    "okx_spot": _okx("BTC-USDT"),
    "okx_swap": _okx("BTC-USDT-SWAP"),
    # Venues with engines in London (Deribit LD4, LMAX LD4) or the US (Coinbase, Kraken, Bitstamp).
    "deribit": Stream("west", "wss://www.deribit.com/ws/api/v2", json.dumps(
        {"jsonrpc": "2.0", "id": 1, "method": "public/subscribe", "params": {"channels": [
            "quote.BTC-PERPETUAL", "trades.BTC-PERPETUAL.100ms"]}}),  # raw trades need a key
        json.dumps({"jsonrpc": "2.0", "id": 9, "method": "public/test", "params": {}})),
    "bitstamp": Stream("west", "wss://ws.bitstamp.net", tuple(json.dumps(
        {"event": "bts:subscribe", "data": {"channel": c}})
        for c in ("live_trades_btcusd", "order_book_btcusd"))),
    "kraken_spot": Stream("west", "wss://ws.kraken.com/v2", tuple(json.dumps(
        {"method": "subscribe", "params": p}) for p in (
            {"channel": "ticker", "symbol": ["BTC/USD"], "event_trigger": "bbo"},
            {"channel": "trade", "symbol": ["BTC/USD"]})), json.dumps({"method": "ping"}), 20.0),
    "kraken_fut": Stream("west", "wss://futures.kraken.com/ws/v1", tuple(json.dumps(
        {"event": "subscribe", "feed": f, "product_ids": ["PF_XBTUSD", "PI_XBTUSD"]})
        for f in ("ticker", "trade")), None),
    # LMAX public data is a 1 s order-book snapshot: kept as a check, too slow to lead.
    "lmax": Stream("west", "wss://public-data-api.london-digital.lmax.com/v1/web-socket",
                   json.dumps({"type": "SUBSCRIBE", "channels": [
                       {"name": "ORDER_BOOK", "instruments": ["btc-usd"]},
                       {"name": "TICKER", "instruments": ["btc-usd"]}]}), ws_ping=None),
    "bullish": Stream("west", "wss://api.exchange.bullish.com/trading-api/v1/market-data/orderbook",
                      json.dumps({"jsonrpc": "2.0", "type": "command", "method": "subscribe",
                                  "params": {"topic": "l1Orderbook", "symbol": "BTCUSDC"},
                                  "id": "1"}),
                      json.dumps({"jsonrpc": "2.0", "type": "command", "method": "keepalivePing",
                                  "params": {}, "id": "2"}), 30.0),
}
