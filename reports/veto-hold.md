# Taker + model veto under the measured venue hold

Data: the veto arm's own 9,890 would-be orders from the 48 h Dublin paper run
(`data/paper/dublin-20261012`, 575 markets, gap-free, settled), replayed on the venue-clock book
(research grid, 5 ms rows, venue stamps). Each order matches at decision + h, with h drawn per order
from the 195 live FAK orders of 2026-10-13 (decision to ack - 14 ms: p10 234, p50 276, p90 574 ms).
60 sh unless stated, 10 s mid markout after the 0.07 p (1 - p) fee at our 0% tier, market-bootstrap
CIs. Selection hours = 2026-10-12, test hours = 2026-10-13 (never used to choose anything).
Code `research/vetohold/`, outputs `data/out/vetohold/*.md`. Read-only, no orders.

## Verdict

**Most of the +$5,006/day paper markout never existed, and the hold removes the rest at +2 c.**
- **Paper to live-like:** the paper bot's log +$5,006/day (+9.6 c/$) -> the same orders on the venue
  clock at the same 150 ms hold +$1,208 (+3.4 c/$) -> the measured hold, live limit seen + 2 c
  **+$81/day [-299, +463]** (+0.3 c/$, fill 31%). The hold-and-feed path removes **98%** of the paper
  edge; **76%** goes before the extra hold, because the paper bot filled against depth its lagging
  feed had not yet seen removed (34% of veto orders were decided on a stale ask).
- **At i = 0 (limit = seen ask, the binding live rule) the arm stays positive:** +$467/day
  [+205, +716], +4.6 c/$ [+2.0, +7.1], fill 13%, 26.6 fills/h. Every larger fixed offset is worse;
  from i = 4 c the CI is below 0.
- **Why:** makers pull 91% of the targeted depth inside the hold (9% is traded away); fills are
  adversely selected (hold-free markout +3.1 c/$ on what fills vs +16.4 on what misses); and the
  **veto selects exactly the signals whose depth gets pulled** (survival at i = 0 falls from 20% for
  vetoed rows to 8% for v1 >= 5 c) while value-if-filled rises from -0.8 to +18.9 c/sh.
- **A predicted offset cannot buy the fills back:** the needed offset i* grows **1.9 c per 1 c of
  model edge**; edge - i* is negative in every edge quintile (-2.5 to -4.3 c). Limit = seen + predicted
  i* lost to plain i = 0 by **-$683/day [-1,113, -307]** on test hours.
- **What works:** a hold-aware gate on top of v1 (`v1h_G_h250x_L0`, pre-registered winner): on test
  hours at i = 0 **+$864/day [+505, +1,272]** vs frozen v1 +$628 [+247, +1,056], paired gain
  **+$236/day [+84, +393]** (+$122 after dropping the top 5 markets). Exported for the Rust bot.

## 1. The veto arm through the measured hold (all 48 h, real hold, 60 sh)

