# Competition and fill realism of the deployed arms (post-freeze diagnostic)

Date 2026-10-12 (round 2). Code `research/predict/improve/diag/competition/`. Detail tables:
`diag-competition-tables.md` (round 1: exposure, splits, race curve, fill models, size rules),
`diag-competition-extra.md` (jitter, losing fills, markout by predicted value),
`diag-competition-sizesel.md`, `diag-competition-vlim.md`, `diag-competition-race-label.md`,
`diag-competition-cadence.md` (+ CSVs). Allowed windows only: select 144, dev3 120, test3 run 1
83, ext 48 markets; every entry point asserts max(start) < 1791744900 and the store cannot open
an hour at or after it. The instrumented simulator reproduces the frozen fills exactly (every
order, shares and 10 s markout, all four windows, `sim/check.py`); the race-label refit
reproduces the frozen v1_L0 predictions to 0.0 (same rows, same learner). Quiet = dev3 + test3
run 1 (203 markets), busy = ext (48), unseen = both (251). Money = 10 s markout at our 0% tier,
95% market-bootstrap CIs (our draw: the frozen 1 s taker gain reads +$849 [-51, +1,879]).

## Verdict

**Rivals do not make the losing fills lose; they take a share of the winning ones.** Hold
slippage is at most 12% of the losing fills' loss and the loss builds 1-10 s after the match. The
harshest fill model (comp) removes 34-46% of the winners' dollars but only 10-25% of the losers',
so realism shrinks the edge without changing its sign. **The one competition-robust improvement
is to size by predicted value**: it beats the deployed 60 sh under all three fill models on
unseen hours for every deployed arm, is flat in busy hours at L = 0 and slightly negative (CIs
across 0) in busy hours at L = -40. Chasing depth with a looser
limit, a race-aware label and shrinking size all lost a comparison.

- **Edge-keyed size, 1 s taker, L = 0** (shares = 2000 x predicted value, 30-200): vs deployed
  +$448 [+160, +773] base, +$389 [+127, +695] e+25, +$132 [+2, +269] comp; vs micf **+$1,297
  [+266, +2,430]** base (frozen: +$849 [-51, +1,879]).
- **Edge-keyed size, veto, L = 0** (3000 x value, 100-300): vs deployed +$801 [+427, +1,258] /
  +$671 / +$220 [+7, +452]; vs micf **+$444 [+12, +843] under comp** (frozen +$224 [-99, +511]).
- **Latency jitter is harmless, a late bias is not:** +/-25 ms of symmetric jitter keeps 99-104%
  of the unseen L = 0 dollars; a uniform 0-50 ms late bias keeps 85-87% (busy 1 s taker: 54%).
- **The rivals that clear our depth are makers:** 85-95% of the hold-time depth drop at our
  levels is cancels; the leaders are 0-12% of the same-side prints in our hold.

## 1. Inside the 150 ms hold (L = 0, base fills, round 1)

| | micf quiet / busy | 1 s taker quiet / busy | veto quiet / busy |
|---|---|---|---|
| orders filled | 38% / 43% | 40% / 41% | 33% / 44% |
| same-side rival print in our hold: filled / unfilled orders | 52 / 78% ; 58 / 85% | 43 / 63% ; 38 / 62% | 30 / 67% ; 33 / 57% |
| leaders' share of those prints (test3) | 4% / 3% | 0% / 4% | 7% / 12% |
| traded share of the hold-time depth drop (filled) | 23% / 29% | 13% / 5% | 6% / 7% |
| our filled shares a rival print took <= 50 ms after our match | 9% / 5% | 12% / 18% | 15% / 14% |
| 10 s markout c/$ | +7.9 / +1.3 | +19.6 / +7.7 | +18.7 / +3.5 |

## 2. Losing fills: the hold is not where the money goes (`losers.py`)

| regime, arm | losers / fills | loss $ | hold slip share of loss | loser markout 1 / 3 / 10 s, c/sh | rival in hold: losers / winners | comp keeps: losers / winners |
|---|---|---|---|---|---|---|
| quiet, 1 s taker | 92 / 312 | -537 | -6% | -1.7 / -3.9 / -11.9 | 59% / 37% | 79% / 62% |
| quiet, veto | 74 / 251 | -172 | +8% | +0.8 / +0.7 / -4.6 | 41% / 25% | 80% / 66% |
| quiet, micf | 101 / 293 | -350 | +9% | -2.5 / -2.7 / -6.5 | 69% / 43% | 89% / 66% |
| busy, 1 s taker | 76 / 158 | -225 | +6% | -1.2 / -4.0 / -5.7 | 37% / 39% | 90% / 56% |
| busy, veto | 124 / 238 | -336 | +12% | -0.5 / -1.0 / -5.3 | 35% / 32% | 79% / 64% |
| busy, veto L = -40 | 437 / 859 | -1,284 | +12% | -0.8 / -1.6 / -6.0 | 29% / 32% | 75% / 54% |

