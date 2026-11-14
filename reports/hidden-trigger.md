# The missing half of the 5m leaders' trigger

Leaders: A = 0xc53375ff94e96100f2b30a4b5775db35218d69a9, B = 0x3048d65321be3497164cdfc2996f94f98a2e7537.
Data: live recorder runs 1-2 (2026-10-09 17:38 to 10-10 22:03 UTC, every 5m BTC market; Binance
perp book from 10-09 22:03, so 24 h with perp) plus a side recorder (Coinbase, OKX, Bybit, Binance
perp trades) for 3.5 h from 10-10 18:31 UTC. Code `research/hidden/`, tables `data/out/hidden/`.
Read-only throughout.

## Verdict

**The missing half is the Binance order book, not Binance prices.** A and B fire on sub-tick
changes of the Binance BTCUSDT top of book (perp and spot microprice: queue sizes and imbalance at
the best bid and ask) about **0.27 s before their CLOB print**, and buy the side the book leans
toward. Most of their "no-move" fills had no trade-price move at all, so 1 s klines and block
times could not see the trigger. The 0.27 s is Polymarket's **150 ms taker hold** plus ~100-120 ms
from the Binance event to the CLOB.

- **Which side, no-move fills, last 8 h held out:** AUC **0.930 (A) / 0.914 (B)** from the perp
  book alone and **0.958 / 0.944** with spot book, Polymarket book and burst state, against
  **0.556 / 0.542** for the forensic feature on the same fills. A no-fit rule (sign of the perp +
  spot microprice change 0.21-0.33 s before the print, else repeat the own last side inside a
  burst) picks the side in **84% / 81%** of no-move fills at 81-82% coverage.
- **When they fire, 50 ms bins, held out:** AUC **0.807 / 0.798** from state (price level, time
  left, own cadence) rises to **0.940 / 0.922** with the Binance book trigger; the forensic 1-10 s
  spot moves add **0.003 / 0.007**. The top decile of bins holds **84% / 74%** of their fills
  (state alone: 44% / 40%).
- **Reaction latency:** the same-side fill rate peaks **270 ms (A) / 250 ms (B)** after a perp
  tick at **74x / 49x** the base rate; after an isolated perp tick the first same-side fill lands
  a median **286 / 273 ms** later. Minus the 150 ms hold, Binance event to CLOB arrival is
  **~120 ms (A) / ~100 ms (B)**. No wallet among the 25 most active takers peaks below 250 ms.
- **What is left:** in **28%** of no-move fills the perp and spot books disagree (15%; the side
  then follows the perp 51-53%, a coin flip) or both point the other way (12-13%); only **3-4%**
  have no Binance book change at all. Bybit and OKX books add **+0.02 AUC** on 3.5 h; nothing else
  tested closes the gap.

## How the fills were timed

- **Attribution:** each websocket `last_trade_price` (ms CLOB stamp) joined to its Data API
  taker fill by transaction hash: one print and one taker row per transaction, **99.3%** of 411k
  prints matched (97.2% of fills on recorded markets). A 4,371 and B 8,005 taker buys (they never
  sell) in 326 / 335 markets.
- **Block time is late:** Data API (Polygon block) time minus CLOB stamp has median **2.22 s**,
  IQR 1.78-2.64 s, max 11 s. The forensic window "1 s closes 1-4 s before the block" mostly
  covers the second around and after the fill, not the trigger.
- **Taker hold** (coordinator, from https://docs.polymarket.com/changelog/predictions.md and
  `itode: true` on live 5m markets): taker orders wait **150 ms** before matching since
  2026-09-04; cancels do not. A print stamp is send + transit + 150 ms, so a trigger sits
  0.2-0.35 s before the print, which is where the signal is.
- **Book vs print stamp:** the book update a fill causes is stamped 10-30 ms before its print, so
  every "state before the fill" read stops 50 ms before the print.
