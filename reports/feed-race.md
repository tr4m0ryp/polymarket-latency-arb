# Feed race: the fastest BTC signal in Europe

**Final.** 7 h on two boxes, 2026-10-15: Dublin 08:04-15:03 UTC and London 08:35-15:35 UTC.
Both runs include the US open (13:30-15:00). The interim version (first ~2 h, commit b0ecdc0)
overstated Deribit's lead. The quiet European morning is its best case.

## Verdict

- **Trigger on the earliest of Deribit `quote.BTC-PERPETUAL` and Binance (perp bookTicker plus
  spot), on the London box.** Per BTC move, this fused feed arrives a median **+101 to +119 ms**
  before our current baseline (London; Dublin +91 to +116 ms). The baseline is the spot
  `btcusdt@trade/@bookTicker` combined JSON stream on one connection. The fused feed is earlier
  than the baseline in **96-97%** of moves.
- **Against the Polymarket 5m book:** the fused feed lands before the side-ask reprice in **81-83%**
  of moves. The median lead over that reprice is **135-155 ms**. Our current bot fan-in (spot +
  perp combined) does this in 62-65% of moves, with a 64-83 ms lead. The spot baseline alone does
  it in 48-52%, with a -9 to +9 ms lead.
- **Deribit alone is not a replacement for Binance.** It reaches London in **10 ms** (p50 venue
  stamp to receipt), while Binance takes **107 ms**. Even so, it shows a move before the best
  Binance feed in only **55-57%** of moves (median +10 to +14 ms). In the quiet hours it does so
  in 64% (+21 ms). During the US open it does so in 48-54% (-4 to +7 ms). Its prediction of the
  PM ask matches Binance's (hit 0.72-0.81 vs perp 0.72-0.81), so the two are best used together.
- **Inside Binance, the perp is the gain and connection tuning is noise.** The fused Binance
  feed (perp + spot) leads the spot baseline by a median of +16 to +27 ms. Raw vs combined,
  `:443` vs `:9443`, `data-stream.binance.vision` and a second connection each change arrival by
  only 1-3 ms at p50. `@depth@100ms` trails `@bookTicker` by a median of 4 ms.
- **The other venues lose.** Coinbase and Bitstamp are reached quickly (47 and 16 ms) but move
  late. Kraken futures trades (11 ms) are earlier than the best Binance feed in only 32% of moves.
  Bybit, OKX and Bullish are hosted in Asia (80-125 ms). LMAX public data is a 1 Hz snapshot.
- **Binance SBE was not tested: it needs an Ed25519 API key.** The endpoint answered HTTP 400
  `No X-MBX-APIKEY header` on both boxes. No such key exists in `~/.config/btclat`, so a
  read-only Ed25519 key from the user's Binance account would be needed. SBE uses the same
  gateways with 65-byte instead of 135-byte messages. I estimate its gain at 0-2 ms, against
  ~100 ms for the fused feed, so it is low priority.

## Setup

- **Recorder:** `research/feedrace/` (`record.py`, `streams.py`, `pm.py`, `sink.py`). It is
  Python asyncio + websockets with one process per stream group: Binance spot, Binance perp,
  Asian venues, Western venues and Polymarket. Each message is stamped on receipt with
  `CLOCK_MONOTONIC` ns and chrony wall-clock ns, and the venue's own stamps are kept. Output is
  gzip TSV, rotated every 15 min.
- **Boxes:** Dublin `<HOST>` and London `<HOST>`, both 2 vCPU Graviton with data in
  `~/feedrace/data/<label>`. Both run chrony on Amazon Time Sync, with offset p50 0.6 / 2.2 us and
  max 18 / 54 us. Nothing in `/opt/btclat` was touched, and no orders were placed.
