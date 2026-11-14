# Order-book prediction: trading ahead of the 150 ms hold

Date 2026-10-11. Code `research/predict/`, outputs `data/out/predict/` (tables `tables.md`,
curves `curve*.md`, `post_curve.md`, freeze record `freeze.json`). Read-only research: no
orders, no keys, no spending. Leaders: A = 0xc53375ff94e96100f2b30a4b5775db35218d69a9,
B = 0x3048d65321be3497164cdfc2996f94f98a2e7537. All money at **our 0% rebate tier**, 150 ms
taker hold, the strategy replay simulator unchanged (`research/strategy/sim/`).

## Verdict

**A more accurate and earlier signal exists, but only its conservative form survived every
fresh hour.** The Binance perp's next tick is close to deterministic from the top of book
(direction AUC 0.99 out to 1 s), so "which side" is solved; the money is whether the
Polymarket book is still behind *after* our order matches (AUC 0.69 at L = 0, 0.71 at -40).
A side-oriented GBDT that predicts that residual value fires before the leaders' trigger in
43% of its orders and, used conservatively, beats micf on 21 h of hours no model or selection
saw.

- **Pre-registered primary (aggressive taker, 3 s model, 2 c margin): failed.** Frozen test
  run 1 (83 markets, 08:00-15:00), L = 0: +6.7 c/$ markout, +$3,233/day vs micf +$896, but
  paired gain CI [-3,486, +8,054]. The extension (48 later, busier markets, 15:00-19:00) turned
  it negative: -1.6 c/$, -$1,269/day. All 251 unseen markets (dev3 + test3, 21 h): +5.7 c/$,
  +$2,850/day, gain over micf +$1,850 [-1,345, +5,417]. Fat tails, and it over-fires when
  activity jumps (3,186 fills/day in the busy hours vs 1,572).
- **What survived (conservative taker, 1 s model, 3 c margin):** on all 251 unseen markets,
  L = 0: **+15.9 c/$ markout, +$1,850/day, gain over micf +$849/day [-22, +1,926]**
  (P <= 0 = 0.03); L = -40: **+$1,360 [+391, +2,431]**. Positive in the busy extension too
  (+7.7 c/$ at L = 0).
- **Model as a veto on their trigger:** L = -40 gain over micf **+$875/day [+426, +1,304]** on
  all unseen hours, **+$884 [+105, +1,665]** on the frozen test hours alone; at L = 0 +$287
  [-119, +654].
- **Decay:** exploitable post-match AUC 0.710 / 0.685 / 0.664 at L = -40 / 0 / 50 (leaders'
  rule 0.631 / 0.608 / 0.583); every 50 ms of latency costs ~0.02 AUC.
- **Resolution PnL is noise over hours:** every directional arm lost at settlement in test
  run 1 (micf -0.3 c/$, leader A -5.6) and won in the extension; read the 10 s markout.
- **Leaders' actual fills, test hours:** A 0.0 / +0.7 c/$, B -0.5 / -0.3 c/$ markout (run 1 /
  extension); the surviving predictive arms beat both per $ in every window.
- **Inference:** 3.6 us per decision (200 trees in C), 5 us per Binance message for the
  feature state; not the bottleneck.
- **Not helping:** perp raw trades (dev3) and depth behind the touch (26 ms diff depth, 3 h
  side recording) add <= 0.002 AUC.
- **Go-live status:** not proven. Paper-run the conservative taker and the trigger veto from
  Dublin for >= 48 h (see Going live); the aggressive primary is retired.

## Freeze log

| when (UTC) | what |
|---|---|
| 2026-10-11 14:10 | splits fixed in `research/predict/__init__.py`: train = run 2 markets before 10-10 10:00, select = run 2 after, dev3 = run 3 before 10-11 08:00, test3 = run 3 from 08:00 |
| 14:30-15:30 | models trained on train only; arms and model variants chosen on select (sel1, then a labelled second look sel2); dev3 used as a transfer check, no choice changed after it |
| **15:31:56** | **freeze** (`data/out/predict/freeze.json`): primary arm, criterion, arm list, model hashes |
| 15:45 | test3 hours converted (blind), simulated once: `final`, `final_comp`, leaders' fills |
| 19:05-19:30 | extension: the same frozen arms on the 48 later test3 markets (15:00-19:00), `ext`; depth study on the side recording |
| after the freeze | maker baseline, tail-cap round (select hours), depth study: diagnostics, none changes a frozen arm |

Primary criterion (pre-registered): at L = 0, 10 s markout c/$ > 0 **and** paired 10 s
markout gain over micf with the 95% market-bootstrap CI above 0.

## 1. Horizon decay curves

Train run 2 first 12 h, scored on run 2 last 12 h (`curve.md`, `curve_tight.md`). Decision
rows = every perp / spot bookTicker update and Polymarket top change, thinned to <= 1 per 20 ms
unless a trigger-sized event happened. Direction AUC is on rows where the target moved;
timing AUC = will it move at all within h.

**Binance perp mid, 1-tick spread rows, full-tick moves** (no mechanical spread refills):

