# Beat the hold: what the taker hold is, how the leaders get ahead of it, and what we can do

Data: our own logged venue answers (hold, dup, maker and taker live runs of 10-14, the live pairs
run of 10-14/15: 654 leg-1 and 34 leg-2 FAKs), the 48 h Dublin tape (10-12/13, leaders' fills
timed to the ms), the dry recording of 10-14 and the live recorder of 10-11 (Chainlink). Pair
economics as in `reports/pairs-live-gap.md` (pe = locked - gas + residual marked at bid - fee at
end - 15 s). Held out = Dublin 10-13 + dry 10-14 (339 markets), selection = Dublin 10-12. CIs are
market bootstraps; "vs" columns are paired by market. Code `research/beathold/`, outputs
`data/out/beathold/`. Read-only: the live bot, server and recorder were not touched.

## Verdict

**Most promising route: a short-lived resting leg 1 instead of the taker FAK.** On each v1 >= 3 c
signal, rest a post-only bid one tick inside the spread on the signal side for 0.5 s. Cancel it
early if the Binance perp moves >= 0.1 bp against that side. Leg 2 stays the current taker.
- **Result:** held out **+$29.5/day [+10, +54]**, against the current rule's -$9.0 [-39, +19].
  Paired gain **+38.5 [+8, +71]**. Selection hours: +11.7 [-6, +28], paired +24.1 [+3, +48].
- **Volume:** 11.4 paired sh/h at 13.6 c per pair, completion 0.85, peak capital max $22.
- **Why it works:** it gets its fills without paying the 150 ms taker delay. Our cancels are
  answered in 33-88 ms and are not held, while a taker crossing our quote is held >= 150 ms.
- **What it needs:**
  1. Insert and cancel latency of 150 ms or better: +24 at 150 ms, +0.3 at 250 ms.
  2. A live check of the maker fill model, which has never been validated for pairs. The live
     inside-gate hour gave 0 real fills where it predicted 1.
  3. GTC plus an explicit cancel, because GTD requires an expiry of at least 180 s.
- **Its edge is the short life, not the guard:** without the Binance cancel it holds +26.5
  held out, but falls to +0.7 on selection. It took 4 rounds and 59 arms; the pick was made on
  selection, so expect shrinkage.

**The lead model, as asked (predict the Polymarket ask >= 400 ms ahead): lost, 4 variants.**
- **Held-out pair economics:** every variant is below v1 >= 3 c under every fill model. Under
  the timing-aware model the best is +4.7 vs v1's +38.4 $/day; under `corr` the best variant is
  +10.6 [-17, +41] over v1, a tie at near-zero volume.
- **Why:** the 5 s Polymarket move is predictable (held-out corr 0.28; the top 1% moves +10.9 c),
  but only 1% of those rows still have the ask at our price after a 270 ms hold.
- **The predictable-and-survivable subset loses:** fit only on rows a taker could buy, the top
  0.1% earn -2.4 c/sh.
- **Chainlink push timing gives no lead:** the book does not reprice at the push (dpm on dcl
  -0.08 c/bp, t -2.0, vs Binance +1.48, t 37).

**The hold:**
- **The deliberate part:** a documented **150 ms crypto taker delay** (changelog 2026-09-04;
  50 ms from 08-17, 250 ms before). The order is held, then validated again, and the API answers
  after the hold.
- **Who it hits:** it applies to every FAK, FOK and marketable GTC we sent. It does not apply to
  cancels, resting post-only orders or pre-match rejects.
- **The rest is queueing:** our holds stretch with venue feed stalls (Spearman 0.83) and run long
  exactly when the move is real.
- **The leaders are no faster on the signal:** they are matched about 250-270 ms after the
  Binance step, at the standing pre-move ask, about 110-170 ms before we would be. That gap is the
  hold, not the signal: their implied decision-to-match is ~180 ms, ours 270 ms quiet, 330 ms p50.
- **Co-location alone:** it saves about 6-10 ms net. It matters only if whitelisting shortens the
  hold. A **150 ms decision-to-match** puts the current rule at -3.9 (corr) to +95.9 (bn) $/day;
  table 6 gives every hold.