| limit | fill | px - seen c | mk10 c/$ | res c/$ | $/order | $/day |
|---|---|---|---|---|---|---|
| **seen + 0 (i = 0)** | 0.13 | -0.8 | **+4.6 [+2.0, +7.1]** | +5.9 [-4.3, +16.1] | +0.09 | **+467 [+205, +716]** |
| seen + 1 | 0.21 | -0.0 | +2.2 [+0.3, +4.1] | +5.6 [-5.1, +16.4] | +0.08 | +379 [+48, +695] |
| seen + 2 (as built) | 0.31 | +0.6 | +0.3 [-1.1, +1.7] | +3.7 [-5.4, +13.2] | +0.02 | +81 [-299, +463] |
| seen + 3 | 0.41 | +1.3 | -0.8 [-2.0, +0.4] | +2.5 [-5.8, +10.7] | -0.06 | -298 [-780, +151] |
| seen + 4 | 0.52 | +1.8 | -1.4 [-2.4, -0.4] | +1.9 [-5.1, +9.1] | -0.15 | -721 [-1,249, -197] |
| seen + 5 | 0.60 | +2.3 | -2.2 [-3.1, -1.3] | +1.1 [-5.2, +7.4] | -0.29 | -1,416 [-2,020, -833] |
| seen + 6 | 0.67 | +2.7 | -2.5 [-3.3, -1.7] | -0.0 [-5.9, +5.8] | -0.37 | -1,851 [-2,525, -1,234] |
| seen + 7 | 0.74 | +3.1 | -2.8 [-3.6, -2.1] | +0.1 [-5.3, +5.8] | -0.48 | -2,351 [-3,078, -1,691] |
| seen + 8 | 0.78 | +3.4 | -3.1 [-3.9, -2.3] | -0.1 [-5.2, +5.2] | -0.56 | -2,778 [-3,532, -2,084] |
| seen + 9 | 0.82 | +3.7 | -3.3 [-4.1, -2.5] | -0.4 [-5.2, +4.7] | -0.64 | -3,161 [-3,946, -2,436] |
| seen + 10 | 0.84 | +4.0 | -3.3 [-4.1, -2.5] | -0.3 [-5.0, +4.6] | -0.67 | -3,323 [-4,145, -2,561] |
| value price (seen + edge + fee) | 0.46 | +1.6 | -1.2 [-2.3, -0.1] | +2.2 [-5.1, +9.7] | -0.11 | -553 [-1,074, -59] |
| value price - 1 c | 0.35 | +1.0 | -0.2 [-1.6, +1.0] | +2.5 [-5.7, +10.9] | -0.02 | -79 [-508, +338] |
| value price - 2 c | 0.23 | +0.3 | +1.5 [-0.2, +3.2] | +3.8 [-5.4, +12.4] | +0.06 | +307 [-47, +647] |
| value price - 3 c | 0.14 | -0.4 | +4.3 [+2.1, +6.5] | +7.5 [-1.7, +16.5] | +0.11 | +547 [+272, +821] |
| fair_p (settlement fair) | 0.05 | -1.2 | +7.1 [+3.7, +10.4] | +8.1 [-2.2, +18.3] | +0.08 | +400 [+199, +598] |

- **Share of the paper edge removed:** 98% at the as-built +2 c, 91% at i = 0. Against micf (the
  paper's +$1,520 [+927, +2,161] paired gain) the veto under the hold is -$262 [-647, +123] at +2 c
  and +$64 [-208, +335] at i = 0.
- **Per hold (seen + 2 c):** 150 ms +$1,208, p10 (234 ms) +$494, p50 (276 ms) +$227, p90 (574 ms)
  -$557; no hold (3 ms) +$6,655. **At i = 0:** 150 ms +$1,122, p10 +$716, p25 +$682, p50 +$602,
  p75 +$548 (all CIs above 0), p90 (574 ms) +$81 [-169, +322]; no hold +$5,220. The slow-hold tail
  costs most of the gap between p50 and the drawn hold.
- **Why +2 c was the default:** `rules.vtaker(slip=0.02)` copied the leaders' observed 1-3 c of limit
  room (reports/strategy-search.md, rebuilt rule); it was never tuned for the veto. On the venue-clock
  150 ms replay +1 / +2 c were best (+$1,230 / +$1,208); under the measured hold the optimum is
  i = 0, on selection and on test hours (test: i = 0 +$682, i = 1 +$660, i = 2 +$337, i = 5 -$1,175).
  "Buy at our predicted price" (value price) only matches i = 0 when shaded by 3 c.
- **Size:** at i = 0, +5.6 c/$ at 5 sh (+$56/day), +4.6 c/$ at 60 sh; c/$ barely depends on size.

## 2. Why it fails (real hold, seen + 2 c unless stated)

- **(a) Depth pulled, not taken:** median depth at <= seen + 2 c is 215 sh at decision (venue clock)
  and 0 at the match; 41% of the targeted shares survive, 33% of orders still have 60 sh; **91%** of
  the removed depth is cancelled or requoted, 9% traded.
- **(b) Adverse selection:** hold-free markout (buy at seen, mark at match + 10 s) is **+3.1 c/$ on the
  orders that fill vs +16.4 c/$ on those that miss**. The fills are the signals that did not move.
- **(c) Drift and a stale feed:** the side-frame ask at the match sits a median **+4.2 c** (mean
  +5.5) above the seen ask. 34% of veto orders were decided when the venue ask already differed from
  ours: they produced $1,833 of the paper's $5,006/day and -$24/day at i = 0 under the hold
  (fresh-feed orders: +$491/day [+238, +737]).
- **(d) The veto picks pulled depth.** All 1.07 M trigger rows of the 48 h, at i = 0
  (`data/out/vetohold/vetosel.md`):

| trigger rows | share | survive at i = 0 | value c/sh | value if filled c/sh | feed lag ms |
|---|---|---|---|---|---|
| vetoed: v1 prefers other side | 6% | 73% | -1.10 | -1.5 | 103 |
| vetoed: v1 < 0 | 70% | 20% | -0.16 | -0.8 | 30 |
| vetoed: 0 <= v1 < 2 c | 18% | 13% | +0.06 | +0.5 | 17 |
| kept: 2-3 c | 3% | 9% | +0.22 | +2.3 | 15 |
| kept: 3-5 c | 2% | 8% | +0.54 | +6.6 | 15 |
| kept: >= 5 c | 1% | 8% | +1.51 | +18.9 | 16 |

  Makers and the model see the same Binance move: the stronger the model's case, the less depth
  survives (veto by edge quintile: survival 46% -> 33%, ask drift p50 3.7 -> 6.6 c). The product
  still rises with the edge, so the veto ranks correctly; it just fills ~9% of what it picks.

## 3. Needed offset i* and the predicted-limit policy

- **Distribution (median hold, first ask with depth minus seen):** p10 0, p25 2, **p50 4**, p75 7,
  p90 12 c; 13% need <= 0, 31% <= 2 c, 62% <= 5 c, 86% <= 10 c, 1% none within +30 c. For the full
  60 sh: p50 5, p90 14 c.
- **What it moves with (Spearman):** depth within +5 c (-0.41), fair-value edge (+0.37), the
  opposite side's model value (-0.37), depth within +2 c (-0.34), perp move over 0.5 / 1 s (+0.28 /
  +0.27), model edge (+0.22).