| h ms | P(move) | timing AUC | direction AUC: GBDT | linear | OFI (CKS) | imbalance (G-B) | leaders' rule |
|---|---|---|---|---|---|---|---|
| 50 | 0.023 | 0.965 | 0.999 | 0.997 | 0.992 | 0.984 | 0.975 |
| 100 | 0.030 | 0.954 | 0.997 | 0.995 | 0.986 | 0.982 | 0.962 |
| 150 | 0.035 | 0.942 | 0.996 | 0.993 | 0.982 | 0.979 | 0.951 |
| 200 | 0.039 | 0.934 | 0.994 | 0.991 | 0.978 | 0.978 | 0.942 |
| 300 | 0.047 | 0.921 | 0.992 | 0.988 | 0.972 | 0.974 | 0.925 |
| 500 | 0.059 | 0.895 | 0.986 | 0.980 | 0.959 | 0.967 | 0.895 |
| 1000 | 0.083 | 0.852 | 0.972 | 0.965 | 0.930 | 0.953 | 0.837 |

Spot (same definition) is the same shape: direction 0.999 -> 0.991, timing 0.959 -> 0.872.
On all rows (spread refills included) perp direction is 0.988 -> 0.967 and timing 0.984 ->
0.892. **Direction barely decays; timing does**, and only 2-8% of instants see a tick at all.

**Polymarket 5m venue mid, move >= 1 c vs our view at t:**

| h ms | P(move) | timing AUC | direction AUC: GBDT | linear | OFI | imbalance | leaders' rule |
|---|---|---|---|---|---|---|---|
| 50 | 0.163 | 0.868 | 0.885 | 0.800 | 0.802 | 0.667 | 0.726 |
| 100 | 0.210 | 0.851 | 0.886 | 0.803 | 0.807 | 0.664 | 0.742 |
| 150 | 0.254 | 0.842 | 0.885 | 0.805 | 0.809 | 0.663 | 0.753 |
| 200 | 0.287 | 0.831 | 0.878 | 0.797 | 0.801 | 0.654 | 0.747 |
| 300 | 0.338 | 0.813 | 0.862 | 0.776 | 0.781 | 0.640 | 0.732 |
| 500 | 0.415 | 0.786 | 0.830 | 0.745 | 0.744 | 0.617 | 0.704 |
| 1000 | 0.540 | 0.749 | 0.772 | 0.705 | 0.692 | 0.593 | 0.662 |

**The part a held taker can still capture** (`post_curve.md`): the venue mid move from the
match time (t + L + 150 ms) over the next window, predicted at t.

| match offset ms (L) | window | P(>= 1 c) | GBDT AUC | leaders' rule AUC | top-10% accuracy |
|---|---|---|---|---|---|
| 110 (-40) | 1 s | 0.41 | 0.710 | 0.631 | 0.89 |
| 150 (0) | 1 s | 0.41 | 0.685 | 0.608 | 0.83 |
| 200 (50) | 1 s | 0.41 | 0.664 | 0.583 | 0.80 |
| 150 (0) | 3 s | 0.63 | 0.648 | 0.560 | 0.74 |
| 150 (0) | 10 s | 0.81 | 0.638 | 0.538 | 0.72 |

Every 50 ms of extra latency costs ~0.02-0.025 AUC on the exploitable move; the leaders'
rule loses its edge twice as fast (0.63 -> 0.58).

## 2. Why the obvious signal loses (perp imbalance, "lost a comparison")

Decomposition per share at L = 0, gated rows (`diag_imb_*`), select hours (train hours agree):

| rule | book move 10 s c | half spread c | hold slippage c | fee c | net 10 s c/$ |
|---|---|---|---|---|---|
| perp imbalance 0.8-0.95 | 1.50 | 0.65 | 0.59 | 1.17 | -1.5 |
| perp imbalance > 0.95 | 4.33 | 0.82 | 2.06 | 1.18 | +0.4 |
| imbalance > 0.8, no recent microprice move | 1.36 | 0.66 | 0.29 | 1.16 | -1.2 |
| leaders' trigger (microprice 0.1 s >= 0.002 bp) | 7.82 | 0.88 | 4.49 | 1.21 | +2.1 |