- **Streams:**
  - **Binance spot JSON:** combined trade+bookTicker x2 (the baseline), raw `@trade` x2 (us
    stamps), raw `@bookTicker` x2, `@depth@100ms`, `data-stream.binance.vision` and `:443`.
  - **Binance USD-M:** `/public` combined x2 and raw bookTicker.
  - **Coinbase:** ticker + matches.
  - **Bybit:** spot and linear, publicTrade + orderbook.1.
  - **OKX:** BTC-USDT and SWAP, trades + bbo-tbt.
  - **Deribit:** quote + `trades.100ms`. Raw trades need a key.
  - **Bitstamp:** trades + book.
  - **Kraken:** spot v2 (bbo ticker + trades) and futures PF_XBTUSD.
  - **Others:** LMAX Digital public, Bullish L1 and the Polymarket 5m BTC Up/Down CLOB book. The
    PM book is recorded on the same box and clock.
- **Re-run on a new box (London, Tokyo):**
  1. `research/feedrace/deploy.sh ubuntu@<ip> <key.pem> <hours> <label>` copies the code to
     `~/feedrace`, builds its own venv and starts the recorder detached.
  2. `research/feedrace/fetch.sh ubuntu@<ip> <key.pem> <label-stamp>` pulls the data.
  3. `python3 research/feedrace/analysis/run.py data/cache/feedrace/<label-stamp> [HH:MM-HH:MM]`
     writes `data/out/feedrace/<label-stamp>[-window].json`.
- **Run quality:** two PM connections in Python fall behind the PM firehose and get
  `slow consumer` disconnects (about 1 per 15 min, reconnected within 1 s). LMAX dropped on
  websocket pings, which is fixed for the next run (`ws_ping=None`). The other feeds ran with at
  most 2 reconnects.

## (c) Venue time to receipt, 7 h, p50 [p10, p90] ms

| feed | Dublin | London |
|---|---|---|
| Polymarket CLOB book | 10.8 [8.6, 21.7] | **7.7** [5.4, 15.4] |
| Deribit quote | 13.2 [8.8, 67.3] | **9.9** [5.3, 39.2] |
| Kraken futures trade | 13.7 [8.2, 62.0] | 11.1 [5.4, 59.1] |
| Bitstamp book | 20.5 [14.0, 40.0] | 16.1 [10.0, 34.5] |
| Kraken spot trade | 26.1 [12.9, 87.7] | 18.2 [7.8, 56.6] |
| Coinbase ticker | 50.2 [48.2, 79.7] | 47.3 [43.7, 120.1] |
| Bybit spot / linear book | 85.1 / 94.9 | 80.2 / 89.0 |
| Bullish L1 | 92.6 | 91.0 |
| Binance spot trade, combined (baseline) | 103.3 [100.3, 110.5] | 107.4 [106.1, 110.8] |
| Binance perp bookTicker `/public` | 103.3 [100.4, 108.6] | 106.5 [105.6, 110.1] |
| Binance `@depth@100ms` | 102.3 | 105.0 |
| OKX spot / swap book | 126.3 / 128.0 | 117.2 / 123.9 |
| Deribit `trades.100ms` (batched) | 196 | 181 |
| LMAX public (1 Hz) | 503 | 516 |

- **Path:** Binance (Tokyo) is 3-4 ms closer to Dublin than to London. Deribit (LD4) and
  Polymarket are 3-4 ms closer to London.
- **Deribit p90 doubles in busy hours** (the interim, quiet-only run gave p90 15-20 ms). The quote
  passes through Cloudflare.

## (a) Same Binance id on several connections, 7 h (clock-free)

Each cell is p50 / p90 delay vs the first arrival, in ms.

| stream | spot trade, Dublin | London | spot bookTicker, Dublin | London |
|---|---|---|---|---|
| combined a (baseline) | 1.7 / 6.6 | 0.9 / 4.2 | 0.9 / 4.1 | 0.6 / 3.6 |
| combined b | 2.1 / 5.2 | 2.9 / 4.9 | 0.9 / 3.9 | 2.3 / 3.9 |
| raw a | 2.5 / 5.7 | 2.1 / 4.8 | 3.0 / 4.2 | 1.6 / 3.7 |
| raw b | 2.8 / 5.9 | 1.2 / 4.2 | 0.7 / 3.5 | 2.5 / 3.8 |
| `:443` combined | 2.1 / 5.0 | 3.0 / 5.0 | 0.8 / 4.2 | 2.7 / 4.1 |
| `data-stream.binance.vision` | 3.4 / 7.5 | 1.9 / 5.0 | 3.3 / 4.2 | 0.9 / 4.0 |