- **Predictor (pre-registered, fit on selection, scored on test):** MAE 2.76 c vs 3.91 for the
  selection median, R^2 0.50, Spearman 0.64. Permutation importance on test: fair-value edge, depth
  within +5 c, opposite-side value, secs left, 30 s perp volatility, perp 1 s move. Partial
  dependence: i* +4.6 c at a 3 c fair edge vs -0.9 c at <= 0; -1.3 c at 3.7 k sh depth vs +1.9 c at
  300 sh. Recent observed hold length is not a feature (the replay draws holds independently).
- **The key question, answered:** no. By model edge quintile, mean edge 2.1 -> 4.4 c while i* 4.6 ->
  8.7 c; **edge - i* = -2.5, -2.5, -2.6, -2.9, -4.3 c**; realized PnL bought at seen + i* is negative on
  average in every quintile. i* rises 1.86 c per 1 c of edge and only 0.20 c per 1 c of realized move:
  makers reprice by the move the model predicts, so the edge left after paying i* stays below 0.
- **Policy result (test hours):** limit = seen + ceil(î), send iff edge - î >= 1 c (chosen on
  selection): sends 6.7% of orders, -$1/day vs plain i = 0 +$682: **-$683 [-1,113, -307]**.

## 4. Fixes in the taker + veto family (frozen 15:32 UTC before scoring; test hours, i = 0)

