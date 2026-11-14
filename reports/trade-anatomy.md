# Trade anatomy of the 5m leaders, and what speed is worth

Sources: forensic fills 2026-10-07 to 10-09 (`python3 research/profit/anatomy.py`, tables in
`data/out/latency/anatomy.md`); live run 1, 4 h (`python3 research/live/speed.py`,
`data/out/live/speed.csv`). Net = PnL minus the full taker fee (our 0% rebate tier).

## How they trade

| | leader A (0xc533) | leader B (0x3048) |
|---|---|---|
| buys per 5m market, mean / median | 48.8 / 42 | 92.5 / 85 |
| USD per market, median | $645 | $1,090 |
| size per buy | 60 shares, median $10.80 | 60 shares, median $7.90 |
| taker share of buys | 70% | 63% |
| buys that win at settlement | 52.4% | 51.1% |
| buys with a positive 2 s markout | 63.5% | 63.9% |
| net per $ at our tier | +1.36 c | -0.34 c |
| markets net positive at our tier | 56% | 47% |

**Win rate is the wrong yardstick.** Each buy pays $1 or $0 at the close, so even a well-priced
buy loses often: cheap tokens (0-0.30) win only 27% yet net +14-18 c per $. Profit comes from
paying less than the true probability. The 2 s markout (did the price move our way right after
the fill) is the cleaner test, and 64% pass it.

## Why buys lose (taker buys, net c per $ at our tier)

- **No Binance move behind the buy:** 45-48% of their USD, -0.3 / -1.4 c. Background trading.
- **Buy against the latest Binance move:** 15-16% of USD, -5.5 to -12.9 c.
- **Aligned with a move > 1 bp:** +6.4 to +15.0 c; > 2 bp: +11.7 / +15.0 c, 93% positive markout.
- **Expensive tokens (0.70-0.90):** win 77-78% but net -2.9 / -4.9 c: small wins, full losses.
- **Buys that reverse the previous side:** 41-42% of USD, -0.3 / -1.6 c vs +2.5 / +0.6 c.
- **Fee:** gross markout is ~3 c per $; the 0% tier fee (~2 c) eats most of the average buy.

**Filtered, the same flow pays:** keeping only buys after an aligned move > 1 bp at price < 0.70
turns leader B from -$1.0k/day to +$5.5k/day at our tier (+14.7 c per $; leader A +$3.4k/day,
+11.2 c). In-sample, and their speed is included, so this is an upper bound for a filter.

## What speed is worth (live run 1, 5m, taker buys on the burst side)

| fill delay after the Binance trade | USD | net c per $ | edge positive |
|---|---|---|---|
| before the 1 bp onset (reacting earlier) | $4,243 | +10.7 | 81% |
| 0-150 ms | $1,552 | +11.0 | ~80% |
| 150-300 ms | $4,283 | +5.3 | 63% |
| 300-500 ms | $5,436 | +2.4 | 44% |
| 0.5-1 s | $7,330 | +0.1 | 42% |
| 1-2 s | $11,919 | -2.4 | 38% |

- **Faster pays, steeply:** within 150 ms about 11 c per $; after 500 ms nothing; after 1 s a
  loss. Most of the volume arrives late and loses.
- **The biggest winners fire before our onset:** they trade on the first part of the move (or
  on the perp, which leads spot), not after a full 1 bp.
- **Fastest reprices:** the book has moved as early as 4-16 ms after the onset trade, and in a
  few bursts before it. No order crosses Tokyo-London in 20 ms (best link ~66 ms one way), so
  those bots anticipated the move: the speed that matters is measured from the START of the
  move, and it is won with an earlier trigger, not only a faster wire.
- 15m shows the same shape at half the size (+4.4 c within 150 ms, negative after 500 ms).

Caveat: run 1 is a quiet 4 h; the sub-150 ms buckets hold 158 trades. Run 2 (24 h) will tighten it.

## How often Binance "updates", and why A and B trade different amounts

Binance has no fixed update count; it streams continuously. Run 2, 12 h (01:00-13:00 UTC, quiet):

| Binance stream, per 5 min | median | max |
|---|---|---|
| spot order-book messages | 7,095 | 18,430 |
| perp order-book messages | 25,523 | 71,702 |
| spot trades | 1,933 | 8,039 |
| spot best-price changes | 70 | 577 |
| perp best-price changes | 127 | 726 |
| spot 1 s moves >= 1 bp (3 s apart) | 2 | 14 |

In the forensic window (2026-10-07 to 10-09, far more volatile) a 5m market held a median 9 seconds
with a >= 1 bp Binance move (mean 17, max 211) and 22 with >= 0.5 bp.

