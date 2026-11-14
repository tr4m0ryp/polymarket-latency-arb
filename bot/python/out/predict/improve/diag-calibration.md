# Diagnostic: calibration and regime drift of the frozen value models

Date 2026-10-12. Code `research/predict/improve/diag/calibration/`, detail tables in
`data/out/predict/improve/calibration/` (`calib.md`, `calib_overall.csv`, `trades.md`, `shift.md`,
`attrib.md`, `recal_rows.md`, `sim_recal.md`, `sim_rm.md`, `rm_choice.json`). Allowed markets only:
train (run 2, 143), select (144), dev3 (120), test3 run 1 (`final`, 83), ext (48); every entry point
asserts max(market start) < 1791744900 and the store refuses hour files at or after it. Read-only:
no orders, frozen models and arms untouched.

## Verdict

**The 1 s model drifts from under- to over-predicting, but the money is in the margin, not the
calibration.** In run 2 and dev3 it under-predicts its own 1 s target in the firing region by
+2 to +5 c/share (calibration slope 1.5-2.1). In test3 run 1 it is about calibrated (slope 0.97).
In the busy extension it over-predicts by **-2.2 c [-3.2, -1.0]**, with slope 0.75 and twice the
firing rows per hour. Correcting the prediction toward its target (isotonic, online bias, lower
bound) does not beat the frozen arm in the simulator. Correcting the **margin by activity regime**
does: 2.5 c in normal activity and the deployed 3 c in the extreme-activity regime.

- **Margin too tight in normal hours, about right in busy hours (L = 0).** dev3 m2 vs m3:
  +$963/day [+14, +2,310]. ext m2.5 vs m3: -$655 [-1,424, +51]; ext m3.5: -$528 [-1,178, +51].
- **At L = -40 the 3 c margin is too loose when busy.** ext m3.5 vs m3: +$828 [-155, +1,831];
  dev3 m2: +$1,091 [+244, +2,150].
- **Regime margin picked on select only** (it also survives the 50 ms competition sensitivity;
  the static 2.5 c margin does not):
  - **L = -40, `rm_2.5_3`:** gain over frozen on 251 unseen markets **+$315/day [+55, +618]**;
    over micf **+$1,675 [+586, +2,895]** (frozen: +$1,360 [+360, +2,461]).
  - **L = 0, `rm_2.5_3.5`:** gain over frozen +$227 [-99, +574] (P <= 0 = 0.10); over micf
    **+$1,076 [+155, +2,106]** (frozen: +$849 [-51, +1,879]).
- **Raising the margin in busy hours loses at L = 0:** busy_m4.5 -$494 [-890, -122] and pmtr_m4
  -$595 [-1,170, -153] vs frozen, pooled unseen. The busy-hour rows at 3-4.5 c are over-predicted
  but still carry positive 10 s value.
- **What inflates predictions when busy:** the spot book. Mapping only the spot-book features of
  ext back onto train marginals removes the whole inflation: mean firing prediction 4.82 -> 3.00 c,
  versus 2.97 c with every feature mapped. The drivers are spot queue depletion toward the side,
  the 50-100 ms spot microprice change, a thinner spot touch and a shorter time-to-depletion
  (log median 3.2 vs 5.6).
- **The miscalibration cannot be predicted from features.** A residual model reaches held-out
  R2 = -0.04 when split by market. The drift is a window-level shift, which is why static
  feature-based recalibration fails.

## 1. Calibration in the firing region (chosen side, pred >= 3 c, row level, best level)

gap = realised - predicted, c/share, market-bootstrap 95% CI; slope = OLS of realised 1 s on pred
over pred >= 0 rows (1 = calibrated, > 1 under-confident).