## 1. The hold mechanism (`hold/acks.py`, `hold/endo.py`, `data/out/beathold/{acks.csv,endo.md}`)

**Documented (Polymarket docs, fetched 2026-10-15):**
- **Order lifecycle:** "Taker delay: used on selected crypto and finance up/down markets. The
  order is held ..., then validation runs again and the order is matched or placed on the book."
- **Answer timing:** "The API waits for this hold and returns the final order result." This is
  unlike sports markets, which answer `delayed` at once.
- **Delay length (changelog):** 2026-08-17 "now `50ms`, down from `250ms`"; 2026-09-04 "now
  `150ms`, up from `50ms`". The lifecycle page and the `itode` market field still say 250 ms.
- **Cancels:** a held order "cannot be canceled" during the delay. Cancels of other orders are
  not delayed.
- **Post-only:** GTC/GTD only; a crossing post-only order "is rejected instead of executed".
- **Batch endpoint:** not documented with respect to the delay ("each order is evaluated
  independently"). We never sent a batch, so this is untested.
- **Unverified:** a 500 ms crypto speed bump was reportedly removed in Feb 2026 (Protos). The
  origin servers are reportedly in AWS eu-west-2 behind Cloudflare (Glassnode).
- **Co-location:** confirmed for us on 10-15 (whitelisted wallets, eu-west-2, Cloudflare stays).

**Our answers, send to HTTP answer (ms):**

| order | n | min | p50 | p90 |
|---|---|---|---|---|
| resting post-only GTC (hold test control / dup test) | 5 / 15 | 36 / 35 | 45 / 38-63 | 536 / 45-334 |
| post-only GTD insert, live maker runs | 42 | 47 | 147 | 334 |
| **post-only crossing the book: rejected** | 1 | 50 | **50** | |
| cancel of a resting order (hold test / maker runs) | 5 / 42 | 30 / 37 | **33 / 88** | 359 / 194 |
| duplicate copy rejected (pairs live, leg 1) | 1,308 | 31 | 45 | 102 |
| balance reject (taker bot) | 34 | 37 | 49 | 62 |
| marketable FAK / FOK / GTC on cheap tokens (hold test, matched) | 2 / 1 / 1 | 206 | **210 / 222 / 216** | |
| marketable GTD | 1 | | 36 (rejected: expiry >= now + 180 s) | |
| leg-1 FAK, marketable on arrival, killed / matched | 548 / 46 | 197 / 202 | 344 / 451 | 1,226 / 1,252 |
| **leg-1 FAK, not marketable on arrival, killed** | 58 | **182** | **306** | 882 |
| leg-2 FAK, matched | 27 | 204 | 274 | 642 |

- **Everything validated before the hold answers in ~35-60 ms.** That covers dedupe, balance,
  post-only cross checks and inserts that rest.
- **Every FAK, FOK and marketable GTC is held about +165-175 ms:** the 150 ms delay plus
  processing. This happened even on cheap tokens where nothing moved.
- **The hold also applies to FAKs whose limit was already below the venue ask 10 ms after the
  decision** (58 orders, min 182 ms). The delay is keyed on the order type, or on a check that
  ran before the book moved, not on crossing by a given number of ticks. One-tick crossings
  (38 of the 58 were 1 tick through after arrival) look the same as deeper ones.
- **Post-only skips it.** A crossing post-only order is rejected in 50 ms, so it cannot be used
  as a fast taker.

**Hold beyond 150 ms: queueing, and it is endogenous.**
- **Feed stalls:** decision-to-match is 268 ms p50 on quiet orders (no gap > 30 ms in the
  venue's book stamps during the hold), against 0.68-1.6 s when the feed stalled.
- **Correlations:** Spearman of hold with the longest venue-stamp gap is +0.83, with the message
  rate in the second before is -0.56, and with the lead L (decision to the ask leaving our limit)
  is +0.56.
- **Fill rate by lead L** (live vs the same holds drawn independently):

| L (s) | n | live fill | independent hold | hold p50 (s) |
|---|---|---|---|---|
| 0-0.1 | 166 | 0.00 | 0.03 | 0.25 |
| 0.2-0.3 | 81 | 0.06 | 0.28 | 0.34 |
| 0.3-0.4 | 47 | 0.11 | 0.56 | 0.44 |
| 0.4-0.5 | 32 | 0.13 | 0.66 | 0.53 |
| 0.5-0.75 | 46 | 0.17 | 0.76 | 0.78 |
| 0.75-1.0 | 24 | 0.04 | 0.83 | 1.05 |
| 1.0-1.5 | 31 | 0.19 | 0.90 | 1.39 |

  The venue answers a median 75-175 ms after the ask leaves, at every lead. Even when the visible
  ask stays 0.4-1.5 s, 81-96% of orders are held past it. Quiet orders only: the same shape
  (0.4-0.5 s: 0.18 live vs 0.85).
- **No race reproduces the adverse selection:** ten variants against the visible book or against
  the Binance move all keep the fills' 5 s markout at +2.1 to +5.7 c, against +0.2 live. The best
  Binance race reproduces the fill rate (0.066) with AUC 0.73. `corr` (AUC 0.90), which uses the
  5 s look-ahead, is the only model that matches. Fills happen when Binance did not move: perp
  move in the second before the decision 0.00 bp for fills, 0.45 bp for kills.
- **Co-location:**
  - **Network:** Dublin to London saves ~10 ms one way on the order. Binance reaches London
    ~4 ms later than Dublin (`reports/fast-link.md`), so the net is about 6 ms.
  - **Earlier match:** 30 ms earlier did nothing measurable (`reports/live-hold.md`).
  - **Cloudflare:** cannot be bypassed.
  - **What could matter:** whether whitelisted orders skip the queueing above the 150 ms. Ours is
    ~120 ms above it on quiet orders; the leaders' implied total is ~180 ms. The Dublin and London
    hold tests (dublin-hold-20261015) answer this; table 6 converts the answer into $/day.

## 2. When the leaders fire (`leaders/`, `data/out/beathold/leaders.md`, 48 h tape, taker fills)

| | A | B | our v1 |
|---|---|---|---|
| perp microprice step toward the side -> event (peak of the lag profile) | 270 ms (match) | 250 ms (match) | **110 ms (decision)** |
| our match after the same step | | | ~360-440 ms |
| px vs ask in force just before their match: 0 / +1 / >= +2 c | 93 / 5 / 0% | 94 / 4 / 1% | |
| paid <= ask 250 ms before the match | 46% | 80% | |
| their size >= 90% of that level | 81% | 84% | |
| ask +1 c at their match / within 250 ms | 69% / 83% | 73% / 85% | |
| perp 1 s move toward the side >= 1 / 2 bp | 11% / 2% | 10% / 2% | |
| mid 1 s / 5 s after - px | +1.82 / +1.87 c | +1.81 / +1.84 c | |
| fee at our 0% tier | 1.50 c | 1.49 c | |

- **They are matched before the makers reprice.** They take the standing pre-move ask, usually
  the last stale level, and the reprice follows their print. They do not pay up at the match.
- **On our signals:** for v1 >= 3 c, the venue ask leaves our seen price a median **59 ms** after
  our decision (88% before decision + 270 ms; already gone at the decision in 34%).
- **Leader on the same token:** matched before decision + 250 ms in **45%** of our signals, a
  median **107-127 ms after our decision**, at our seen price or 1 c above.
- **Their inferred send** (match - 190 ms) is **63-83 ms before our decision**.
- **Most of their fills are elsewhere:** only 7-8% follow a v1 signal; they trade many more,
  smaller moves.
- **What their lead is made of:** their match is ~110-170 ms ahead of ours on the same Binance
  step, and our decision is only ~30-40 ms later than their send. Most of the gap is the venue
  hold (theirs ~180 ms decision to match, ours 270-330 ms), not the signal.
- **Their fills earn +1.8 c** against a 1.5 c fee at our tier: thin even for them. Their profit
  comes from the 50% rebate and the residual (`reports/pairs-leaders.md`).
- **Clocks:** venue ms, Binance exchange time and our wall clock are taken as UTC. The Dublin
  book feed lags the venue by ~80 ms, and the match row is the book row that removed the level
  (the print is stamped ~21 ms later).

## 3. Lead models (`lead/`, `data/out/beathold/{lead_fit,lead_diag,chainlink}.md`, `lead-held.csv`)

**Rows:** every 50 ms of every market, both sides, 7.4 M rows.

**Features (56):**
- Binance perp and spot top of book: mid changes over 50 ms to 5 s, microprice, queue imbalance
  and its change, update counts, age.
- Spot trade flow, the perp/spot basis.
- The BTC fair value (strike = start mid, 60 s vol).
- The Polymarket top of book on our view, plus depth 100 ms ago.
- Chainlink-timing proxies.

**Labels:** a taker buy at our seen ask matched 270 ms later (the quiet live hold), 5 s mark.

**Fill models in the pair engine (`fill/models.py`):**
- `corr`: validated for v1; it kills informed fills whatever their timing, so it is pessimistic
  for earlier signals.
- `bn`: timing-aware. A fill survives only if the match beats the makers' Binance trigger
  (0.5 bp from 1 s before) + 50 ms. Calibrated on the live orders: fill 0.066 vs 0.073 live.
  Fills' 5 s markout +2.3 c vs +0.2 live, so it is optimistic.
- `none`: visible book only.

Thresholds were set on selection at 0.5x / 1x / 2x v1's signal rate.

| held out, live hold pool | bn $/day | corr $/day | vs v1 under corr | none $/day |
|---|---|---|---|---|
| **v1 >= 3 c (reference)** | **+38.4 [+3, +74]** | **-9.0 [-39, +19]** | | **+67.3 [+18, +117]** |
| A: regress value under bn, 0.5x / 1x / 2x | +4.7 / -29.2 / -54.3 | -2.4 / -17.1 / -66.2 | +6.6 / -8.1 / -57.2 | +4.7 / -28.7 / -74.7 |
| B: classify "the move comes after our match" | -102 / -126 / -182 | -72 / -155 / -155 | -63 / -146 / -146 | -103 / -126 / -183 |
| C: A + Chainlink-timing proxies | -4.9 / -37.2 / -50.2 | -0.5 / -27.5 / -73.3 | +8.5 / -18.5 / -64.3 | -4.9 / -35.2 / -61.4 |
| D: regress value under the visible race | -0.3 / -11.8 / -82.5 | +1.6 / -3.1 / -61.5 | +10.6 / +5.9 / -52.4 | -0.3 / -11.8 / -83.2 |

At a fixed 150 ms hold (`lead_hold-held.csv`) every variant still loses to v1 (v1 bn +95.9; best
lead +2.9).

**Lead fills, held-out rows at 1x:**
- **Fill rate high, quality low:** 0.76-0.98 of lead fills survive the hold, but they earn
  -5.3 to +0.1 c/sh. A and D score AUC 0.47-0.50 on their own target, C the same; B scores AUC
  0.71 on its label but buys spread widenings.

**Why (diagnostics, `lead_diag.md`):**

| model of the 5 s side-mid move | held corr | top | realized move | survives the hold | move when it survives | v_bn c/sh |
|---|---|---|---|---|---|---|
| fit on all rows | 0.28 | 1% / 0.1% | +10.9 / +20.2 c | **1% / 0%** | -0.7 c | -0.02 / 0.00 |
| fit only on survivable rows | 0.20 | 1% / 0.1% | +1.4 / +0.3 c | 52% / 55% | **-1.1 / -2.4 c** | -1.54 / -2.43 |

The Polymarket move is predictable from public data only once Binance has moved, and then the
makers have moved too. Before that, nothing in the Binance book, flow or fair value predicts a
move that lands after our match.

**Chainlink (`lead/chainlink.py`, 20,908 pushes over 6 h):** push - observation lag p50 1.17 s.
The book does not move at the push: |dpm| per 50 ms bin is flat around it (0.07-0.10 c).
Regression dpm ~ dcl + Binance(pre) + Binance(on): **-0.08 (t -2.0)**, +0.20 (t 6.4), +1.48
(t 37). Makers quote off Binance, not the oracle push.

## 4. Fills that do not depend on the move failing (`routes/guard.py`, `route*-{sel,held}.csv`)

**The asymmetry we use:**
- A taker crossing our resting bid is held >= 150 ms (engine XHOLD 270 ms).
- Our cancel is answered in 33-88 ms and is not held.
- So a resting quote cancelled the moment Binance turns against it is gone before any taker
  reacting to the same move can match it.
- The engine's maker legs fill on recorded taker flow at our price behind the queue, with the
  rival haircut and our insert/cancel latency (`legs/maker.py`). `corr` touches only taker leg 1.

**Rounds:**
1. Join the bid vs one tick inside, life 2 / 10 s, guard 0.3-1 bp, v1 signals vs every trigger
   row. **Long lives lose** (-71 to -659 $/day). 2 s with the 0.3 bp guard ties (+1.4).
2. Life 1-2 s, guard 0.1-0.3 bp, v1 3 / 5 c.
3. Controls and the next step: no guard, 0.5 s life, 5 sh clip.
4. Sweep of the winner: life, guard, latency, fee.

| arm (held out unless noted) | pe $/day [CI] | vs current [CI] | selection | pairs sh/h | c/pair | compl |
|---|---|---|---|---|---|---|
| current rule (taker leg 1, i = 0) | -9.0 [-39, +19] | | -12.3 | 18.4 | 9.1 | 0.71 |
| join bid, 2 s, no guard (pairs-live-gap) | -43.3 [-92, +6] | -34.3 | -70.7 | 42.6 | 8.3 | 0.64 |
| guard v1 3c, 2 s, 0.3 bp, inside | +1.4 [-41, +46] | | -40.1 | 35.7 | 10.1 | 0.69 |
| guard v1 3c, 1 s, 0.1 bp, inside | +25.9 [-2, +55] | | -6.6 | 19.1 | 12.1 | 0.75 |
| join v1 3c, 1 s, inside, no guard | +10.1 [-25, +45] | +19.2 [-22, +59] | -17.8 | 21.9 | 11.7 | 0.68 |
| **pick: guard v1 3c, 0.5 s, 0.1 bp, inside** | **+29.5 [+10, +54]** | **+38.5 [+8, +71]** | **+11.7 [-6, +28]** | 11.4 | 13.6 | 0.85 |
| pick, no guard | +26.5 [+4, +52] | +35.6 [+5, +69] | +0.7 | 12.8 | 12.8 | 0.81 |
| pick, at the bid | +23.5 [+4, +47] | +32.5 [+2, +64] | +10.5 | 8.1 | 15.5 | 0.81 |
| pick, life 0.25 / 0.75 s | +24.0 / +23.4 | +33.1 / +32.5 | +3.8 / +3.5 | 7.3 / 16.4 | 15.0 / 11.4 | 0.90 / 0.79 |
| pick, latency L 100 / 150 / 250 ms | +20.3 / +24.0 / +0.3 | +29.4 / +33.0 / +9.4 | +3.6 / -1.3 / -11.7 | 9.8 / 9.5 / 9.9 | | 0.81 / 0.77 / 0.68 |
| pick, 5 sh clip (1 s life) | +13.1 [-2, +29] | +22.1 | -1.6 | 9.9 | 11.9 | 0.73 |
| pick, v1 >= 4 c | +11.9 [-7, +33] | +20.9 | +1.0 | 5.2 | 14.8 | 0.78 |
| pick, taker fee x0.5 (leaders' tier) | +30.3 [+10, +55] | +39.3 | +10.8 | 11.4 | 13.8 | 0.85 |

- **Short life is the lever.** Residual falls from -$49/day (current) to -$7.6/day: a 0.5 s
  quote inside the spread fills on flow that does not keep going.
- **The guard adds +3 held out and +11 on selection**, and is never negative. Guard size 0.05
  to 0.2 bp makes no difference held out.
- **Capital fits $100:** peak p95 $10.8, max $22.
- **Latency is the binding condition:** the engine default (50 ms) assumes the Dublin probe.
  The live maker runs measured insert p50 147 ms and cancel p50 88 ms, so L 100-150 ms is the
  realistic row: +20 to +24 held out, -1 to +4 on selection.

## 5. Classification (improvement discipline)

| idea | class | premises / what reopens it |
|---|---|---|
| lead model, 4 variants (A-D) | **lost a comparison** to v1 under all 3 fill models | 48 h of public Binance/PM data; reopens with a private faster signal (another exchange's book, OTC) that moves before Binance |
| "fire 400-500 ms before the ask" premise | **closed under its premises** for public data | predictable rows have a 1% hold survival; survivable rows have no positive move (`lead_diag.md`) |
| Chainlink-push timing | **proven closed** (6 h, 20,908 pushes) | book does not reprice on the push; reopens only if makers start quoting off RTDS |
| co-location, network part (~6-10 ms) | lost a comparison (nothing measurable at 30 ms) | |
| co-location, whitelisted hold | **never tested** (London hold test pending) | table 6 gives the payoff per measured hold |
| post-only as a fast taker | proven closed | crossing post-only is rejected (50 ms) |
| other order types (FOK, marketable GTC/GTD) | proven closed | all held (+165-176 ms) or rejected (GTD expiry) |
| batch endpoint | never tested | docs: orders evaluated independently |
| **short-lived inside quote + guard** | **won on selection and held out** (+38.5 [+8, +71] paired) | maker fill model not validated live for pairs; L <= 150 ms |

## 6. If whitelisting shortens the hold (`fill/arms.py hold`, held out, `hold-held.csv`)

The hold here is **decision to match**. A venue delay D from London gives about D + 15-20 ms. The
leaders' implied total is ~180 ms; ours today is the live pool (p50 330 ms).

Under each fill model:
- `corr` keeps today's adverse selection, so it is a floor.
- `bn` lets matches that beat the Binance trigger survive. It is optimistic by about $47/day at
  today's hold (+38 vs -9), so read it as a ceiling, or shift it down by that amount.
- `none` is the visible book alone.

| rule | hold | corr | bn | none | sel (bn) |
|---|---|---|---|---|---|
| **current rule** (v1 3c, i = 0) | live pool | -9.0 [-39, +19] | +38.4 [+3, +74] | +67.3 [+18, +117] | -11.7 |
| | 150 ms | -3.9 [-39, +28] | +95.9 [+49, +145] | +155.8 [+93, +218] | +20.0 |
| | 100 ms | -4.5 [-46, +35] | +174.2 [+108, +239] | +263.8 [+175, +347] | +48.9 |
| | 50 ms | +12.5 [-33, +56] | +271.7 [+181, +358] | +344.5 [+235, +448] | +191.9 |
| **gap pick** (v1 5c, limit + 3 c, stop 120 s) | live pool | +7.4 [-7, +22] | +6.9 [-8, +20] | +28.9 [-2, +59] | -3.3 |
| | 150 ms | +8.1 [-11, +24] | +21.4 [-4, +47] | +78.8 [+38, +122] | +3.1 |
| | 100 ms | +28.3 [+15, +43] | +50.0 [+24, +76] | +137.1 [+92, +183] | +37.6 |
| | 50 ms | +14.7 [-8, +34] | +80.1 [+53, +109] | +142.5 [+94, +191] | +75.4 |
| **v1 >= 6 c** | live pool | +8.4 [+2, +17] | +5.1 [-8, +17] | +36.2 [+14, +63] | +1.2 |
| | 150 ms | -6.4 [-21, +3] | +18.7 [-6, +45] | +70.0 [+37, +106] | +10.7 |
| | 100 ms | -2.1 [-18, +11] | +37.8 [+10, +68] | +105.9 [+67, +149] | +25.8 |
| | 50 ms | -1.0 [-19, +14] | +60.8 [+27, +95] | +127.1 [+84, +172] | +54.0 |

- **At 150 ms the taker rule needs the timing to pay off.** Under `corr` nothing changes (-3.9).
  Under `bn` the current rule gains **+104.9 [+61, +153]** paired, and +$49/day after the bn
  offset.
- **Action rule once the London hold is measured:**
  - **Decision-to-match <= ~150 ms with a fill rate well above today's 7%:** run the current rule
    taker (bn row). Its leg-1 fill rate rises from 5% to 14% (bn) at 150 ms.
  - **Otherwise:** run the resting-leg-1 pick (section 4), which does not depend on the hold.
- **Leg 2:** both routes keep the taker leg 2. Live it completes 0.79 and is helped by a shorter
  hold.

## Novel contributions

- **Endogenous hold, measured per order.**
  - Claim: on Polymarket the time from a marketable order to its match is not independent of the
    book path. Even with no feed stall, the venue answers 75-175 ms after the ask leaves, at
    every lead from 0.2 to 1.5 s.
  - What it beats: independent-hold models, which overstate fills 4x (0.29 vs 0.073), and every
    race model (10 variants), which leaves fills' markout at +2 to +6 c vs +0.2 live.
  - Falsifiable: on the London whitelisted path, the fill rate by lead must stay below the
    independent draw.
- **Predictable vs survivable decomposition.** Under a speed bump, the share of predictable moves
  that can still be bought is 1%, and the survivable subset has a negative move. This is a
  general test for whether any latency signal can beat a taker delay.
- **The speed bump used from the maker side for pairs.** A 0.5 s inside quote with a guard
  gains +38.5 [+8, +71] $/day paired, held out, over the taker rule. Beats: the taker rule and
  the unguarded 2 s join of `pairs-live-gap`. Falsifiable: live, its leg-1 fills' 5 s markout
  must not be worse than the engine's, and pe must stay above the taker rule's.
- **Publication:** an empirical note on Polymarket's taker delay (endogeneity, leaders' timing,
  the predictable-vs-survivable bound). Speed bumps protecting makers are known (IEX, Aquis); the
  delta is the order-level endogeneity and its consequence for latency signals.

## Caveats

- **Maker fill model:** queue position, rival haircut, insert/cancel latency from the Dublin
  probe. It has never been validated for pairs; the live inside hour had 0 real vs 1 inferred
  fill.
- **Multiple rounds:** route rounds 1-4 tested 59 arms, picked on selection (+11.7 [-6, +28]
  alone). Held out is the honest number but shrinks with the search.
- **Fill models for earlier signals:** `bn` reproduces the live fill rate but only two thirds of
  the adverse selection. No model validated for v1 transfers cleanly to other timings, so the
  hold table is a band, not a forecast.
- **Clocks and samples:**
  - Leaders' timing compares venue ms, Binance E and our wall clock as UTC.
  - The quiet hold pool comes from one 5 h window (458 orders).
  - The Chainlink test uses one 6 h window of 10-11 (Paris recorder).
- **Fixed-hold arms assume** the venue still answers after the ask has left in the same way.
  Only a live test at the new hold settles which column applies.

## Reproduce

```
PYTHONPATH=. python3 -m research.beathold.hold.acks && PYTHONPATH=. python3 -m research.beathold.hold.endo
ls data/trade/dublin-pairs-20261014live/bot-*.jsonl* | xargs -P 6 -n 1 research/beathold/hold/split_bn.sh
for m in binance book fills signals report; do PYTHONPATH=. python3 -m research.beathold.leaders.$m; done
PYTHONPATH=. python3 -m research.beathold.lead.chainlink
PYTHONPATH=. python3 -m research.beathold.lead.rows --set dublin --workers 4   # ~20 min, 7.4 M rows
PYTHONPATH=. python3 -m research.beathold.lead.rows --set dry --workers 4
PYTHONPATH=. python3 -m research.beathold.lead.train --refit && PYTHONPATH=. python3 -m research.beathold.lead.diag
for a in hold lead lead_hold route route2 route3 route4; do for s in "dublin held" "dry all" "dublin sel"; do set -- $s
  PYTHONPATH=. python3 -m research.beathold.fill.run --arms $a --set $1 --part $2 --workers 6; done
  for p in held sel; do PYTHONPATH=. python3 -m research.beathold.fill.table $a $p; done; done
```
