# AWS probe, 2026-10-11 22:24-22:33 UTC (account <AWS_ACCOUNT>, 5 x t4g.micro, all self-terminated)

Binance receive delay, event stamp E to receipt (synced clocks, Amazon Time Sync), median:

| zone | perp bookTicker p50 / p99 ms | best perp trade conn p50 | best spot conn p50 |
|---|---|---|---|
| apne1-az4 (Tokyo) | **1.92** / 36.0 | 2.43 | 3.84 |
| apne1-az2 (Tokyo) | 2.41 / 18.8 | 3.27 | 3.67 |
| apne1-az1 (Tokyo) | 2.74 / 34.3 | 3.25 | 6.44 |
| euw1-az1 (Dublin) | 104.3 / 264 | 101.1 | 102.4 |
| euw2-az1 (London) | 108.7 / 289 | 106.3 | 106.8 |

Polymarket CLOB warm HTTP/2 request round trip, p50 (p10-p90):
- London euw2-az1: **18.4 ms** (17.1-25.1); Dublin euw1-az1: **25.6 ms** (24.7-27.4); Tokyo: 241-244 ms.
- After 60 s idle: London 30 ms, Dublin 35 ms (keep the connection warm).

Read:
- **Dublin build total (Binance event to order at the CLOB): ~101 + ~13 = ~114 ms**, matching the
  ~113 ms estimate behind L = 0 in the simulator and the predict study.
- **Fastest Tokyo zone for a signal box: apne1-az4** (perp bookTicker 1.9 ms).
- Parallel connections matter: in Dublin the best perp connection arrived first 74% of the time;
  others trailed by up to tens of ms at p99.
- Geoblock endpoint returns blocked=true for JP, IE and GB IPs. Per Polymarket docs JP and IE are
  website-only restrictions (API not restricted); GB is close-only on the API (co-location form
  only). Not yet verified with a real order (needs user approval).