| model | window | firing rows/h | pred c | realised 1 s c | gap 1 s | realised 10 s c | gap 10 s | slope |
|---|---|---|---|---|---|---|---|---|
| v1_L0 | train | 812 | 7.25 | 10.82 | +3.6 [+2.4, +4.8] | 11.63 | +4.4 [+2.6, +6.1] | 1.55 [1.37, 1.77] |
| v1_L0 | select | 489 | 6.21 | 10.82 | +4.6 [+0.6, +8.5] | 11.73 | +5.5 [+1.4, +9.8] | 2.10 [1.38, 2.92] |
| v1_L0 | dev3 | 601 | 6.91 | 10.67 | +3.8 [+0.6, +7.3] | 11.17 | +4.3 [+0.3, +8.8] | 1.85 [1.31, 2.38] |
| v1_L0 | final | 533 | 6.71 | 5.89 | -0.8 [-3.4, +1.6] | 7.97 | +1.3 [-2.3, +4.9] | 0.97 [0.64, 1.32] |
| v1_L0 | **ext** | **1,008** | 4.82 | 2.65 | **-2.2 [-3.2, -1.0]** | 4.09 | -0.7 [-2.7, +1.2] | **0.75 [0.53, 0.97]** |
| v1_L-40 | select | 941 | 6.69 | 9.73 | +3.0 [+0.8, +5.2] | 10.07 | +3.4 [+0.9, +5.8] | 1.78 [1.40, 2.16] |
| v1_L-40 | dev3 | 1,123 | 7.20 | 9.44 | +2.2 [+0.5, +4.2] | 9.48 | +2.3 [-0.3, +5.0] | 1.67 [1.39, 1.97] |
| v1_L-40 | final | 879 | 7.60 | 7.49 | -0.1 [-2.0, +1.7] | 9.75 | +2.2 [-0.5, +4.7] | 1.20 [0.97, 1.43] |
| v1_L-40 | **ext** | **2,739** | 5.39 | 3.04 | **-2.4 [-3.1, -1.4]** | 4.17 | -1.2 [-2.4, +0.0] | **0.79 [0.65, 0.94]** |
| v3p_L0 (retired) | ext | 1,188 | 4.93 | 2.00 | -2.9 [-4.0, -1.9] | 3.62 | -1.3 [-3.5, +1.2] | 0.71 [0.49, 0.90] |

By prediction decile (`calib.md`) the bulk (deciles 0-8) is calibrated within 0.1 c in every
window. Only ext's top two deciles over-predict, by 0.6 c and 1.6 c. By fixed bin, ext
over-predicts the 1 s target by about 2 c at every level from 1 to 7 c, an additive level shift.
In the quiet windows the under-prediction sits in the >= 7 c bin (realised 21-24 c vs predicted
10-11 c), the shrinkage of a 15-leaf GBDT with min 200 rows per leaf.