The imbalance does predict a 1.5-4.3 c book move (the strategy agent's 2-2.6 c), but **half
of it lands inside the 150 ms hold** (slippage 0.6-2.1 c) and the rest is eaten by the half
spread and the 0.07 p (1 - p) fee. It lost because the move is front-loaded, not because it
is wrong. Fix: predict the value left *after* the match instead of the move, which is what
the value model does; imbalance becomes one input among ~100.

## 3. The model

- **Target:** per-share value of buying a side at the best venue ask at t + L + 150 ms,
  marked at the venue mid k s later, after the taker fee (`model/derive.py`). k = 3 won
  (k = 1 close; **k = 10 lost held out**, -0.4 c/$: the 10 s mark is too noisy to train on).
- **Side-oriented rows:** one row per decision and side, every directional feature signed
  toward that side, so one model serves Up and Down with twice the data (`model/orient.py`).
- **Features (98, receipt clock):** perp and spot top of book (imbalance, microprice offset and
  changes over 25 ms-1 s, spread), Cont-Kukanov-Stoikov OFI decayed at 25/100/400/1600 ms,
  queue depletion and time-to-depletion per side (Cont-de Larrard), decayed intensities of mid
  ticks (Hawkes-style), spot trade flow, perp-spot basis, the Polymarket view (price, spread,
  staleness = perp microprice move since our view last changed, recent repricing), the
  strategy fair value (pzm), and Binance moves converted to Polymarket cents through the
  settlement delta.
- **Learner:** sklearn HistGradientBoosting, 200 trees x 15 leaves, min 200 rows per leaf,
  trained on rows where something is happening (trigger, extreme queue, stale book or fair
  edge within 2 c). Larger trees (31 leaves x 400) and coarser leaves (1000) both lost on
  select.
- **What it reads** (grouped permutation importance, select hours, `importance.md`): the
  spot book (-3.2 c/sh on the top 2% when shuffled), the Polymarket state (-2.8), the fair
  value (-1.6); each perp group alone < 0.6 because they are redundant with each other.
- **Earlier than the leaders:** 43% of its firing rows had **no** leaders' trigger toward the
  side yet; those earned +3.9 c/sh at the best level, the trigger-aligned ones +10.4.

## 4. Trading results

Arms: **predictive taker** (buy the side with predicted value >= 2 c, 60 sh, limit = seen
ask + 2 c, >= 0.2 s between orders), **predictive veto** (their trigger or micf, kept only
when the model agrees), **predictive maker** (fair +/- 3 c quotes, a side pulled when the
model predicts the opposite side gains >= -3 c). Baselines: micf, their rule rebuilt, the
strategy's maker, leaders' actual fills. Full tables `data/out/predict/tables.md`.

**Frozen test, run 3, 83 markets (2026-10-11 08:00-15:00 UTC):**

| arm | L ms | fills/day | net $/day [CI] | net c/$ | 10 s mk c/$ | 10 s mk $/day | max DD $ |
|---|---|---|---|---|---|---|---|
| **predictive taker (primary)** | -40 | 2,634 | -4,406 [-29,603, +12,765] | -5.7 | +3.9 | +3,026 | 3,597 |
| predictive veto on their trigger | -40 | 857 | +2,497 [-325, +5,125] | +12.8 | +13.4 | +2,612 | 172 |
| micf | -40 | 555 | -21 [-2,416, +2,331] | -0.1 | +7.8 | +1,402 | 221 |
| their rule, rebuilt | -40 | 2,700 | -305 [-8,635, +6,504] | -0.4 | +2.1 | +1,693 | 1,338 |
| **predictive taker (primary)** | **0** | 1,572 | -4,393 [-26,023, +11,018] | -9.1 | **+6.7** | **+3,233** | 3,429 |
| predictive taker, 1 s model, margin 3 c | 0 | 468 | +498 [-4,955, +5,846] | +4.0 | +13.6 | +1,716 | 741 |
| predictive veto on their trigger | 0 | 201 | +741 [-796, +2,378] | +17.1 | +24.1 | +1,043 | 140 |
| predictive maker | 0 | 1,544 | -458 [-3,396, +2,291] | -3.5 | +2.9 | +369 | 237 |
| micf | 0 | 392 | -35 [-2,109, +2,063] | -0.3 | +6.6 | +896 | 177 |
| their rule, rebuilt | 0 | 2,092 | -946 [-8,371, +5,572] | -1.4 | +0.6 | +403 | 1,188 |
| strategy maker | 0 | 2,037 | -910 [-3,798, +1,835] | -4.5 | -3.9 | -792 | n/a |
| leader A actual | actual | 3,262 | -2,275 [-6,523, +1,387] | -5.6 | 0.0 | 0 | 1,053 |
| leader B actual | actual | 6,985 | +180 [-3,954, +4,444] | +0.3 | -0.5 | -335 | 707 |
| **predictive taker (primary)** | 50 | 1,298 | -5,979 [-28,202, +9,304] | -14.0 | +4.3 | +1,816 | 3,596 |
| micf | 50 | 350 | -267 [-2,357, +1,893] | -2.2 | +5.5 | +671 | 220 |

**Paired 10 s markout gain over micf** (market bootstrap):

| arm | L | test3 (83 mkts) | dev3 + test3 pooled (203 mkts) |
|---|---|---|---|
| predictive taker (primary) | -40 | +1,623 [-4,864, +7,599] | +2,474 [-1,840, +7,089] |
| predictive taker (primary) | 0 | +2,338 [-3,486, +8,054] | +2,676 [-1,152, +6,923] |
| predictive taker (primary) | 50 | +1,145 [-4,188, +6,812] | +1,920 [-1,680, +5,922] |
| predictive veto on their trigger | -40 | **+1,210 [+686, +1,735]** | **+1,007 [+685, +1,320]** |
| predictive veto on their trigger | 0 | +147 [-485, +700] | +239 [-82, +513] |
| predictive taker, 1 s model, margin 3 c | -40 | +1,121 [-1,448, +3,952] | +1,318 [+119, +2,548] |

**Competition sensitivity** (50 ms race window, half of each level, L = 0): primary +3.6 c/$
markout, +$1,338/day; micf +4.4 c/$, +$453/day; gain +$885 [-3,336, +4,550]
(`final_comp`). The primary leans on depth that rivals may take first.

**Across windows, L = 0, 10 s markout c/$ and $/day:**

| arm | select (run 2, selection) | dev3 (unseen, 10 h) | test3 (frozen, 7 h) |
|---|---|---|---|
| predictive taker (primary) | +4.3 / +3,435 | +10.8 / +4,232 | +6.7 / +3,233 |
| predictive veto on their trigger | +21.0 / +1,496 | +17.1 / +1,626 | +24.1 / +1,043 |
| predictive maker | +5.9 / +933 | +6.5 / +768 | +2.9 / +369 |
| micf | +3.5 / +816 | +8.7 / +1,323 | +6.6 / +896 |
| their rule, rebuilt | -0.8 / -725 | +1.6 / +936 | +0.6 / +403 |
| strategy maker | +1.7 / +394 | +4.6 / +791 | -3.9 / -792 |

The primary earned 2.6-4.2x micf's markout dollars in these three windows, then lost in the busy extension (section 5). **Why the CI is wide:**
its per-market markout is fat-tailed (top 5 markets > 100% of the total on dev3 and test3,
bottom 5 about -$760). Capping it (orders per market 5-40, per burst window) on select hours
lowered the dollars faster than the variance (`sel3`): cap 5-10 drops the markout to ~0, a
burst cap of 2 per 5 s lifts the t-stat 3.2 -> 3.9 but halves the dollars. **The tails are
the edge** (bursts where Polymarket lags for seconds), not noise to trim.

## 5. Extension of the frozen test (pre-registered in `freeze.json`)

The same frozen arms on the 48 test3 markets after run 1 (15:00-19:00 UTC, `ext`). These hours
were much busier: their rule fires 17,886 times a day (2,092 in run 1).

| arm | L | ext 10 s mk c/$ | ext mk $/day | gain vs micf (ext) | all unseen, 251 mkts: mk c/$ | gain vs micf, all unseen |
|---|---|---|---|---|---|---|
| predictive taker (primary, 3 s, 2 c) | 0 | -1.6 | -1,269 | -1,644 [-5,996, +2,287] | +5.7 | +1,850 [-1,345, +5,417] |
| predictive taker (1 s, 3 c) | 0 | +7.7 | +1,450 | +1,075 [-622, +2,705] | +15.9 | **+849 [-22, +1,926]** |
| predictive veto on their trigger | 0 | +3.5 | +866 | +491 [-1,258, +2,075] | +12.0 | +287 [-119, +654] |
| predictive taker (primary) | -40 | -0.7 | -1,227 | -1,987 [-9,939, +4,089] | +3.4 | +1,621 [-2,128, +5,614] |
| predictive taker (1 s, 3 c) | -40 | +2.6 | +2,301 | +1,542 [-346, +3,514] | +7.5 | **+1,360 [+391, +2,431]** |
| predictive veto on their trigger | -40 | +1.0 | +1,081 | +321 [-1,583, +2,065] | +5.8 | **+875 [+426, +1,304]** |
| micf | 0 | +1.3 | +375 | | | |
| their rule, rebuilt | 0 | -2.6 | -13,471 | | | |
| leader A / B actual | actual | +0.7 / -0.3 | +471 / -317 | | | |

By hour (L = 0, test3 run 1 + ext) the primary lost in the busiest hour (15:00, -11 c/$ on
112 fills) where the 1 s / 3 c taker made +13.8. **Why the primary failed** (diagnosis, not
re-tested): its 2 c margin is calibrated on quiet weekend hours; when activity jumps its
predicted values inflate with the volatility inputs, it doubles its fire rate, and the extra
fills land where rivals clear the depth first (its markout already halved under the 50 ms
competition sensitivity). A 3 c margin and the less smoothed 1 s target are the robust
setting. Classified **lost a comparison** (to its own conservative sibling), reopenable with
a volatility-scaled margin selected on a busy select window.

## 6. Depth behind the touch (side recorder, post-freeze diagnostic)

Binance offers USD-M diff depth at **@depth@0ms (~26 ms batches, ~37 msgs/s)**, @100ms and
partial depth5/10/20 at >= 100 ms; spot's fastest diff depth is 100 ms (spot @0ms sends
nothing); bookTicker is real time (~98 msgs/s perp). Probed 2026-10-11. A side recorder
(`research/predict/ingest/depth_rec.py`, separate process and directory, run 3 untouched)
captured perp @depth@0ms + bookTicker 15:31-18:31 UTC; the book was rebuilt from absolute
level sizes (`depth/parse.py`, 394k updates). Adding log queue at the 2nd level, 2-5 and 2-10
ticks behind the touch and their imbalances (train first 2 h, test last 1 h, `depth_study.md`):