- **No stream type wins.** Each connection stays fast or slow (by 2-3 ms) for its whole life,
  depending on the gateway host. The p99 tails reach 20-58 ms on every connection.
- **Fan-in of six connections** gains p50 1-2 ms and p90 4-7 ms over the baseline connection.
  The earlier finding of a whole connection running ~100 ms late did not recur.
- **Perp:** the bookTicker on `/public` combined vs raw differs by 0-3 ms p50, per connection.
  The p99 reaches 127-208 ms on one London connection during the US open.

## (b) Per BTC move: who shows it first (local receipt)

- **Onset:** the first update at least $X from that feed's own price 1 s earlier.
- **Move:** onsets within 1 s of each other in the same direction. Only moves where at least
  half the venue feeds fire are kept.
- **Best Binance:** the earliest of Binance spot book/trade and perp book/trade.
- **Fused:** the earliest of Deribit quote and best Binance.

**London 7 h**, $5 / $10 moves (6923 / 3876):

| feed | first | gain vs baseline p50 ms | earlier than baseline | gain vs best Binance p50 ms (p25, p75) | earlier than best Binance |
|---|---|---|---|---|---|
| **fused Deribit + Binance** | **40% / 41%** | **+119 / +101** | **96% / 97%** | +1 / +7 (0, +101 / +106) | 51% / 54% |
| Deribit quote | 24% / 27% | +67 / +58 | 68% / 69% | **+10 / +14** (-149 / -65, +116 / +117) | **55% / 57%** |
| best Binance | 16% / 14% | +27 / +16 | 93% / 94% | 0 | |
| bot fan-in today (spot + perp combined) | 9% / 6% | +18 / +12 | 74% / 74% | 0 | 4% |
| Binance perp book | 9% / 7% | +25 / +15 | 67% / 66% | 0 | |
| Kraken futures trade | 6% / 7% | +3 / -9 | 51% / 48% | -108 / -101 | 33% / 32% |

**Dublin 7 h**, $5 / $10 moves (6349 / 3490):
- **Deribit quote:** earlier than best Binance in 52% / 52% of moves, median +3 / +5 ms.
- **Fused feed:** median gain over the baseline +116 / +91 ms.
- **Bybit, OKX, Coinbase, Bitstamp:** earlier than best Binance in 10-33% of moves, median
  -36 to -195 ms.

Deribit quote vs best Binance, quiet hours vs US open, at $5 / $10:

| window | London: earlier share, p50 ms | Dublin: earlier share, p50 ms |
|---|---|---|
| 08:05-13:25 (quiet) | 64% / 64%, +21 / +21 | 60% / 57%, +14 / +9 |
| 13:25-15:35 (US open) | 48% / 54%, -4 / +7 | 45% / 50%, -13 / 0 |

**Why Deribit is sometimes first.** On the venues' own clocks (Deribit quote timestamp vs Binance
perp `T`), Binance moves first in **57-61%** of moves, by a median of 35-60 ms. When Deribit moved
first at the source (39-43%), its quote reaches us first in **78-85%** of those moves, by a
median of +144 to +181 ms. When Binance moved first, Deribit's ~95 ms shorter path still gets
its reprice to us first in 33-38% of moves, but the median is -18 to -35 ms. During the US open
the median falls to -104 ms at $5, because Deribit's makers react more slowly. Deribit therefore
adds its own price discovery (European/US flow) plus a geographic head start. It is a second
source, not a faster copy of Binance.

## (d) Polymarket 5m: predictive power and arrival before the reprice

- **Side ask:** the Up ask after an up move, the Down ask after a down move.
- **Reprice:** the first +1 c on that ask. Each box records the PM book itself on the same clock.
- **Hit:** every onset of a feed, scored on whether the side ask reprices within 1 s.
- **Before PM:** market-wide moves with a reprice within 2 s, scored on whether the feed's onset
  arrives before the reprice.

**London 7 h:**