**A and B do not trade every Binance update; each runs its own trigger.** Per 5m market A buys in
a median 29 distinct 2 s blocks (24 as taker) and B in 49 (39 as taker); A also gets 14.7 and B 34.6
resting (maker) buys filled. B trades in 16,633 blocks A never touches, A in 5,114 that B skips,
13,146 shared. Their taker blocks track Binance only loosely: per-market correlation with the count
of >= 0.5 bp seconds is 0.29-0.30, and in 46% (A) / 51% (B) of taker blocks Binance moved under
0.2 bp in the prior 3 s. **So B's trigger is looser (more, weaker signals; more maker and pair
flow), which is why B trades twice as often and nets less per $.** What fires them on no-move
blocks is still unknown: candidates are the perp (not in the forensic data), stale Polymarket
quotes relative to their own fair value, and the clock skew of 2 s block times.

## Reverse-engineered trigger (`research/trigger/reverse.py`, `data/out/latency/reverse.md`)

Per live market second, block-time resolution (2 s), Binance 1 s closes. Held-out markets.

- **When they fire** (gradient boosting AUC 0.85 / 0.85): price level, own cadence and time left
  dominate; Binance move size adds a little. Fire rate per second, A / B:
  - market undecided (favourite 0.50-0.60): 0.19 / 0.28; favourite 0.80-0.90: 0.08 / 0.14; > 0.90: ~0.
  - last 30 s: ~0.01; 240-300 s left: 0.14 / 0.22.
  - Binance 3 s move < 0.2 bp: 0.07 / 0.11; > 3 bp: 0.17 / 0.23.
  - clustered: 2-4 s after their own last buy 0.20 / 0.29; > 20 s after: ~0.02. Median gap 3 s.
- **Which side** (AUC 0.75 / 0.71): the direction of the last ~3 s Binance move picks the side in
  69% / 65% of fires. Their position, last side and Up+Down pair gain predict nothing (50-53%).
  On the ~half of fires with no Binance move the side is a coin flip on every feature we have,
  so that half runs on information missing from 1 s spot data (likely the perp, sub-second).
- **Rule, as far as it can be read:** while the market is undecided and > 30-60 s remain, fire in
  bursts every ~1-4 s, more often after larger Binance moves, and buy the side of the latest move.

## Resting (maker) orders and who trades with whom

- A and B almost never trade with each other: < 1% of either one's filled resting orders were
  taken by the other; 91-93% were taken by wallets outside the latency-bot set.
- Their resting bids are not pair-completion (46-47% on the side opposite their position, same as
  chance); they earn +2.2 / +2.7 c per $ 2 s markout and pay no fee.
- They still end each market with 85% / 90% of shares in Up+Down pairs (pair cost 1.0008 / 0.989),
  so the net bet on the outcome is small.

## 10 ms speed buckets, runs 1 + 2 (21 h), 5m taker buys on the burst side

Pooled: 0-50 ms +14.5 c per $ ($2,103), 50-100 ms +19.6 c ($2,346), 100-150 ms +12.1 c ($2,129),
150-200 ms +4.1 c, 200-300 ms +2.3 c, 300-500 ms +0.2 c, 0.5-1 s -3.6 c, 1-2 s -2.4 c; before the
1 bp onset +16.8 c ($16,282). Each 10 ms bucket holds only 25-39 trades, so single buckets swing
from +4.6 to +27.9 c on noise. **Inside 150 ms there is no measurable gain from being faster; the
cliff is at 150-300 ms.** 15m: same cliff, smaller numbers. Table: `data/out/live/speed.csv`.

**Correction 2026-10-10 (taker delay):** Polymarket holds every marketable order on crypto up/down
markets for 150 ms before matching (changelog 2026-09-04; live 5m markets `itode: true`). A fill
at +X ms was therefore SENT at about +X - 150 ms. The 12-20 c per $ zone (fills within 150 ms of
the onset) consists of orders sent before the onset trade existed: anticipation, not a faster
wire. A purely reactive taker cannot fill before ~200 ms (physical floor + hold). See
reports/infra-plan.md.

## Competitor timing: the reactive wave (runs 1 + 2, 5m, burst-side taker fills)

Fills per 50 ms after the Binance onset trade (venue clocks): a flat ~100-175 per bin from -500 to
+150 ms (background and anticipation), 189 at 150-200, 231 at 200-250, then **499 at 250-300 and a
peak of 695 at 300-350 ms**, decaying to ~250 by 1 s. With the 150 ms taker hold, the reactive wave's
orders arrive **~100-200 ms after the Binance trade** (AWS-class routes, 108-123 ms one way), and
its front edge sits at ~100 ms arrival. A cheap Dublin build (~113 ms arrival, ~263 ms fill) would
land at the front of this wave; a private-link build (69-78 ms) ahead of it. Anticipating orders
(filled before +150 ms, sent before the onset) are a minority by count but carry the best edge.

**Delay "bypass" check (2026-10-10):** no documented way to shorten the taker delay. History from
Polymarket's changelog and press: 500 ms (removed Feb 2026), 250 ms (Jun), 50 ms (Aug 17), 150 ms
(Sep 4, current). Orders that rest on the book (maker) and cancels are not delayed; a taker order
sent ~150 ms early (anticipation) hides the delay. Verifying the live hold needs one real 5-share
order from a permitted host, which needs the user's explicit approval.