| rule (params from selection) | sent | mk10 c/$ | $/day | gain vs plain i = 0 |
|---|---|---|---|---|
| plain veto, i = 0 | 100% | +5.6 [+2.1, +9.4] | +682 [+253, +1,132] | |
| (i) survival veto: P(fill) x E[value given fill] >= 0 | 57% | +10.8 [+6.8, +15.4] | +778 [+469, +1,140] | +96 [-175, +382] |
| (ii) predicted i* limit | 7% | -0.0 [-6.0, +6.4] | -1 [-215, +217] | -683 [-1,113, -307] |
| (iii) size = 50% of predicted surviving depth | 100% | +5.3 [+0.8, +10.4] | +238 [+36, +459] | -445 [-777, -143] |
| (iv-a) fresh feed only (lag <= 20 ms) | 66% | +9.0 [+4.6, +13.9] | +737 [+375, +1,162] | +55 [-168, +284] |
| (iv-b) direct EV regression >= -2 c/$ | 83% | +8.7 [+5.0, +12.9] | +810 [+441, +1,216] | +128 [-64, +328] |
| (i) + (iii) | 57% | +10.7 [+5.1, +16.9] | +263 [+123, +428] | -420 [-813, -38] |
| best fixed i on selection (i = 0) | 100% | +5.6 | +682 | 0 |

Filters (i), (iv-a), (iv-b) double the c/$ but drop as many dollars as they save: none beats plain
i = 0 with a CI above 0.

## 5. The veto model retrained for the hold (i = 0)

**Label:** what a 60 sh FAK at limit = seen earns per intended share when it matches at t + h on
the venue-clock book: 10 s value if depth at <= seen survives (partial fills pro rata), 0 otherwise.
h = 16 equal-mass quantiles of the live hold (`real`), or fixed 250 / 300 ms. Rows = all 1.07 M
trigger rows that pass the gates (473 k selection rows, 286 markets), v1's 98 oriented features;
`+x` adds 7 book-survival features on the receipt clock (depth at seen / +2 / +5 c, its change over
0.25 / 1 s, level age, mean feed lag of the last 50 book messages). Variants: A = one regressor on the
label, B = P(survive) x E[value | filled], S = stacked on v1's value (rows v1 >= 0), G = gate on rows
v1 already keeps (>= 2 c). Margin per variant and the winner (best out-of-fold selection $/day) were
fixed before scoring. Round 1 (A, B) lost to v1 on selection; round 2 (S, G) was added after that,
still before any test row was scored (`data/out/vetohold/model-prereg{,-round1}.json`).

Test hours (289 markets), replay with own-take memory, real hold, i = 0, 60 sh
(`data/out/vetohold/model-score.md`):

| model | orders/h | fills/h | mk10 c/$ | $/day | gain vs v1 |
|---|---|---|---|---|---|
| v1 frozen (2 c) | 228 | 32.3 | +5.2 [+2.0, +8.8] | +628 [+247, +1,056] | |
| v1, margin re-chosen (2.5 c) | 149 | 19.8 | +9.4 [+4.9, +14.4] | +703 [+359, +1,104] | +75 [-112, +248] |
| **G_h250+x (winner)** | 200 | 26.0 | **+8.5 [+5.0, +12.6]** | **+864 [+505, +1,272]** | **+236 [+84, +393]** |
| G_real+x | 201 | 26.3 | +7.9 [+4.5, +11.6] | +808 [+459, +1,204] | +179 [+20, +338] |
| S_h250+x | 182 | 50.2 | +2.4 [+0.9, +4.0] | +643 [+231, +1,075] | +14 [-368, +388] |
| S_real+x | 72 | 25.3 | +4.1 [+1.9, +6.6] | +573 [+266, +903] | -55 [-431, +308] |
| S_real | 519 | 93.2 | +0.7 [-0.4, +2.0] | +338 [-220, +929] | -291 [-768, +177] |
| A_h250 | 5 | 3.4 | +2.9 [-6.1, +10.6] | +68 [-117, +256] | -560 [-1,040, -108] |
| A_real+x | 12 | 7.1 | +1.3 [-4.4, +6.6] | +56 [-183, +289] | -572 [-1,066, -122] |
| B_real | 0.3 | 0.2 | -3.1 | -8 | -636 [-1,071, -250] |

- **Robustness:** at the median hold (276 ms) the winner gains +$179 [+30, +327]; at 150 ms +$74
  [-97, +244]; it beats v1 in 16 of 25 test hours; dropping the top 5 markets leaves +$122/day.
- **Why the direct labels fail:** the i = 0 label is mostly 0 (fills ~10-20%), so a model trained from
  scratch on 24 h learns where depth survives, which is where nothing happens. Keeping v1's 10 s value
  as the ranking and learning only "will this one survive and pay" on rows v1 keeps works.