Losers are reversals after the match, as the loss-anatomy diagnostic found from the other
side: the veto's quiet-hour losers were still winning at 1 and 3 s. A rival print inside our hold
flags a loser in quiet hours (crowded fills earn less), not in busy ones, and it is only visible
after the order is sent. **Competition is adverse selection on the winners:** the comp model
keeps 54-66% of winners' dollars and 75-90% of losers'; at e+25 in busy hours the 1 s taker keeps
79% of winners and 95% of losers.

## 3. Race curve and latency jitter (`jitter.py`)

Race curve, 10 s markout $/day at a fixed match shift e (round 1): the 1 s taker keeps 90% of
its quiet-hour dollars 25 ms late, but loses 44% of its busy-hour dollars 10 ms late (72% of
that loss is five orders on big stale quotes). Mixtures over e (trapezoid weights on the
simulated grid), L = 0, $/day [gain vs micf under the same mixture]:

| arm, window | base (e = 0) | e ~ U(-25, +25) | e ~ U(0, +25) | e ~ U(0, +50) |
|---|---|---|---|---|
| 1 s taker, unseen | +1,850 [+849] | +1,841 [+842] | +1,667 [+784] | +1,574 [+754] |
| veto, unseen | +1,288 [+287] | +1,342 [+344] | +1,176 [+293] | +1,121 [+301] |
| 1 s taker, busy | +1,450 [+1,075] | +1,325 [+1,018] | +929 [+626] | +790 [+537] |
| veto L = -40, unseen | +2,406 [+875] | +2,348 [+829] | +1,965 [+661] | +1,654 [+504 (+42, +889)] |
| veto L = -40, busy | +1,081 [+321] | +925 [+193] | +358 [-124] | -117 [-520] |

The race curve is convex near e = 0 (earlier gains more than later loses), so unbiased jitter
costs nothing. **What the Dublin paper run must measure is the mean receipt-to-CLOB offset,
not its spread.** At L = 0 the gain over micf barely moves with a late bias because micf loses
as much.

## 4. Size by predicted value (`sizesel.py`, selected on select, read on unseen)

Realized markout rises with the predicted value (unseen, base, c/sh): 1 s taker 5.8 / 9.9 / 8.0 /
11.2 / 15.5 for predictions 3-4 / 4-5 / 5-7 / 7-10 / 10+ c; veto 2.5 / 5.8 / 9.6 / 20.0 / 12.0 /
22.1 from < 3 c up. The comp model keeps that order. The high-value orders sit on the thinnest,
most contested stale quotes (37-44 sh filled of 60; 35-45% taken by a rival <= 50 ms later in
the 7-10 c bin), so a bigger order there takes depth a rival would have taken.

Rule pooled from 12 fixed / value-keyed sizes: the size with the largest comp-gain CI lower bound
on select (the competition guard). Paired vs the same arm at 60 sh, same fill model, $/day:

| arm | rule | window | base | e+25 | comp | vs micf, comp |
|---|---|---|---|---|---|---|
| 1 s taker, L = 0 | 2000 x value, 30-200 sh | unseen | **+448 [+160, +773]** | **+389 [+127, +695]** | **+132 [+2, +269]** | +538 [-86, +1,150] |
| | | busy | +147 [-123, +484] | +79 [-144, +338] | +45 [-151, +264] | +292 [-1,090, +1,504] |
| veto, L = 0 | 3000 x value, 100-300 sh | unseen | **+801 [+427, +1,258]** | **+671 [+329, +1,078]** | **+220 [+7, +452]** | **+444 [+12, +843]** |
| | | busy | +144 [-581, +858] | +4 [-817, +772] | -58 [-707, +605] | +103 [-1,682, +1,763] |
| veto, L = -40 | 3000 x value, 60-300 sh | unseen | **+1,472 [+870, +2,156]** | **+987 [+471, +1,576]** | **+424 [+92, +755]** | **+725 [+41, +1,352]** |
| | | busy | -158 [-1,521, +1,246] | -315 [-1,674, +1,071] | -347 [-1,526, +785] | -1,548 [-4,330, +883] |

The same arms at 60 sh vs micf under comp: 1 s taker +$406 [-149, +982], veto L = 0 +$224
[-99, +511], veto L = -40 +$302 [-131, +682]. The alternative selection (largest e+25 gain with
the comp CI above 0 on select) picks 300 sh flat for the veto, which loses $1,034/day under comp in
busy hours; the value-keyed rule is the safe form. **Selection caveat:** this rule was written
after the size tables had been printed, so the unseen read is a diagnostic, not a blind test.

## 5. Chasing depth: value-capped limit (`vlim.py`)

limit = seen + clip(predicted value - floor, lo, 10 c) instead of seen + 2 c (take the depth
rivals left while it still pays). Picked on select: floor 0, never tighter than + 2 c, with the
value-keyed size. Net of the size rule (paired vs 3000 x value at + 2 c), $/day:

| arm | select comp | unseen base / e+25 / comp | busy base / e+25 / comp |
|---|---|---|---|
| 1 s taker, L = 0 | +621 [+57, +1,404] | +319 [-120, +736] / +153 / +109 [-278, +464] | +260 / +67 / -240 |
| veto, L = 0 | +543 [+99, +1,140] | +231 [-89, +497] / +153 / +87 [-224, +322] | -126 / -96 / -137 |
| veto, L = -40 | +707 [+188, +1,356] | +351 [-223, +973] / +253 / -182 | **-1,837 [-3,145, -593] / -1,908 / -3,246 [-4,399, -2,170]** |

A tighter limit when the value is small (floor 2 c, lo 0) went the other way in the busy hours
at L = -40 (+$692 [-89, +1,601] comp) but no select window is busy, so it cannot be chosen yet.
**Take more at the levels you saw; do not chase levels rivals repriced.**

## 6. Race-aware value label (`race/label.py`, hypothesis 1 of round 1)

Same rows, features and learner as the frozen v1_L0; target = min (rmin) or mean (ravg) of the
1 s value at L = 0 and L = 50. Same margin as the frozen sibling (label effect only), unseen, vs
frozen sibling, $/day:

| arm | base | e+25 | comp | busy, e+25 |
|---|---|---|---|---|
| ravg, 3 c, any | -335 [-1,146, +596] | -159 [-951, +766] | -5 [-691, +782] | -474 [-1,204, +157] |
| rmin, 3 c, any | -1,340 [-2,074, -712] | -1,082 [-1,723, -549] | -720 [-1,263, -298] | -963 [-1,761, -268] |
| ravg, 2 c, trigger | -180 [-381, +17] | -143 [-352, +54] | -61 [-239, +97] | -94 [-1,014, +716] |
| rmin, 2 c, trigger | -613 [-908, -346] | -516 [-800, -261] | -300 [-526, -91] | -673 [-1,813, +324] |

The select pick (ravg at 2 c, `any`: +$669 [+163, +1,247] over the frozen arm under e+25 on
select) won through its lower margin and lost on unseen (-$113 [-1,219, +1,020]; busy -$641).
The label penalizes exactly the contested rows that carry the edge (section 2), so it trades
winners for safety; the gap closes as the fill model gets harsher but never turns positive.

## 7. Rival timing (`cadence.py`)

Distinct print milliseconds cluster at 90-99 ms of each 100 ms (1.42x the mean in test3 run 1,
1.09-1.12x in dev3 and ext): a rival population keyed to a 100 ms clock, not batched matching.
Our orders' fill rate, rival prints and markout show no pattern by match-time phase.

## 8. Ideas and status

| idea | status | premises |
|---|---|---|
| size by predicted value (2000-3000 x value) | **open, positive** on unseen under base, e+25, comp for all three deployed arms; flat in busy hours at L = 0 | selection not blind; rival reaction to our size not modelled; L = -40 busy is negative (CIs cross 0) |
| fewer shares when depth is thin / rivals active (round 1) | **lost a comparison** to 60 sh, every fill model | thin depth and crowding mark the stale quotes, the best fills |
| fixed size-up (100-300 sh) | **lost a comparison** to value-keyed size | 300 sh: -$1,034/day busy under comp |
| value-capped, looser limit (chase depth) | **lost a comparison** to the value-keyed size at + 2 c | select-only gain; unseen CIs cross 0; L = -40 busy -$1,837 to -$3,246 |
| regime-tight limit in busy hours | **never tested** (no busy select window) | ext hint only: +$692 [-89, +1,601] at L = -40 comp |
| race-aware label (rmin, ravg) | **lost a comparison** to the frozen v1 at the same margin, every fill model | L = 0 sim with e <= +25 and comp; reopen only if Dublin is >= 50 ms late |
| cancel a held taker order when a rival prints in our hold | **never tested** | needs Polymarket to allow cancelling a held taker order (unknown) |
| leaders as the main rival | **rejected** | 0-12% of rival hold prints |

## Hypotheses (falsifiable)

1. **Value-keyed size is the competition-robust capacity lever:** pre-register 2000 x value
   (30-200 sh) for the 1 s taker and 3000 x value (100-300 sh) for the veto as secondary arms
   on the next unseen window after prereg2. Predicted: gain vs the same arm at 60 sh > 0 under
   base and e+25, comp CI low bound >= 0, busy hours within +/-$300/day. Fails if comp < 0.
2. **Competition is adverse selection on winners:** on any new window, the comp / e+25 fill
   keeps a smaller share of winners' than losers' dollars (gap >= 15 points). The paper run
   should show its realized-vs-simulated shortfall concentrated in high-value orders.
3. **Bias, not jitter:** in the Dublin paper run, markout per order vs measured receipt-to-CLOB
   offset; the mean offset predicts the shortfall, its spread does not (convex race curve).
4. **Chasing loses in busy hours:** with a busy select window, a tighter limit when the value is
   small (floor 2 c) beats + 2 c at L = -40 under comp; a looser one loses.
5. **100 ms rival cadence:** the 90-99 ms print cluster strengthens with Binance activity; if a
   rival group trades on @100ms streams, our bookTicker trigger stays ahead of it.