| features | perp timing AUC 150 ms | 300 ms | post-match AUC (L = 0, 1 s) |
|---|---|---|---|
| top of book only | 0.893 | 0.859 | 0.637 |
| + depth behind the touch | 0.892 | 0.859 | 0.626 |

**No gain.** The perp touch holds ~4 BTC and the next levels a few hundredths, so the next
tick is decided at the touch. Premises: 3 h, 10 levels, 26 ms batches; reopen only with a
faster depth feed or a much busier day.

## 7. Inference latency (`inference.md`)

| step | cost per decision |
|---|---|
| incremental feature state per Binance message (pure Python: 4 decayed OFIs, depletion, intensity, 1 s microprice ring) | 5.3 us |
| 200-tree model compiled to C, per row (gcc -O2, batched) | 3.6 us |
| same through ctypes, one call | 21.6 us (17 us is ctypes overhead) |
| sklearn `predict` on one row (research path) | 31,000 us |

The C scorer reproduces sklearn to 0.000 max error. A production bot needs C/Rust feature
state plus the C trees: **well under 50 us** end to end, against 26 ms batches of the fastest
Binance depth stream and ~100 ms of network.

## 8. Literature and fidelity audit

| family (verified citation) | predicts | horizon, accuracy | fidelity to what moves this market |
|---|---|---|---|
| Queue imbalance: Gould & Bonart 2016, MML 2(2), doi 10.1142/s2382626616500064 | sign of the next mid change | event time; large-tick +50-60% over null | **holds here, extreme:** perp direction AUC 0.98 from imbalance alone; silent on when |
| Lipton, Pesavento, Sotiropoulos 2013, arXiv 1312.0514 | next mid change and wait time | event time | the only timing result; matches our timing AUC falling with h |
| OFI: Cont, Kukanov, Stoikov 2014, JFE 12(1), doi 10.1093/jjfinec/nbt003; multi-level Xu, Gould, Howison 2019 | contemporaneous price change | 10 s bins, R2 65% | contemporaneous, not predictive; as a decayed feature 0.98 -> 0.93 |
| Micro-price: Stoikov 2018, QF 18(12), doi 10.1080/14697688.2018.1489139 | martingale fair price | a few ticks | it is the leaders' trigger; Polymarket makers already react to it within the hold |
| Hawkes: Bacry, Mastromatteo, Muzy 2015, MML 1(1); Morariu-Patrichi & Pakkanen 2022, QF | event arrival clustering | intensity fits, no forecast scores | used as decayed intensities; adds little (< 0.4 c/sh importance) |
| Queue depletion: Cont & de Larrard 2013, SIFIN 4(1); Huang, Lehalle, Rosenbaum 2015, JASA 110 | time to the next price change | generative | time-to-depletion features carry the timing signal (0.4 c/sh) |
| Deep LOB: Zhang, Zohren, Roberts 2019, IEEE TSP 67(11); Briola, Bartolucci, Aste 2024, arXiv 2403.09267; Kolm, Turiel, Westray 2023, Math. Finance | next k-event mid direction | 61-85%, decays with k; large-tick easier; "accuracy is not actionable" | needs depth; event-time labels; Briola's warning is exactly our section 2 |
| Crypto lead-lag: Alexander & Heck 2020, JFS; Aleti & Mizrach 2021, JFM | venue price discovery | minutes to 1 s | too coarse; we see perp leading spot by 50-100 ms and the 5m book by 100-300 ms |
| Latency races: Budish, Cramton, Shim 2015, QJE 130(4); Aquilina, Budish, O'Neill 2022, QJE 137(1) | value of stale-quote races | 5-10 us races, ~0.5 tick each | Polymarket races last 100s of ms because of the hold |
| Asymmetric delays: Baldauf & Mollner 2020, JF 75(3); Chen et al. 2016 (SSRN 2860359); Brolley & Cimon 2020, JFQA | who wins under a taker-only delay | theory and lab | predict makers win; nobody models a taker that forecasts through the delay |