- **Quiet regime:** 13.4 (A) and 23.9 (B) taker buys per market, against 49 / 92 buys in the
  forensic window. At ms resolution **71% / 77%** of fills had < 0.2 bp spot move in the prior 3 s
  (block-time definition: 72% / 78%), so the no-move half is not a clock artefact.

## Evidence

**Event study** (`eventstudy.csv`, mean signed path on a 10 ms grid). Around no-move fills the
four largest 10 ms steps of perp mid and perp microprice in the bought direction fall at
**-300 to -260 ms** for both leaders (spot: -310 to -250 ms on all fills). The Polymarket book then
drifts their way from about -250 ms (faster takers and maker cancels during the hold) and jumps
at -30 to -10 ms (their own fill).

**Where the side information sits** (no-move fills, test hours, perp microprice change, `side.md`):

| window before the print | A accuracy / coverage | B |
|---|---|---|
| 0.21-0.33 s (trigger) | 0.806 / 0.93 | 0.785 / 0.91 |
| 0.20-0.50 s | 0.819 / 0.98 | 0.808 / 0.98 |
| 0.33-1.0 s | 0.669 / 0.99 | 0.646 / 0.99 |
| 0-0.21 s (inside the hold) | 0.509 / 0.95 | 0.488 / 0.93 |

- **Mid ticks are rare but exact:** a perp mid tick in the trigger window occurs in 10% / 6% of
  no-move fills and picks the side **100%** of the time; the rest is sub-tick.
- **Bigger book changes, surer side** (all no-move fills): change < 0.0001 bp 0.60 / 0.59,
  0.0001-0.0005 bp 0.78 / 0.85, 0.0005-0.002 bp **0.94 / 0.95**, > 0.002 bp **0.99**. 16-17% of
  no-move fills have no perp book change in the window.
- **Stable:** the rule scored 0.74-0.94 in each of the first 20 hours checked one by one.

**Side models** (`side.md`, gradient boosting, train first 16 h, test last 8 h, no-move fills):

| features | A AUC | B AUC |
|---|---|---|
| forensic (block time, 1 s closes) | 0.556 | 0.542 |
| spot trade prices, ms-aligned, 0.05-10 s | 0.606 | 0.495 |
| spot book + spot taker flow | 0.878 | 0.844 |
| **perp book only** | **0.930** | **0.914** |
| Polymarket only (book, flow, state) | 0.835 | 0.682 |
| own burst state (gap, last side) | 0.518 | 0.561 |
| perp + spot + burst state | 0.936 | 0.933 |
| perp + spot + Polymarket + burst state | 0.958 | 0.944 |

**Timing model** (`hazard.md`, 1.57 M bins, 567k held out; label = fill in the bin):

| features | A AUC | A fills in top decile | B AUC | B fills in top decile |
|---|---|---|---|---|
| state | 0.807 | 44% | 0.798 | 40% |
| state + forensic spot | 0.810 | 44% | 0.805 | 43% |
| state + Polymarket flow | 0.852 | 53% | 0.828 | 48% |
| state + spot book | 0.913 | 74% | 0.890 | 64% |
| state + perp book | 0.936 | 83% | 0.915 | 73% |
| **state + Binance book trigger** | **0.940** | **84%** | **0.922** | **74%** |
| everything | 0.947 | 86% | 0.928 | 78% |

**Accounting of no-move fills** (`account.md`, no fit): Binance book trigger on their side
**68.7% / 66.7%**; opposite 12.4% / 13.2%; perp and spot disagree 15.0% / 15.7%; no Binance book
change 3.9% / 4.3% (burst repeat 0.4 / 0.5, Polymarket book moved their way 2.0 / 0.9, nothing
1.5 / 2.9 points). Inventory: the side reduces their own Up/Down imbalance in **50.2% / 51.3%**.

## How strongly a book event triggers them (`respond.md`)

