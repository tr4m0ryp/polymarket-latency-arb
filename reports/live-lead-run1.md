# Live run 1: Binance-to-Polymarket lead and stale depth

Run: 2026-10-09 17:38-21:38 UTC, 4.0 h, Scaleway Paris, read-only. 50 5m and 17 15m BTC markets.
Recorder `python3 -m btclat.live`; analysis `python3 research/live/run.py`; full tables in
`reports/live-lead.md` (regenerated on every run, so the numbers below freeze run 1).
Clocks: the host ran 8.3 s slow; all receipt times are SNTP-corrected.

## Verdict

**The window is about 200 ms, not 1-2 s.** The forensic study's 2-3 s reaction came from Polygon
block times; the live book reprices within a few hundred milliseconds of the Binance trade. From
Paris we receive Binance 125 ms late, and in **64%** of 5m bursts the book has already started
moving before our spot tick arrives. Competitors see the move earlier or read a faster source.

**The money is real but small and selective.** All takers together collected about **$445/h of
fee-adjusted edge** (0% tier) in the 2.5 s after 1 bp bursts in 5m, about $10.7k/day at this
evening's volatility, the same order as the incumbents' measured PnL. Bursts of 1-2 bp lose after
the fee; only moves of **2 bp and up** pay.

## Lead (5m, burst = Binance 1 s move >= 1 bp, n = 155 clean events)

- **First reprice:** median **0.10 s** after our receipt of the onset trade, **0.20 s** after the
  Binance trade time on the venues' own clocks. 74% reprice within 250 ms vs 9.6% at random times.
- **Who moves it:** a trade in **78%** of 5m bursts (takers hit the stale quote), 55% in 15m.
- **Catch-up:** share of the book's 3 s move already priced in, by offset from our receipt:
  27% at 0, 62% at +250 ms, 83% at +500 ms, 92% at +1 s. Binance itself is 54% done at our
  receipt, because the onset sits mid-move.
- **15m** is the same shape: median first reprice 0.12 s, 90% caught up at +1 s.

## Stale depth (5m, fair = book mid 3 s later, edge net of the taker fee at 0% tier)

Edge still on the book after a 1 bp burst decays with a half-life of about 100 ms. The baseline
row is random times, the noise floor of this fair-value definition.

| still on book after our receipt | 0 s | 0.1 s | 0.25 s | 0.5 s | 1 s |
|---|---|---|---|---|---|
| burst >= 1 bp, $ edge per event | 108 | 60 | 33 | 21 | 17 |
| random time, $ edge per event | 20 | 18 | 16 | 13 | 8 |
| excess over random | 88 | 42 | 17 | 8 | 9 |

- **This is an upper bound on capacity:** it counts every level inside fair, and the fair includes
  drift after the burst. What takers actually took is the realistic number:

| Binance move over 6 s (5m) | n | book move (c) | USD taken | edge taken, $ per event |
|---|---|---|---|---|
| 1-2 bp | 83 | 7.4 | 238 | -2.0 |
| 2-3 bp | 37 | 11.0 | 316 | +15.6 |
| 3-5 bp | 15 | 18.5 | 505 | +65.7 |
| >= 5 bp | 6 | 17.8 | 340 | +25.1 |

- **Per burst, takers buy ~$290 (24 fills) with the move and ~$120 against.** Random times are
  symmetric ($86 / $83), which supports reading `last_trade_price.side` as the taker side.
- **15m pays far less:** +$1.7 per 1 bp burst; the 5m book carries the latency edge, as the
  forensic study found.

## Chainlink vs Binance (open question 1)

**Chainlink does not lead.** On observation timestamps its 1 s returns track Binance at lag 0-1 s
(xcorr 0.58 / 0.56), it publishes 1.18 s after the observation and reaches us 0.30 s later.
Binance therefore leads the settlement feed by about 1.5 s in data we can act on. Basis is a
steady $76 (USD vs USDT), irrelevant to up/down since strike and close use the same feed.

## Caveats

- **Quiet evening, 4 h:** only 7 clean 5m bursts >= 3 bp. Edge scales with volatility.
- **Recorder backlog:** Polymarket closed our socket 14 times for "slow consumer", and Binance
  receipt lag had a 9 s p99.9 tail. Events with Binance lag > 0.3 s, CLOB lag > 0.1 s or a
  reconnect within 5 s are dropped (30% of 1 bp bursts, 49% of 3 bp), which under-samples the
  big bursts. Fixed for run 2 (writer thread, deeper socket queue).
- **Fair value:** the spot model (strike TWAP, 300 s realized vol) gives similar ranks but noisier
  levels; it is reported in `reports/live-lead.md` and not used for the verdict.

## What it means for the build

- **Speed budget:** to beat the 100 ms half-life we need the Binance signal earlier than Paris
  gets it (Tokyo-side spot, or a leading feed) and an order path in tens of milliseconds to the
  CLOB (13 ms from Paris).
- **Rule at 0% tier:** fire only on >= 2 bp 1 s moves in 5m; 1-2 bp bursts are net negative.
- **Run 2 (started 2026-10-09 22:03 UTC, 24 h)** adds Binance USD-M futures to test whether the
  book follows the perp before spot, which would explain the 64% "already moved".