- **Export (for the Rust bot):** `data/out/predict/models/v1h_G_h250x_L0.{pkl,trees.json}`, pkl
  sha256 `c485164f043a647b844ccafa79fdda93e645eedffdf01eeb991dbb6743201242`, trees.json sha256
  `6761315ea71372322df0eb3e798612baa0d31151478a8cd8cfd0469d94b9c16e`. Rule: trigger fires and gates
  pass, v1 trigger-side value >= 2 c and >= the other side, gate prediction >= -0.005, 0.2 s
  refractory, limit = seen. Inputs: v1's 98 trigger-side features, `v1_value`, and the 7 `x_*` book
  features exactly as in `research/vetohold/label/extras.py` (Up-token book, receipt clock); the bot
  must compute these before it can load this model. The meta field `hold` reads "h250+x": the label
  hold is a fixed 250 ms.

## 6. Classification (improvement-discipline table)

| idea | class | premises / what reopens it |
|---|---|---|
| wider fixed limit (i = 1..10) | lost a comparison (to i = 0) | 60 sh, measured hold; reopens only if the hold shortens (at 150 ms +1 / +2 c were best) |
| limit = seen + predicted i* | lost a comparison, -$683 [-1,113, -307] | i* grows ~1.9 c per c of edge; reopens if a feature predicts i* independently of the edge |
| value-price limit (seen + edge + fee - j) | lost a comparison (pv3 ~ i = 0, pv0 -$553) | same mechanism as i* |
| (i) hold-survival veto | lost a comparison, tie (+$96 [-175, +382]) | 24 h selection; reopen with more hours |
| (iii) size to surviving depth | lost a comparison (-$445) | c/$ does not depend on size at i = 0 |
| (iv-a) fresh-feed gate, (iv-b) EV regression | lost a comparison, ties (+$55, +$128) | reopen with more hours |
| retrained veto, direct label (A, B) | lost a comparison (-$560 to -$636) | sparse label on 24 h; reopen with weeks of labels |
| stacked retrain (S) | lost a comparison, tie | |
| **v1 + hold-aware gate (G)** | **won, pre-registered, +$236 [+84, +393]** | one test day; confirm on new hours |
| none of the above is proven closed | | |

## Caveats

- **One test day** (289 markets), one afternoon's hold sample (195 orders); the test day was better
  than selection for every arm (plain i = 0: +$682 vs +$254/day).
- **Hold:** decision to ack - 14 ms over all 195 live orders, heavier-tailed than the fills' tape match
  (send + 246 ms median, p90 351 ms); the fixed 250 ms label is the closer match for fills.
- **Our order changes nothing** in the replay (no maker reaction to it); own takes are remembered 3 s;
  the venue book is level-aggregated.
- **Live size is 5 sh;** 60 sh tables scale linearly in c/$ at i = 0 (+5.6 c/$ at 5 sh).
- **The paper bot's fill engine** reads its own lagging feed and overstates fills; future paper
  numbers need the venue-clock replay (`research/vetohold/replay`).

## Reproduce

```
PYTHONPATH=. nice -n 10 python3 -m research.vetohold.replay.run --workers 3        # rows.pkl (~35 min local)
PYTHONPATH=. python3 -m research.vetohold.tables.headline
PYTHONPATH=. python3 -m research.vetohold.tables.decompose
PYTHONPATH=. python3 -m research.vetohold.tables.istar
PYTHONPATH=. python3 -m research.vetohold.fixes.prereg && PYTHONPATH=. python3 -m research.vetohold.fixes.score
PYTHONPATH=. python3 -m research.vetohold.fixes.accuracy
# AWS m6a.8xlarge, OMP_NUM_THREADS=1 per worker:
PYTHONPATH=. python3 -m research.vetohold.label.build --workers 30                 # ~4 min
PYTHONPATH=. python3 -m research.vetohold.label.train                              # ~8 min
PYTHONPATH=. python3 -m research.vetohold.label.score --workers 30                 # ~6 min
PYTHONPATH=. python3 -m research.vetohold.tables.vetosel
```