- **Dose-response:** fills per 1,000 bins are 0.6 (A) / 1.4 (B) with no perp book change in the
  trigger window, 11 / 23 for a 0.0005-0.002 bp microprice change and **44 / 70 for 0.002-0.01
  bp** (70x / 50x), flat above that. With a strong trigger: 62-69 (A) / 90-101 (B) while the
  favourite is <= 0.80, 53 / 64 at 0.80-0.90, 0.5 above 0.90.
- **Conversion:** a perp mid tick in an active market (favourite < 0.90, > 30 s left) gets a
  same-side fill 0.15-0.45 s later in **19% (A) / 22% (B)** of cases, 32% for either. The rate
  barely moves with time since their last fill (16-25%) or spread, and drops only when the
  Polymarket book already moved against them (13-17%). Unfilled orders are invisible here, so
  the likely reading is that they send on most ticks and the hold kills many orders.
- **Anticipation:** fills landing < 150 ms after a tick were sent before it; at their send time
  the perp imbalance already leaned the tick's way (+0.63 to +0.75, vs +0.43 one second before
  an average tick).

## Hypotheses

| # | hypothesis | result | class |
|---|---|---|---|
| 1 | Binance perp leads | **Confirmed in a sharper form:** the perp *book* (microprice, imbalance) 0.21-0.33 s before the print, not the perp price. Perp beats spot (side 0.930 vs 0.878, timing 0.936 vs 0.913) but both books carry mostly one signal: when they disagree the side follows the perp 51-53% | explains ~70% |
| 2 | stale-quote sniping on the Polymarket book | Polymarket-only side AUC 0.835 / 0.682, but on top of Binance + burst state it adds 0.022 / 0.011. The book moves their way *after* the trigger (maker cancels during the hold, faster takers). Claims at most 2.0% / 0.9% of no-move fills | lost a comparison |
| 3 | other venues, Chainlink | Chainlink 3 s move: 0.50 / 0.49. Coinbase, OKX, Bybit tick 0-50 ms *after* the perp (median; first in 13-17%). On 3.5 h they add +0.02 AUC; Bybit's book picks the side 0.68-0.69 on fills where Binance's books miss (below) | lost a comparison (small additive) |
| 4 | copying other bots, fixed cadence, inventory | A fills within 50 ms after a same-side B fill in 32.5% of A's fills (B after A 3.3%). A copy lands >= 150 ms after the copied print (hold), so these are one trigger with B ~13 ms faster; on shared isolated perp ticks A lands a median 11 ms after B (56% within 20 ms), but A and 0x0ca4e9d27ff826a109ecbf74754fb66b93f277a6 are as tight (57%): similar paths, no evidence of one operator. Fills 150-300 ms after B (12.8% of A's) score 0.74 on the Binance rule vs 0.82-0.88 elsewhere, so copying could add ~1%, at most 4%. Other takers' flow: 0.54. No lock to the wall-clock second (chi2 5.9 / 31.3 on 9 df). Bursts: follow-ups 0.2-0.6 s after the own last fill (12-14% of fills) repeat the side 71-78% and half of them carry no Binance trigger. Inventory 50% | copying: **proven closed** above 4% (premise: every taker order waits 150 ms); cadence: explains burst repeats only; inventory: closed (50% on 7k fills) |
| 5 | artefact of 2 s blocks and 1 s klines | Block time sits 2.2 s after the match, so the forensic window was misplaced. But at ms resolution 71-77% of fills still show no spot price move: the signal lives in book queues, which no price series carries | explains why the old rule looked weak, not the no-move half |

**Other venues** (`venues.md`, 3.5 h, 887 leader fills, out-of-fold by half hour):

| features | A AUC | B AUC |
|---|---|---|
| Binance books | 0.830 | 0.852 |
| + OKX | 0.829 | 0.866 |
| + Bybit | 0.836 | 0.860 |
| + Coinbase | 0.843 | 0.858 |
| + Binance perp trades | 0.847 | 0.854 |
| + all of them | **0.851** | **0.873** |

