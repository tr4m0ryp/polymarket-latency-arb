# polymarket-latency-arb

**Trade Polymarket's 5-minute BTC markets on the exchange price, before the Polymarket book has caught up.**

## The idea

Polymarket settles its BTC up/down markets on the Chainlink BTC/USD price. That price trails the exchanges: Chainlink lags Binance by about 1.5 s, and the Polymarket order book reprices only after the exchanges have moved.

We read the move at the source instead. Binance (hosted in AWS Tokyo) and Deribit feed one fused fair value, computed on a server in AWS London, the same region as Polymarket's matching engine. Polymarket approved our wallets for its co-location programme, which puts an order 15 ms from the engine. A small prediction model filters out the moves that will not carry through.

The wallets that already run this buy the side of the latest 1 to 3 s exchange move in small fixed clips and hold to resolution. They earn **2.44 cents per dollar traded** before fees, and **10.7 cents** right after a clear move of more than 1 basis point.

## The limitation

The taker fee is `0.07 * p * (1 - p)` per share, about 3% of the amount traded near even odds. That is larger than the average edge.

Polymarket returns part of the fee by volume tier: 3, 8, 18, 32, 44 or 50%. The top tier, 50% back, needs about **$10M of weighted trading volume per 30 days**. Every profitable bot we measured sits there. Over two days the second-best one made $12,074 at that tier and would have made $2,713 without it. A new account starts at 0%, where our own live result was about zero.

Two smaller obstacles remain: a 150 ms hold that Polymarket applies to taker orders, and a median of 4 rival bots chasing each move.

## Status

We have not found a way to reach that volume without losing money on the way up, so the gap stays locked for us. If you are rich, congratulations: this makes you richer.

## License

polymarket-latency-arb is **source-available**, licensed under the [PolyForm Noncommercial License 1.0.0](./LICENSE), **not** an OSI open-source license.

- **You may** use, modify, fork, and share polymarket-latency-arb freely for any **noncommercial** purpose, as long as you keep the copyright and `Required Notice:` lines (see [`NOTICE`](./NOTICE)) and credit *"polymarket-latency-arb by Keygraph, Inc."*
- **You may not** sell it, bundle it into a paid product, or run it as a paid/hosted service **without a commercial license**.

Copyright (c) 2026 Keygraph, Inc. Commercial licensing enquiries: see [`NOTICE`](./NOTICE).
