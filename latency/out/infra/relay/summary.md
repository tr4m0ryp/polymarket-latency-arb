# Relay probe, 2026-10-11 ~23:00 UTC (Tokyo apne1-az4 -> Dublin euw1-az1 / London euw2-az1, UDP over AWS)

Same Binance perp updates via the Tokyo relay and via a direct websocket, compared per update id
on one clock (300 s, ~19k bookTicker updates per receiver). Binance event E to arrival, ms:

| path | Dublin p50 / p90 / p99 | London p50 / p90 / p99 |
|---|---|---|
| direct websocket (4 conns) | 100.5 / 133.7 / 308.7 | 106.3 / 141.3 / 334.6 |
| Tokyo relay (UDP) | 101.5 / 203.3 / 313.0 | 106.4 / 210.8 / 309.9 |
| **best of both** | **100.5 / 128.8 / 208.9** | **106.3 / 137.1 / 213.8** |

- Relay first in 5% (Dublin) / 30% (London) of updates; median relay minus direct +0.9 / +0.1 ms.
- Tokyo sender: E to Tokyo receipt p50 2.0 ms but p90 74.8 ms (single Python loop on a t4g.micro
  under burst load): the relay tail is the sender's backlog, not the network.
- Read: AWS Tokyo to Europe is ~99-104 ms one way whichever way the bytes go; Binance's own
  stream already rides that path. A relay saves nothing at the median. Run both paths and take
  the first arrival: it cuts the p99 by ~100 ms. A faster sender (compiled, larger instance)
  should help the tail further. Going below ~100 ms needs a non-AWS route (reports/fast-link.md).