- **On Binance-miss fills** (38% / 44% in these hours): Bybit microprice 0.68 / 0.69 at ~60%
  coverage, Coinbase 0.69 / 0.60 at 23-26%, OKX 0.48 / 0.59. A "Binance, else Bybit" rule raises
  coverage from 77% to 90% at ~0.74 on the added fills.
- **No venue leads:** impulse-response peaks are perp 270 / 260 ms, OKX 270 / 260, Bybit 230 / 210
  (its ticks come ~20 ms after the perp), Coinbase 250 / 200 at only 7x / 4x lift.
- **Perp trades** (raw, now recorded): taker flow in the trigger window 0.81 / 0.77 at 27-30%
  coverage, a subset of the book signal.

## Reaction latency (for the infra design)

`irf.md`, venue clocks (Binance stamp T to CLOB print stamp), 24 h:

| event | A peak / lift | B peak / lift | A excess p10 / p50 / p90 | sent before the event, A / B |
|---|---|---|---|---|
| perp mid tick | 270 ms / 74x | 250 ms / 49x | 160 / 280 / 680 ms | 9% / 9% |
| perp microprice >= 0.02 bp | 270 / 77x | 250 / 45x | 160 / 290 / 690 | 9% / 9% |
| spot mid tick | 270 / 53x | 260 / 36x | 90 / 280 / 690 | 14% / 14% |
| spot trade move >= 0.05 bp | 260 / 33x | 260 / 21x | 130 / 270 / 590 | 11% / 10% |
| all other takers, perp tick | 280 / 17x | | 230 / 400 / 810 | 4% |

- **Isolated perp ticks** (none in the prior 1 s): first same-side fill median **286 ms (A) /
  273 ms (B)**, p25 262 / 255, p75 369 / 369; 62-63% within 200-350 ms.
- **Decomposition:** 250-270 ms = 150 ms hold + ~100-120 ms from the Binance stamp to CLOB
  arrival (an upper bound that includes matching and stamping, 10-30 ms). That matches an
  AWS-class Tokyo-to-London path with near-zero decision time (infra plan: 108-123 ms), not a
  private link.
- **Fastest wallets** (`peers.md`, same impulse response, 25 most active takers): 250 ms
  0x21f4c1a1be34a39a7bc20985df4b7e5a39fb691d (38x) and B (49x); 260 ms
  0x764fd57b0b885cbeada5a119cdf0a113ee4ec347 (85x); 270 ms A (74x); 280 ms
  0x0ca4e9d27ff826a109ecbf74754fb66b93f277a6 (96x, the sharpest) and
  0x1b58d3de60d7f9e1aefdc9449e8d3733ea096f11. **Nobody peaks below 250 ms**, so ~100 ms arrival
  plus the hold is the floor everyone currently sits on.
- **Price during the hold** (`value.md`): the ask of the side bought moves >= 1 c against A in 45%
  of fills (B 18%; B usually fills first); A pays +0.55 c and B +0.06 c over the ask at send on
  average (p90 +3 / +2 c), so both send marketable limits with ~1-3 c of room.

## What the hidden half is worth (`value.md`, 2 s markout after the full 0% tier fee)

No-move fills with the Binance book on their side: **+1.26 c/$ (A), +1.34 c/$ (B)**; book against
them: +0.78 / -0.76; move fills against the book: **-4.1 / -5.0**. In this quiet window the
no-move half pays a little, and the fills against the Binance book are the losers.

## What would have to be true (the unexplained ~28%)

Four variants tried (`side_rich.py`, `venue_cmp.py`), none closes it:

- **Learned weights and memory:** 15 fine windows (0-2.5 s) of perp and spot microprice and
  imbalance changes plus imbalance levels: no-move AUC **0.942 / 0.926** vs 0.930 / 0.914 for the
  perp-book group (+0.01).
- **Event anchoring for latency jitter:** sign of the largest 20 ms microprice step 0.15-0.45 s
  before the print: perp 0.80 / 0.79, spot 0.82 / 0.80. Same ceiling.