**Within-window regime splits** (busy-index, Binance rate, 10 s volatility, Polymarket top-change
and trade rate tertiles, train cutpoints) mostly overlap. The one consistent discriminator is the
**Polymarket trade rate (rivals' taker activity)**. In its top tertile the 1 s gap is the lowest
in dev3 (-1.4 [-3.7, +1.2] vs +8.8 in the mid tertile), final (-3.2 [-6.6, -0.3]) and ext
(-2.3 [-3.6, -1.0]).

## 2. What changed in ext (regime medians per decision row)

| window | perp msgs/s (60 s) | spot msgs/s (10 s) | perp vol 60 s, bp/sqrt(s) | PM book msgs/s | PM top changes/s | PM trades/s | rows in train busy tertile |
|---|---|---|---|---|---|---|---|
| train | 80 | 18.5 | 0.050 | 698 | 1.0 | 3.1 | 33% |
| select | 75 | 19.7 | 0.053 | 783 | 1.4 | 3.6 | 34% |
| dev3 | 67 | 18.2 | 0.036 | 737 | 1.3 | 3.5 | 29% |
| final | 69 | 17.1 | 0.041 | 840 | 1.4 | 4.0 | 32% |
| **ext** | **232** | **69.7** | **0.167** | **1,124** | **2.0** | **5.1** | **85%** |

`final` looks like train on every activity measure, yet its slope already fell to 0.97. Part of the
drift is therefore not activity: day-of-week, or more and faster makers (PM trades/s +27% vs train
in `final`).

## 3. Trade level (frozen simulator fills of the deployed arms, L = 0)

| arm | window | fills / market-hour | pred c/sh | realised 10 s c/sh | gap c/sh | 10 s markout c/$ |
|---|---|---|---|---|---|---|
| vt_v1_m0.03_any | select | 23.8 | 4.21 | 7.97 | +3.8 [+0.9, +6.8] | +14.3 [+7.6, +23.7] |
| vt_v1_m0.03_any | dev3 | 16.9 | 4.51 | 11.04 | +6.5 [+2.8, +10.9] | +24.5 [+15.2, +35.6] |
| vt_v1_m0.03_any | final | 19.4 | 4.08 | 8.08 | +4.0 [-4.5, +12.1] | +13.7 [-2.8, +33.5] |
| vt_v1_m0.03_any | **ext** | **38.8** | 3.74 | 3.59 | **-0.2 [-2.7, +3.1]** | +7.8 [+1.5, +15.5] |
| vt_v1_m0.02_trigger | dev3 | 18.3 | 3.76 | 8.80 | +5.0 [+2.6, +7.6] | +17.3 [+12.4, +22.8] |
| vt_v1_m0.02_trigger | **ext** | **56.5** | 2.71 | 1.54 | **-1.2 [-3.0, +1.1]** | +3.8 [-1.6, +9.5] |

In busy hours the taker's fills are calibrated rather than over-predicted, so its predictions are
not wrong at the fill level. Each fill is worth a third of what it was, and there are twice as
many. The veto lets the leaders' trigger through 3-7x as often, at about zero markout per share.

## 4. Covariate shift, train vs window (`shift.md`)

| window | domain AUC | largest PSI (feature: PSI) | group carrying the shift (AUC drop) |
|---|---|---|---|
| select | 0.648 | sigma 0.30, lzs 0.13 | settlement scale 0.085, spot book 0.043 |
| dev3 | 0.654 | sigma 0.28, s_lq 0.19 | spot book 0.066, settlement scale 0.055 |
| final | 0.681 | sigma 0.23, s_lq 0.22, PM trades 0.20 | spot book 0.077, settlement scale 0.057 |
| **ext** | **0.855** | **perp msgs 1.84, sigma 1.58, rv60 1.50, lzs 1.08, delta 0.91, s_lq 0.85, p_tsm 0.84** | **settlement scale 0.160, spot book 0.109** |

PSI > 0.25 counts as a major shift. In ext, 30+ features exceed it; the other windows stay at or
below 0.30.

## 5. What drives the inflation (`attrib.md`, v1_L0)

Quantile-mapping each feature group of ext onto its train marginal and re-predicting:

| group mapped to train | firing share % (0.83 observed) | mean pred of firing rows c (4.82 observed) |
|---|---|---|
| all features | 0.54 | 2.97 |
| **spot book only** | **0.42** | **3.00** |
| perp intensities / last tick | 1.03 | 5.40 |
| settlement scale (sigma, zs, delta) | 1.01 | 5.27 |
| any other group | 0.78-0.91 | 4.59-5.06 |

Per feature (`attrib_ext_features.csv`, side-oriented: "toward the side" = the queue whose
emptying moves the price toward the bought side) the largest single effects are:
- spot queue depletion toward the side (-0.45 c)
- spot microprice change over 50 ms (-0.40 c) and 100 ms (-0.20 c)
- spot touch size (-0.26 c, a thinner touch)
- spot time-to-depletion toward the side (-0.17 c; log median 3.2 vs 5.6)

In quiet hours these spot "move coming" signals precede a Polymarket repricing. When busy they fire
at twice the base rate while makers already reprice faster (top changes/s 2.0 vs 1.0), so the
residual after the hold is smaller. Higher volatility halves `delta` (8.9 vs 18.6 c per bp), and
that pulls predictions down (+0.42 c when mapped back), partly cancelling the inflation.

Within-regime permutation (pooled unseen, sampled rows) points the same way. The spot book and the
Polymarket state carry the ranking in both regimes (top-2% drop 8.0 / 3.9 c quiet, 6.2 / 4.2 c
busy). Shuffling either one turns the busy-regime firing gap negative. A residual model on
(realised - pred) has **held-out R2 -0.04**, so no stable feature pattern predicts the
miscalibration across markets.

## 6. Recalibration forms in the simulator (unchanged simulator, 150 ms hold, J 10 ms)

The rebuilt frozen arms reproduce the frozen agg files to the cent in every window, for example
ext L = 0 $1,450.2 and L = -40 $2,301.4. Gains are paired 10 s markout $/day vs the frozen arm.
Static forms were fitted on select; the `rm_*` pick was made on select (`rm_choice.json`,
12:14:58 UTC) before its unseen runs.

| arm | L | unseen 251 mkts: mk $/day | vs frozen | vs micf | ext only: vs frozen |
|---|---|---|---|---|---|
| **frozen vt_v1_m0.03_any** | 0 | 1,850 | | +849 [-51, +1,879] | |
| m2.5 (static) | 0 | 2,069 | +220 [-126, +609] | +1,069 [+114, +2,122] | -655 [-1,424, +51] |
| iso (select fit, ~2.6 c) | 0 | 1,972 | +122 [-228, +498] | +972 [+49, +1,966] | -810 [-1,490, -187] |
| iso per busy tertile | 0 | 1,612 | -237 [-855, +380] | +612 [-404, +1,646] | -928 [-1,811, -88] |
| busy_m4.5 | 0 | 1,356 | **-494 [-890, -122]** | +356 [-358, +1,112] | -1,014 [-2,065, -135] |
| pmtr_m4 | 0 | 1,255 | **-595 [-1,170, -153]** | +254 [-430, +927] | -933 [-2,178, +25] |
| online bias, 10 s mark, band 2-5 c, tau 90 min | 0 | 1,800 | -50 [-747, +714] | +800 [-372, +2,009] | -1,178 [-2,079, -429] |
| online ratio, 1 s mark, tau 90 min | 0 | 1,689 | -161 [-1,055, +585] | +688 [-187, +1,610] | -1,333 [-2,571, -268] |
| **rm_2.5_3.5 (select pick)** | 0 | 2,076 | +227 [-99, +574] | **+1,076 [+155, +2,106]** | -425 [-1,168, +237] |
| rm_2.5_3 | 0 | 2,163 | **+314 [+21, +651]** | **+1,163 [+237, +2,200]** | +37 [-242, +357] |
| **frozen vt_v1_m0.03_any** | -40 | 2,891 | | +1,360 [+360, +2,461] | |
| m3.5 | -40 | 2,778 | -113 [-437, +209] | +1,248 [+376, +2,246] | +828 [-155, +1,831] |
| iso (select fit) | -40 | 2,770 | -122 [-438, +207] | +1,239 [+364, +2,249] | +835 [-157, +1,843] |
| **rm_2.5_3 (select pick)** | -40 | 3,206 | **+315 [+55, +618]** | **+1,675 [+586, +2,895]** | -188 [-753, +343] |
| rm_3_3.5 | -40 | 2,973 | +82 [-69, +245] | +1,442 [+438, +2,526] | +592 [-86, +1,320] |
| frozen veto vt_v1_m0.02_trigger | -40 | 2,406 | | +875 [+400, +1,282] | |
| veto, margin 3 c | -40 | 2,214 | -192 [-501, +73] | +683 [+218, +1,086] | +486 [-624, +1,517] |
| veto, online 10 s bias | -40 | 2,071 | **-335 [-660, -55]** | +540 [+102, +940] | -586 [-2,177, +589] |

`rm_Q_B`: margin Q c when the busy index (mean of train-standardised log perp message rate, 60 s
volatility and Polymarket trade rate) is below 1.0, B c at or above it. That is 11.6% of train rows
and 62.6% of ext rows. The full margin sweep (m2-m5) per window is in `sim_recal.md`. It puts the
L = 0 optimum at 2 c in dev3 (+$963 [+14, +2,310]), 2.5 c in final (+$393 [+36, +795]) and 3 c in
ext. At L = -40 it is 2 c in dev3 and 3.5 c in ext.

**Competition sensitivity** (J = 50 ms race window, half of each level; `sim_rmcomp.md`):

| arm | L | unseen mk $/day | vs frozen (same conditions) | ext only: vs frozen |
|---|---|---|---|---|
| frozen vt_v1_m0.03_any | 0 | 946 | | |
| m2.5 (static) | 0 | 1,071 | +125 [-185, +477] | **-838 [-1,482, -247]** |
| rm_2.5_3 | 0 | 1,199 | **+253 [+3, +570]** | -88 [-302, +136] |
| rm_2.5_3.5 | 0 | 1,194 | +248 [-14, +578] (P <= 0 = 0.04) | -199 [-635, +204] |
| frozen vt_v1_m0.03_any | -40 | 839 | | (ext alone -$540/day) |
| m2.5 (static) | -40 | 727 | -112 [-443, +207] | **-1,557 [-2,467, -737]** |
| rm_2.5_3 | -40 | 991 | +152 [-27, +372] | -189 [-646, +235] |
| rm_2.5_3.5 | -40 | 1,161 | **+322 [+75, +591]** | +689 [-130, +1,590] |

Under rivals the static lower margin breaks in the busy hours, while the regime margin keeps its
gain. It holds because it fires less exactly where extra fills are contested.

## 7. Ideas and their status

| idea | status | evidence / premises |
|---|---|---|
| "3 c too loose when busy": raise the margin in the busy tertile (L = 0) | **lost a comparison** | busy_m4.5 -$494 [-890, -122], pmtr_m4 -$595 [-1,170, -153]; ext rows at 3-4.5 c still +2.7 to +3.3 c/sh at 10 s. Holds at L = -40 in ext only (m3.5 +$828, CI touches 0) |
| "3 c too tight when quiet": lower margin outside extreme activity | **open, positive** | rm_2.5_3 (L = -40, select pick) +$315 [+55, +618]; L = 0 neighbour +$314 [+21, +651], select pick +$227 [-99, +574] |
| isotonic recalibration (global / per busy tertile, select fit) | **lost a comparison** | +122 [-228, +498] / -237 [-855, +380] at L = 0; select is under-confident, so the map inflates p exactly where ext over-predicts (ext -810 / -928) |
| online self-calibration from delayed labels (1 s and 10 s marks, bias and ratio) | **lost a comparison** | every variant <= frozen on unseen; correct direction in ext (it raises the effective margin) but costs $1.2-1.3k/day there, because the marginal fills are profitable. Premise: corrects p toward its own target; reopenable as an online estimate of marginal fill value |
| q25 lower-bound model (train fit, budget-matched) | **lost a comparison** (row level only) | ext row proxy -$3,101 [-9,711, +1,537]; not simulated |
| feature-level residual correction | **proven closed on these data** | premise: a market-split residual model must generalise; held-out R2 -0.04 |
| recalibrated veto (margin 3 c, online bias) | **lost a comparison** | -192 / -335 at L = -40; the veto's busy-hour problem is the trigger's fire rate, not the margin |

## 8. Caveats

- **Garden of forking paths:** the regime-margin family was proposed after the margin sweep had been
  read on the unseen windows (ext wants a higher margin than dev3). Only the grid pick was made on
  select. The 251 markets are therefore not a clean test for `rm_*`; the sealed prereg2 hours or
  later hours are.
- **One busy window:** the extreme-activity regime appears in 4 h of one Sunday (48 markets). Its
  threshold (busy index 1.0) was fixed from train percentiles, and select holds only 13.5% of such
  rows, so the busy-side margin is weakly identified.
- **Competition:** the regime-margin gain survives the 50 ms / half-depth sensitivity
  (+$248-322/day). The micf comparison under that sensitivity was not rerun, because micf was
  taken from the frozen J = 10 ms files.
- **Row proxy vs simulator:** the best-level row test (`recal_rows.md`) favours lower margins
  everywhere. In ext the simulator shows those extra fills lose (m2 -$1,805 [-3,942, -157]); depth
  and rivals decide the busy-hour margin, not calibration.

## 9. Testable hypotheses (next)

1. **Regime margin (primary candidate):** `rm_2.5_3`, 2.5 c below busy index 1.0 and 3 c at or
   above it, beats the frozen 3 c taker at L = 0 and L = -40.
   - Test: freeze it now and register it as an additional arm on the sealed prereg2 hours, or on
     hours after run 3, before anyone opens them.
   - Pass: paired 10 s gain vs frozen with CI above 0 at L = -40, and the same sign at L = 0.
   - Predicted: about +$300/day (+$150-320 under the 50 ms competition sensitivity).
2. **Continuous activity margin:** a margin that rises smoothly with the busy index (for example
   2.5 c + 0.5 c per index unit above 0, capped at 3.5 c) captures the L = -40 busy-hour gain
   (m3.5 +$828 in ext) without the step.
   - Test: choose the slope on select plus dev3, then score on final plus ext and on fresh hours.
3. **Spot-signal base-rate normalisation:** divide the spot depletion, microprice-change and
   time-to-depletion inputs by their trailing 10-30 min base rate before scoring. This should
   remove the busy-hour prediction inflation, which comes from the spot book alone.
   - Test: retrain v1 on train with the normalised features. The ext firing-region 1 s gap should
     move from -2.2 c toward 0, and the select ranking (top-2% value) should not degrade.
4. **Marginal-value online margin:** instead of correcting p toward its target, estimate online
   the realised 10 s value of the last N would-be fills in the marginal band, using the simulator's
   fill logic live. Raise the margin when that value turns <= 0.
   - Test: replay on all allowed windows; it must match rm_2.5_3 on dev3 and beat it in ext.
5. **Veto fire-rate cap in busy hours:** the veto's busy-hour loss is the trigger rate (56 fills
   per market-hour, 1.5 c/sh), not its margin.
   - Test: cap veto orders per 5 s window only when the busy index is >= 1.0. Pass: ext gain vs
     the frozen veto > 0 with dev3 unchanged.