**Shared omission (the gap we built from).** Every family scores the *source* book: the
next Binance tick in event time. None models the *follower* (a slow, 1-cent book whose makers
reprice off the source with a lag) and none labels outcomes in wall-clock time relative to a
fixed delay. Our data says the source problem is nearly solved (direction 0.99) and therefore
worthless on its own: the money is the follower's residual staleness after the hold, a
different target with AUC 0.69 at L = 0. Inverting the default (predict the follower's
post-delay value, not the source's next move) is the invention.

## 9. Ideas tested and their status

| idea | status | evidence / premises |
|---|---|---|
| perp queue imbalance as a taker signal | **lost a comparison**, fixed by re-targeting | move real (1.5-4.3 c) but 50% lands in the hold; as a value-model input it pays |
| direction-only Binance forecaster | **lost a comparison** | direction AUC 0.99 yet the leaders' rule fills still lose without a value filter (their rule -0.8 to +1.6 c/$ markout) |
| value model trained on the 10 s mark | **lost a comparison** | -0.4 c/$ markout on select vs +4.3 for the 3 s target; reopen with more data or a denoised mark |
| bigger trees (31 x 400) / coarse leaves (1000) | **lost a comparison** | +0.6 c/$ ($826/day) and +6.4 c/$ ($2,797/day) vs the winner's +4.3 c/$ ($3,435/day) on select |
| exposure caps on the winner | **lost a comparison** | caps remove the burst fills that carry the edge |
| perp raw-trade flow (run 3 only) | **lost a comparison** (no increment) | dev3 6 h -> 4 h: timing / direction / post-match AUC change <= 0.002; reopen on a busy day |
| deeper book (diff depth @0ms) | **lost a comparison** (no increment) | 3 h side recording: timing 0.893 -> 0.892, post-match 0.637 -> 0.626 |
| aggressive predictive taker (3 s target, 2 c margin) | **lost a comparison** to its 1 s / 3 c sibling | positive in quiet hours, -1.6 c/$ in the busy extension; reopen with a volatility-scaled margin |
| predictive maker | **open, positive** | markout > 0 in 3 of 3 windows at L = 0, beats the strategy maker in point estimate; not significant |
| Bybit / OKX confirmation | **never tested here** | not in run 3; hidden-trigger study found +0.02 AUC on 3.5 h |

## 10. Novel Contributions

| claim | what it beats | falsifiable test |
|---|---|---|
| **Follower-residual target:** under an asymmetric taker delay, predict the follower's value left after the match (venue mid k s after t + L + 150 ms minus the post-hold ask and fee), not the source's next move | micf (value-filtered leaders' trigger) on 251 markets no model or selection saw: conservative implementation (1 s target, 3 c margin) +$849/day of markout at L = 0 [-22, +1,926], +$1,360 [+391, +2,431] at L = -40; their rule and the leaders' actual fills by 8-16 c/$ markout | a >= 48 h paper run and the rest of run 3: gain over micf with CI above 0 at L = 0; fails if it crosses 0 |
| **Direction is solved, timing is the frontier:** at a 1-tick spread the perp's next full tick is called with AUC 0.99 (0.98 from imbalance alone) out to 1 s, while timing decays 0.965 -> 0.852 and the exploitable follower move decays ~0.02 AUC per 50 ms | the literature's event-time direction scores (Gould-Bonart, DeepLOB), which on this market are near-ceiling and not actionable | same curves on run 3 and on a high-volatility day: direction >= 0.97 at every h <= 1 s, timing monotone decreasing |
| **Hold-front-loading explains why imbalance loses:** the imbalance-predicted move lands ~50% inside the 150 ms hold | the strategy agent's imbalance taker (-5 to -7 c/$) | slippage share >= 40% of the move for imbalance > 0.8 rows on any new window |
| **Model as a veto on a known trigger is the cheapest significant gain:** +$875/day over micf at L = -40 [+426, +1,304] on all unseen hours, +$884 [+105, +1,665] on the frozen test hours | micf at the split Tokyo latency | the remaining run-3 hours keep the CI above 0 at L = -40 |

**Honest publication assessment.** The empirical core (a decay map of what is predictable at
which delay, and the follower-residual target) is a clean workshop-level contribution for
market-microstructure or ML-for-finance venues; the asymmetric-delay angle is under-studied
(no paper found on takers forecasting through a delay). It is not yet a paper: 11 h of frozen
test on one weekend, the pre-registered primary failed in busy hours while its conservative sibling held
(P = 0.03 at L = 0 on 21 unseen hours, not pre-registered as primary), and a simulator rather
than fills. Needs the conservative arm pre-registered as primary on >= 48 h of new hours, a busy
weekday, and a paper run that matches the simulator's fill rate.

## 11. Caveats

- **Sample:** test3 is 11 h of a Sunday (7 quiet + 4 busy); dev3 10 h overnight. Resolution PnL swings +/- 15 c/$
  with the window; read the 10 s markout.
- **Competition:** the primary needs depth that survives 10 ms after its match; at a 50 ms
  window and half of each level its markout halves (+3.6 c/$). Taking depth from rivals would
  change their behaviour; not modelled.
- **Selection:** ~65 arms (x 3 latencies) were scored on the select hours (two labelled
  looks); the frozen test is the guard, and the winner's markout did not regress there (+4.3
  select, +6.7 test).
- **Clock:** L is from our Paris receipt (Binance + ~112 ms); L = 0 is a Dublin host, L = -40
  the split Tokyo build. The L = -40 rows read the Paris Polymarket view, a few tens of ms of
  look-ahead on that view only.
- **Best-level analyses** (sections 2, 3) ignore depth and rivals; the simulator does not.
- **Makers:** counterfactual fills from recorded taker flow; latent takers attracted by our
  quotes are not modelled.

## 12. Going live (paper first)

1. **Paper bot on the surviving arms:** run `vt_v1_m0.03_any` (1 s model, 3 c margin) and the
   trigger veto `vt_v1_m0.02_trigger` in paper mode from the Dublin host (L ~ 0) for >= 48 h: log every would-be order, the venue book at
   t + L + 150 ms, and compare realized would-be fills and prices to the simulator for the
   same hours (target: fill rate and price within 25%).
2. **Port the hot path:** feature state and the C tree scorer into the bot process (Rust or C
   extension), keep the Binance connection fan-out (3-4 parallel sockets) from
   `reports/infra-plan.md`; budget < 50 us per decision.
3. **Retrain weekly** on the latest 24 h (train) + 12 h (select), same frozen selection rule;
   track the post-match AUC curve as the health metric.
4. **Real orders only with explicit approval**, starting at 60 shares, after the paper run
   meets step 1 and the pooled frozen-test CI over micf is above 0.

## Reproduce

```
nice -n 10 python3 -m research.strategy.ingest.run --workers 2      # hours -> npz (shared cache)
nice -n 10 python3 -m research.predict.ingest.perp_trades           # run-3 perp trades
nice -n 10 python3 -m research.strategy.eval.prep --micro            # strategy v2 tables (baselines)
nice -n 10 python3 -m research.predict.feats.run --seg train,select,dev3,test3
nice -n 10 python3 -m research.predict.model.curve [--tight --tag _tight]
nice -n 10 python3 -m research.predict.model.post_curve
nice -n 10 python3 -m research.predict.model.diag_imb --seg select
nice -n 10 python3 -m research.predict.model.train --name v1 --k 1 --leaf 200
nice -n 10 python3 -m research.predict.model.train --name v3p --k 3 --leaf 200 --prefilter
nice -n 10 python3 -m research.predict.sim.run --arms sel1 --tag sel1 --seg select
nice -n 10 python3 -m research.predict.sim.run --arms final --tag final --seg test3
python3 -m research.predict.sim.leaders --seg test3
python3 -m research.predict.sim.score --tag final --leaders test3
python3 -m research.predict.infer.bench && python3 -m research.predict.report.tables
```

## Improvement round 2026-10-12

Five invented candidates were scored on the allowed data, 395 markets with max start 1791744600, under two-fold window CV. Full tables are in `data/out/predict/improve/summary.md`. **None survived adversarial verification, so no prereg3.json was written.** The sealed prereg2 segment is judged with the frozen arms only, as registered.

- **C1 conviction-keyed size:**
  - Pooled result: taker `ek_pred_2000` +531 [+306, +767] $/day vs `vt_any`; veto `vk_vstar_3000` +1,117 [+701, +1,593] vs the frozen veto (CV:all, L0).
  - Fold A, the most recent hours: +158 [-135, +457] for the taker and +15 under comp. Dropping the top 5 markets turns it negative.
  - The constants were designed on screens covering every evaluate window, so the result counts as never tested out of sample.
  - Lead for the next registration.
- **C2 settlement-delta floor:** the veto `dmv_f3` gives +68 [+6, +161], but 63% of that comes from one market and it is -1 after dropping the top 5. The taker missed its own busy-hour PASS.
- **C3 two-side coherence:** lost a comparison. The identity holds on the match book, not on the seen book (the hold widens the spread by 1-3 c).
- **C4 race clock:** the cap/tighten direction is proven closed under three premises: free FAK rest, walked shares with positive markout, and no impact. The size/walk direction ties race-free twins.
- **C5 busy-inclusive refit:** lost a comparison. All 22 variants lose to v1, even in-sample (best-level target misaligned with fill markout).

## Pre-registered test 2 (`prereg2.json`), sealed segment, 2026-10-12 22:45 UTC

**Both registered arms PASS.** The test covers the 324 run-3 5m markets starting 2026-10-11 18:55 to
2026-10-12 21:50 UTC (start >= 1791744900; 27 h, no gaps; the 21:55 market is excluded because
its book runs into the hour the recorder cut at 22:03). The run is the arms of `final.py` unchanged
(`arms/prereg2.py` asserts identity) and model hashes equal to the registration, simulated once.
The improvement round had no survivors, so no prereg3 was frozen, and this segment was opened only
after that (commit a38b76d).

| arm | L | 10 s mk c/$ | 10 s mk $/day | gain vs micf, 10 s mk $/day [95% CI] | resolution $/day [CI] | fills/day | max dd $ | verdict |
|---|---|---|---|---|---|---|---|---|
| taker `vt_v1_m0.03_any` | 0 | **+5.7** | +849 | **+848 [+281, +1,411]** | +838 [-1,102, +2,888] | 860 | 692 | **PASS** |
| veto `vt_v1_m0.02_trigger` | -40 | +1.1 | +1,398 | **+928 [+5, +1,806]** | +1,428 [-3,665, +7,003] | 6,227 | 2,182 | **PASS** |
| taker | -40 | +2.2 | +1,874 | +1,403 [+380, +2,393] | +1,012 [-4,793, +7,556] | 5,191 | 2,799 | |
| veto | 0 | +2.3 | +659 | +657 [+82, +1,200] | +1,715 [-1,026, +4,889] | 1,656 | 1,328 | |
| taker / veto | 50 | +5.2 / +9.9 | +133 / +279 | +260 [-292, +776] / +406 [-80, +872] | +8 / +65 | 130 / 164 | | |
| micf | 0 | 0.0 | +1 | | +1,029 | 965 | 790 | |
| their rule, rebuilt | 0 | -2.8 | -15,703 | -15,704 | -22,145 | 19,170 | 28,764 | |
| leader A / B actual | actual | -0.1 / +0.1 | -193 / +195 | | -1,114 / +819 | 9,220 / 18,422 | | |

**Pooled with the 251 earlier unseen markets (575 markets, labelled pooled):** taker L = 0 +9.5 c/$,
gain vs micf +849 [+333, +1,441]; veto L = -40 +905 [+345, +1,440]; taker L = -40 +1,384 [+637, +2,140].

Read it plainly. The predictive edge over the leaders' own trigger holds on 27 hours no model,
threshold or selection saw: about +$850/day of 10 s markout at L = 0 in the simulator. Three caveats
stand. Resolution PnL is not significant for any arm (CIs span 0), and at L = -40 micf out-earned the
taker on resolution (+1,657 vs +1,012). The veto's lower bound is +$5/day, a bare pass. Fills come
from the replay simulator at our 0% fee tier; the 50 ms competition model was not rerun here. At
L = 50 neither gain is significant, so the edge depends on reaching the book within the leaders' window.

Files: `data/out/predict/prereg2/{score,pooled}.md`, `{agg,fills,markets,score,paired}-prereg2*`,
`*-pooled_pre2*`. Reproduce:
```
nice -n 10 python3 -m research.predict.sim.run --arms prereg2 --tag prereg2 --seg test3 --exclude seen_pre2
python3 -m research.predict.sim.leaders --seg test3 && python3 -m research.predict.sim.score --tag prereg2 --leaders test3
python3 -m research.predict.sim.pool --tags dev1,final,ext,prereg2 --arms prereg2 --out pooled_pre2
python3 -m research.predict.sim.score --tag pooled_pre2
```

## Taker hold 270 ms vs 150 ms, taker vs maker (2026-10-13)

Live FAK orders ack in ~270 ms (p50) against 56 ms for a resting insert, so the venue holds takers
longer than the 150 ms the simulator assumed. Every prereg2 arm and every maker arm (strategy maker,
26 distinct value makers) was rerun on all 575 unseen markets (dev3 + test3) at `--hold 0.15` and
`0.27`; the 0.15 rows reproduce the pooled prereg2 numbers (taker L = 0 +9.52 c/$). Fill rate =
simulated fills / decisions (takers). 10 s markout with a 95% market bootstrap CI.

**The longer hold halves the taker; the makers do not notice it:**

| arm | L | hold | fill rate | 10 s mk c/$ [CI] | 10 s mk $/day [CI] |
|---|---|---|---|---|---|
| taker `vt_v1_m0.03_any` | 0 | 0.15 | 34% | +9.5 [+6.2, +13.2] | +1,286 [+831, +1,780] |
| taker `vt_v1_m0.03_any` | 0 | 0.27 | 24% | +6.6 [+2.3, +11.1] | +670 [+241, +1,146] |
| taker | -40 | 0.15 / 0.27 | 66% / 40% | +3.5 / -0.2 [-1.8, +1.3] | +2,318 / -105 |
| veto `vt_v1_m0.02_trigger` | -40 | 0.15 / 0.27 | 66% / 41% | +2.1 / -0.7 [-1.5, +0.1] | +1,838 / -451 |
| micf | 0 | 0.15 / 0.27 | 36% / 30% | +1.8 / +0.5 [-1.2, +2.1] | +437 / +96 |
| maker `vm_fair0.03_p-0.03` (frozen pick) | 50 | 0.15 / 0.27 | | +5.1 [+0.5, +9.8] (0.27) | +328 [+29, +635] |
| maker `vm_v1_fair0.04_p-0.02` | 50 | 0.27 | | +3.0 [+0.6, +5.4] | +479 [+103, +847] |
| maker `vm_v1_fair0.03_p-0.02` | 50 | 0.27 | | +2.3 [+0.4, +4.1] | +522 [+94, +927] |
| maker `vm_v1_fair0.04_p-0.02` | 100 / 150 | 0.27 | | +0.8 [-1.5, +3.1] / -0.7 | +123 / -104 |
| strategy maker | 50 | 0.27 | | -2.8 [-5.3, -0.4] | -461 |

Read it plainly. At 0.27 s the primary taker keeps a positive simulated markout at L = 0 (+6.6 c/$,
CI above 0) and loses it at L = -40, where it fired most. Live it filled 14% of 155 sent orders
(sim 24%) at -4.1 c/$ [-13, +8], and the orders that missed live would have earned +16.8 c/$ on the
paper engine while the 36 that filled lost -5.2: **the simulator does not reproduce the live adverse
selection.** The live sample is small and cap-filtered (40 orders/h, $15 exposure), so it does not
reject +6.6 on markout, but the fill-rate gap (expected ~37 fills, got 22) is real. Something the
replay cannot see takes the depth our correct signals target: rivals reacting to the same Binance
move inside the hold, which the recorded book shows only as the outcome of their reaction, not as
a race against our order.

The makers barely change with the hold (their fills come from trades through the quote and queue,
not from held crossing orders) but they decay with **cancel latency**: at L = 50 eight value makers
keep a markout CI above 0; at L = 100 only `vm_v3p_fair0.04_p-0.04` does (+0.03 lower bound); at 150
none. Live cancels ack in ~45 ms p50 and 113-149 ms p90, so the maker edge lives inside the cancel
p50 and the tail eats it. Caveats: 26 makers were compared on the same hours (best-of selection; the
frozen pick `vm_fair0.03_p-0.03` is the clean read, CI [+0.5, +9.8] c/$); makers quote 60 shares with
300 open, not our 5-share caps; maker fills are inferred counterfactually and the taker inference
was optimistic live. Verdict: the taker route is closed until a live fill test agrees with the
sim; the maker route is the open one, conditional on cancels under ~50 ms and a live maker test.

Files: `data/out/predict/hold/{summary,tail}.{md,csv}`. Reproduce:
```
for s in dev3 test3; do for h in 150 270; do
  nice -n 10 python3 -m research.predict.sim.run --arms hold --tag hold${h}_$s --seg $s --hold 0.$h; done
  nice -n 10 python3 -m research.predict.sim.run --arms holdtail --tag holdtail_$s --seg $s --hold 0.27 --L 100,150; done
for h in 150 270 tail; do python3 -m research.predict.sim.pool --tags hold${h}_dev3,hold${h}_test3 --arms hold$([ $h = tail ] && echo tail) --out hold$h; done
python3 -m research.predict.sim.holdcmp --tags hold150,hold270 --out data/out/predict/hold/summary.md
python3 -m research.predict.sim.holdcmp --tags holdtail --out data/out/predict/hold/tail.md
```