- **Pricing instead of following:** side = sign of (perp-implied fair change minus Polymarket mid
  change) over 1 / 3 / 10 s up to send time: 0.59 / 0.53 / 0.51 on all fills and **0.48 / 0.47 /
  0.45 (A), 0.51 / 0.49 / 0.48 (B) on the Binance-opposite fills**. A value rule does not explain
  them; a level-based fair scored 0.46-0.49 too.
- **Other venues:** +0.02 AUC (above).

For the rest to be explained, one of these would have to be true:

- **A multi-venue signal we only partly see:** Bybit already picks 0.68 of Binance-miss fills;
  a weighted book across Binance, Bybit, OKX and Coinbase (and venues not recorded, such as
  Hyperliquid or Deribit) would need to reach ~0.9 there. Testable with a longer side recording.
- **A longer memory we have not modelled:** on opposite-side fills the 0.33-1 s perp book window
  points with the side (0.59-0.62) while 1-10 s perp moves point against it (0.39-0.42): they
  bought the reversal of an earlier move. Test: a rule on the last N book events, not windows.
- **Order-level noise:** unfilled orders are invisible; if they send on both sides in some states
  (85-90% of their shares end paired), the order that fills can be the opposite one. Testing it
  needs order-level data, which we do not have.

## Caveats

- **Quiet 24 h:** fewer, smaller moves than the forensic window; the trigger mix may shift in
  volatile hours (big moves are the "move" fills the forensic study already explained).
- **Spot bookTicker has no venue stamp:** its time is receipt minus the hour's median spot trade
  lag; tens of ms of jitter blur the spot-vs-perp comparison in spot's disfavour.
- **Venue clocks assumed aligned:** receipt lags (Polymarket ~11 ms, Binance ~110-115 ms on a
  healthy connection) fit that; Binance connections running ~100 ms late affect receipt only, not
  the T stamps used here.
- **Hedging alternative not excluded for size-only book changes:** a leader's own Binance order
  0.27 s before its Polymarket fill would look the same. Implausible (they end 85-90% paired) and
  it cannot produce the 74x response to market-wide perp ticks.
- **Peers are a common trigger:** "everything" side AUC 0.984 for A includes B's fill 0-50 ms
  earlier, which is not a signal anyone can trade on.
- **Other venues: 3.5 h only** (887 fills); their +0.02 is within what one more quiet hour can move.

## Perp trade stream and run 3

- **Fix:** Binance moved USD-M streams to routed paths; the legacy `/stream` path still serves
  `@bookTicker` and `@trade` but silently drops `@aggTrade`. `btclat/live/feeds.py` now uses
  `wss://fstream.binance.com/public/stream?streams=btcusdt@trade/btcusdt@bookTicker` (raw trades,
  one message per fill with E = T; `@aggTrade`, served on `/market`, is stamped ~150 ms after its
  trade time). Tested standalone and through the 3.5 h side recorder.
- **Run 3 started** 2026-10-10 22:03 UTC after run 2 stopped: `python3 -m btclat.live --hours 48`
  (PID 2664441, log `data/live/recorder3.log`), ends ~2026-10-12 22:03 UTC. Its first 20 s held
  495 perp trades and 24,925 perp book messages.

## Reproduce

```
python3 research/hidden/fetch.py                 # Data API taker fills + the leaders' own fills
nice -n 10 python3 research/hidden/prep/run.py   # parse hours (2 workers, venue hours included)
python3 research/hidden/attrib.py                # join prints to wallets by tx hash
nice -n 10 python3 research/hidden/features.py   # per-fill ms features
python3 research/hidden/eventstudy.py && python3 research/hidden/side.py
python3 research/hidden/hazard.py && python3 research/hidden/irf.py && python3 research/hidden/respond.py
python3 research/hidden/account.py && python3 research/hidden/value.py && python3 research/hidden/peers.py
python3 research/hidden/side_rich.py && python3 research/hidden/venue_cmp.py
python3 research/hidden/venues.py --hours 4      # optional: side recorder (Coinbase, OKX, Bybit, perp trades)
```