| feed | hit $5 / $10 / $20 | before PM $5 / $10 | median lead over reprice $5 / $10 ms |
|---|---|---|---|
| **fused Deribit + Binance** | | **82.5% / 81.0%** | **+155 / +135** |
| Deribit quote | 0.72 / 0.78 / 0.81 | 68.9% / 70.8% | +107 / +99 |
| best Binance | | 68.0% / 63.5% | +94 / +71 |
| bot fan-in today | | 65.4% / 62.0% | +83 / +64 |
| Binance perp book | 0.72 / 0.78 / 0.81 | 59.4% / 56.5% | +58 / +33 |
| Binance spot combined (baseline) | 0.74 / 0.80 / 0.82 | 51.5% / 48.1% | +9 / -9 |
| Kraken futures trade | 0.67 / 0.72 / 0.76 | 49.3% / 46.2% | -4 / -27 |
| random time and direction | 0.35 | | |

The table covers 4169 / 2342 moves with a PM reprice at $5 / $10, and 3942-7566 feed onsets
at $5.

- **Dublin agrees:** the fused feed is before PM in 82.3% / 80.3% of moves (+160 / +133 ms),
  Deribit in 69.4% / 68.3%, the bot fan-in in 66.1% / 63.1%, and the baseline in 50.9% / 49.8%.
- **US open (London 13:25-15:35):** the fused feed is still before PM in 80.7% / 81.0% of moves
  (+159 / +143 ms). Deribit's own hit drops to 0.66 / 0.75 against the perp's 0.68 / 0.75 and
  the spot's 0.72 / 0.78. In busy minutes Deribit's quote is the noisier of the three.
- **The lead is real time to act:** for half of the moves, the fused feed gives at least
  ~135 ms before the PM book reprices. Our current single spot stream gives about 0 ms.
- **False fires:** the Deribit quote fires more often than Binance (7566 vs 5869 onsets at $5;
  $0.5 tick, jumpier mid). A live trigger should weigh Deribit by its size at the touch, or
  require the Binance perp to agree within ~50 ms when Deribit alone has moved.

## Bot: `--trigger combined` (Rust, 2026-10-15)

The live bot reads `quote.BTC-PERPETUAL` and fires the fused trigger
(`rust/crates/signal/src/trigger/`, Python twin `research/feedrace/analysis/fused.py`, fixtures
bit-identical). With `--fire-window-ms 0` (default) the live trigger reproduces the research
composite: before PM in **82.5% / 80.9%** of moves (+155 / +135 ms), London $5 / $10.
`research/feedrace/analysis/confirm.py` scores the Deribit confirmations
(`data/out/feedrace/confirm-*.json`):

| London $5 (Dublin) | fires | hit 1 s | before PM | lead p50 ms | Deribit-fire hit |
|---|---|---|---|---|---|
| Binance only (1 s window) | 9757 | 0.715 | 61.4% (62.4%) | +77 | |
| fused, no confirm, window 0 | 40169 | 0.730 | **82.5%** (82.2%) | +155 | 0.716 |
| perp agrees within 50 ms, window 0 (bot default) | 37541 | 0.732 | 76.7% (76.8%) | +132 | 0.691 / late 0.812 |
| perp within 100 ms, window 0 | 38082 | 0.732 | 77.9% (77.9%) | +136 | 0.688 / late 0.833 |
| touch size >= 20k weight, 1 s window | 12394 | 0.714 | 71.8% (71.8%) | +129 | 0.754 |

- **Deribit fires are not noisier per fire over 7 h:** their 1 s hit (0.72) equals Binance's.
  The confirmations raise the hit of what they keep by 1-3 pp, and cost 5-11 pp of moves
  caught before PM. The default stays `--confirm perp` as asked. `--confirm none` is the
  research optimum on these two days.

## Next

1. **Bot:** add a Deribit `quote.BTC-PERPETUAL` reader (public, no key; heartbeat with
   `public/test`) to the Rust feed fan-in, alongside the Binance perp and spot feeds, on the
   London box. Score the fused trigger on the live PM book before any money goes in.
2. **Tokyo box:** run `deploy.sh` there for the same tables. Binance should be ~1 ms away and
   Deribit ~200 ms, which bounds what a Tokyo signal with a London relay could win.
3. **SBE:** only if the user creates a read-only Ed25519 key. The expected gain is 0-2 ms.
