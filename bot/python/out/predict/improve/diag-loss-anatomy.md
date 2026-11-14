# Loss anatomy of the deployed predictive arms (diagnostic)

Date 2026-10-12. Code `research/predict/improve/diag/loss-anatomy/`, tables
`data/out/predict/improve/loss-anatomy/*.csv`. Arms: 1 s taker `vt_v1_m0.03_any` (taker1s), trigger
veto `vt_v1_m0.02_trigger` (veto), micf for contrast; L = 0 and -40; frozen fills of the select
(sel1), dev3 (dev1), test3 run 1 (final) and extension (ext) runs, 8,248 fills on 395 markets. No
re-simulation; edge = 10 s markout. Sealed prereg2 segment (start >= 1791744900) never opened: market
lists come from frozen market files, every script asserts max(start) < 1791744900, and Polymarket
events are read only from hour files ending by 18:00 UTC (the eleven 18:00-18:50 ext markets have no
venue-depth columns). Diagnostic only: no arm, model or threshold of the frozen arms changes.

## Verdict

- **Losers are reversals, not costs:** winners and losers pay the same half spread, book walk,
  fee and hold drift; the whole gap is the venue move after the match (1 s taker, L = 0:
  +19.2 vs -6.3 c/sh). No execution-side change (limit, size, slippage) separates them.
- **One consistent separator, the settlement delta** (cents of the bought token per bp of BTC,
  `model/derive.py`): AUC for "fill loses" 0.31-0.40 on the deployed arms, below
  0.5 in every arm x L x window cell. Fills at delta <= 3 c/bp: -10.8 to -3.7 c/$,
  62%-78% losers; delta > 12 earns +10 to +28 c/$.
- **The model is flat across delta, the market is not:** predicted value at the fills stays at
  2.4-4.9 c/sh in every delta bin while the realized 10 s markout runs from
  -2.2 to +16.2 c/sh. Row level (every decision row with pred >= 3 c, best level, no
  simulator, L = 0): in ext the model over-predicts in every delta bin, worst at delta <= 3
  (4.2 c predicted, -0.7 c realized at 1 s); in the quiet windows it under-predicts at
  delta >= 8 (5.8-7.3 c predicted, 8.5-10.6 c realized) and low-delta rows are not
  clearly over-predicted (few markets).
- **The busy extension is a low-delta regime:** median fill delta 5.6-8.5 c/bp in ext vs
  15-62 elsewhere; 26%-41% of ext fills below 5 c/bp vs <= 8% elsewhere.
  The fire-rate jump in ext is mostly these fills. On top, ext under-delivers in every delta bin.
- **No gate chosen on select can see it:** select has 0-2% low-delta fills. A delta floor picked on
  select + dev3 and read on test3 run 1 + ext (fill-drop approximation, not a re-simulation):
  taker1s L0: thr 3, +61 [-45, +217]; taker1s L-40: thr 3, +269 [+2, +642]; veto L0: thr 4, +154 [-67, +467]; veto L-40: thr 6, +328 [-83, +769] $/day. It drops nothing in select or test3 run 1.
- **Everything else is weak or two-faced:** price level separates how often a fill loses (cheap
  tokens), not dollars; Binance message rate acts only through vol; burst position, own history,
  time to expiry and adding to a losing fill do not separate consistently; requiring Polymarket
  staleness removes the 1 s taker's early-entry edge (-$300 to -$920/day in every window).
- **Worst markets are one-offs:** the single worst (test3 run 1, 10:40 UTC) is a pinned BTC with
  the strike at spot (delta 200-280 c/bp): five Up buys in 1.4 s at 62 s to expiry with no Binance
  signal while the Up mid fell 0.77 -> 0.07. Market regime separates losing markets weakly.

## Method

Each fill is joined to its decision-table row (exact for the value-model arms, as-of for micf) for
Binance vol and message rate, Polymarket spread / staleness / recent repricing, the venue book
replayed at the decision (top size, depth to the limit, liquidity within 5 c), price level, time
to expiry, strike distance (|z| of the fair price, settlement delta), own history (burst
position, fills in the last 5 s, fills so far) and the 1 s model's prediction for both sides.
Loss = 10 s markout < 0. AUC with a 400-draw market bootstrap; $/day over all markets of the
windows read; gate effects = minus the markout of the fills a rule would have dropped, market
bootstrap (an approximation: a dropped order frees the 0.2 s refractory and the depth memory).

## 1. Arms on the allowed windows (10 s markout c/$ / fills per day)

| arm | L | select | dev3 | test3r1 | ext |
|---|---|---|---|---|---|
| micf | -40 | +5.4 / 848 | +9.6 / 614 | +7.8 / 555 | +2.1 / 1,224 |
| micf | 0 | +3.5 / 714 | +8.7 / 432 | +6.6 / 392 | +1.3 / 936 |
| taker1s | -40 | +8.9 / 1,658 | +13.7 / 1,445 | +8.5 / 1,270 | +2.6 / 5,148 |
| taker1s | 0 | +14.3 / 574 | +26.0 / 425 | +13.6 / 468 | +7.7 / 948 |
| veto | -40 | +8.4 / 1,238 | +9.0 / 1,433 | +13.4 / 857 | +1.0 / 5,154 |
| veto | 0 | +21.0 / 350 | +17.0 / 463 | +24.1 / 201 | +3.5 / 1,428 |

## 2. Winners vs losers: c per share of each markout part

`d_move` = venue mid 10 s after the match minus the mid at the match; `d_half` = mid minus ask at the match; `d_walk` = ask at the match minus the fill VWAP; `d_hold` = ask drift during the hold.

| arm | L | fill | n | d_move | d_half | d_walk | d_fee | d_hold | mk_sh |
|---|---|---|---|---|---|---|---|---|---|
| veto | 0 | winner | 401 | 16.16 | -0.66 | -0.32 | -1.29 | 0.34 | 13.89 |
| veto | 0 | loser | 242 | -3.52 | -0.64 | -0.42 | -1.10 | 0.30 | -5.69 |
| veto | -40 | winner | 1314 | 12.52 | -0.59 | -0.38 | -1.22 | 0.35 | 10.33 |
| veto | -40 | loser | 885 | -4.04 | -0.57 | -0.41 | -1.15 | 0.35 | -6.17 |
| taker1s | 0 | winner | 484 | 19.24 | -0.82 | -0.56 | -1.32 | -0.75 | 16.53 |
| taker1s | 0 | loser | 256 | -6.29 | -0.87 | -0.45 | -1.24 | -0.68 | -8.83 |
| taker1s | -40 | winner | 1470 | 14.22 | -0.63 | -0.47 | -1.31 | 0.00 | 11.82 |
| taker1s | -40 | loser | 1033 | -4.53 | -0.58 | -0.41 | -1.19 | 0.15 | -6.71 |
| micf | 0 | winner | 442 | 14.81 | -0.67 | -0.31 | -1.16 | 0.09 | 12.67 |
| micf | 0 | loser | 328 | -5.75 | -0.77 | -0.28 | -1.03 | 0.25 | -7.84 |
| micf | -40 | winner | 620 | 14.52 | -0.66 | -0.36 | -1.15 | 0.20 | 12.35 |
| micf | -40 | loser | 377 | -5.53 | -0.65 | -0.36 | -1.06 | 0.13 | -7.60 |

## 3. What separates losing fills (AUC for "fill loses", market bootstrap 95% CI, windows on the same side)

AUC > 0.5: higher values lose more often. Signed variables point toward the side bought.

| var | group | taker1s_L0 | veto_L0 | taker1s_L-40 | veto_L-40 | micf_L0 |
|---|---|---|---|---|---|---|
| delta | strike distance | 0.40 [0.32, 0.46] 4/4 | 0.31 [0.26, 0.38] 4/4 | 0.40 [0.37, 0.44] 4/4 | 0.38 [0.35, 0.41] 4/4 | 0.42 [0.37, 0.47] 4/4 |
| seen | price level | 0.38 [0.30, 0.46] 4/4 | 0.37 [0.31, 0.44] 4/4 | 0.37 [0.33, 0.42] 4/4 | 0.38 [0.34, 0.41] 4/4 | 0.54 [0.48, 0.59] 2/4 |
| pred_x_rv | model | 0.44 [0.37, 0.50] 2/4 | 0.33 [0.27, 0.39] 4/4 | 0.41 [0.37, 0.44] 4/4 | 0.38 [0.36, 0.41] 4/4 | 0.34 [0.30, 0.38] 4/4 |
| rv300 | binance vol | 0.57 [0.50, 0.64] 3/4 | 0.66 [0.60, 0.72] 4/4 | 0.59 [0.56, 0.62] 3/4 | 0.61 [0.58, 0.64] 3/4 | 0.58 [0.52, 0.62] 3/4 |
| pred_over_delta | model | 0.59 [0.53, 0.67] 3/4 | 0.66 [0.59, 0.72] 4/4 | 0.58 [0.54, 0.62] 4/4 | 0.59 [0.56, 0.62] 4/4 | 0.34 [0.30, 0.38] 4/4 |
| dist_bp | strike distance | 0.59 [0.53, 0.65] 4/4 | 0.66 [0.60, 0.71] 4/4 | 0.59 [0.55, 0.63] 4/4 | 0.59 [0.55, 0.62] 4/4 | 0.58 [0.53, 0.63] 4/4 |
| sigma | binance vol | 0.57 [0.50, 0.66] 2/4 | 0.66 [0.60, 0.72] 4/4 | 0.57 [0.52, 0.61] 2/4 | 0.61 [0.58, 0.64] 4/4 | 0.54 [0.48, 0.59] 3/4 |
| rv60 | binance vol | 0.55 [0.48, 0.63] 2/4 | 0.66 [0.60, 0.72] 4/4 | 0.58 [0.55, 0.62] 4/4 | 0.61 [0.59, 0.64] 4/4 | 0.58 [0.53, 0.63] 3/4 |
| v_near | polymarket book | 0.58 [0.52, 0.64] 2/4 | 0.62 [0.54, 0.69] 4/4 | 0.58 [0.55, 0.61] 4/4 | 0.56 [0.52, 0.59] 4/4 | 0.52 [0.47, 0.56] 2/4 |
| pred_other | model | 0.54 [0.48, 0.60] 4/4 | 0.63 [0.58, 0.67] 4/4 | 0.59 [0.56, 0.62] 4/4 | 0.57 [0.54, 0.59] 4/4 | 0.71 [0.66, 0.75] 4/4 |
| pred_gap | model | 0.46 [0.41, 0.52] 4/4 | 0.37 [0.33, 0.42] 4/4 | 0.42 [0.39, 0.45] 4/4 | 0.45 [0.42, 0.47] 4/4 | 0.29 [0.25, 0.34] 4/4 |
| rows10 | binance rate | 0.52 [0.45, 0.58] 2/4 | 0.62 [0.57, 0.67] 4/4 | 0.56 [0.52, 0.59] 2/4 | 0.60 [0.57, 0.62] 4/4 | 0.56 [0.50, 0.62] 3/4 |
| abs_mid | price level | 0.56 [0.51, 0.62] 4/4 | 0.60 [0.55, 0.65] 4/4 | 0.58 [0.54, 0.61] 4/4 | 0.55 [0.51, 0.58] 4/4 | 0.58 [0.52, 0.63] 4/4 |
| pm_stale | binance signal (signed) | 0.45 [0.40, 0.51] 3/4 | 0.39 [0.35, 0.44] 4/4 | 0.47 [0.44, 0.50] 3/4 | 0.42 [0.40, 0.45] 4/4 | 0.41 [0.37, 0.46] 3/4 |
| fill_idx | own history | 0.46 [0.40, 0.52] 2/4 | 0.60 [0.54, 0.66] 3/4 | 0.54 [0.51, 0.57] 3/4 | 0.58 [0.55, 0.61] 3/4 | 0.54 [0.49, 0.58] 2/4 |
| abs_dmid5 | binance vol | 0.56 [0.50, 0.62] 4/4 | 0.57 [0.51, 0.63] 3/4 | 0.55 [0.52, 0.58] 4/4 | 0.57 [0.54, 0.59] 4/4 | 0.57 [0.52, 0.61] 3/4 |

### Settlement delta: 10 s markout c/$ by bin (fills, share in ext)

| delta c/bp | micf L-40 | micf L0 | taker1s L-40 | taker1s L0 | veto L-40 | veto L0 |
|---|---|---|---|---|---|---|
| (0.0, 3.0] | -2.1 (17, 94% ext) | -2.5 (15, 93% ext) | -7.0 (153, 90% ext) | -10.8 (32, 81% ext) | -3.7 (187, 91% ext) | -9.9 (72, 90% ext) |
| (3.0, 5.0] | -3.8 (25, 56% ext) | -7.8 (18, 50% ext) | +4.5 (146, 73% ext) | +5.7 (22, 68% ext) | +1.3 (159, 65% ext) | +8.7 (47, 70% ext) |
| (5.0, 8.0] | -1.4 (59, 42% ext) | -1.7 (47, 40% ext) | +1.1 (406, 55% ext) | +3.9 (51, 69% ext) | +0.6 (462, 51% ext) | +5.5 (109, 50% ext) |
| (8.0, 12.0] | +2.4 (144, 41% ext) | +1.5 (116, 41% ext) | +6.6 (378, 48% ext) | +9.4 (77, 39% ext) | +2.8 (416, 44% ext) | +5.9 (98, 37% ext) |
| (12.0, 20.0] | +6.0 (250, 24% ext) | +5.0 (195, 23% ext) | +10.8 (473, 31% ext) | +20.1 (105, 21% ext) | +10.4 (434, 26% ext) | +16.7 (126, 25% ext) |
| (20.0, 40.0] | +8.2 (315, 7% ext) | +6.7 (240, 7% ext) | +9.8 (536, 9% ext) | +16.7 (177, 12% ext) | +11.9 (414, 11% ext) | +23.5 (119, 12% ext) |
| (40.0, inf) | +10.7 (233, 3% ext) | +8.1 (174, 3% ext) | +11.3 (563, 2% ext) | +17.1 (293, 3% ext) | +17.5 (250, 2% ext) | +28.1 (93, 4% ext) |

### Low-delta share by window: median delta / share < 5 c/bp / low-delta fills per day

| arm | L | select | dev3 | test3r1 | ext |
|---|---|---|---|---|---|
| taker1s | -40 | 25.8 / 1% / 14 | 21.9 / 7% / 101 | 24.8 / 2% / 24 | 7.5 / 28% / 1,458 |
| taker1s | 0 | 62.0 / 0% / 2 | 26.6 / 6% / 26 | 36.2 / 1% / 3 | 8.5 / 26% / 246 |
| veto | -40 | 16.5 / 2% / 28 | 15.2 / 8% / 118 | 19.8 / 4% / 31 | 6.5 / 32% / 1,644 |
| veto | 0 | 17.7 / 2% / 8 | 18.4 / 8% / 36 | 18.6 / 3% / 7 | 5.6 / 41% / 588 |

### Row-level calibration, L = 0 (every decision row with pred >= 3 c; best level, no rivals)

| regime | delta_bin | rows | mkts | pred_c | real_1s_c | real_10s_c |
|---|---|---|---|---|---|---|
| ext (busy) | (0.0, 3.0] | 899 | 12 | 4.2 | -0.7 | -0.6 |
| ext (busy) | (3.0, 5.0] | 401 | 12 | 4.8 | 0.1 | 2.5 |
| ext (busy) | (5.0, 8.0] | 559 | 19 | 4.1 | 2.5 | 0.7 |
| ext (busy) | (8.0, 12.0] | 1235 | 28 | 6.6 | 1.3 | 5.5 |
| ext (busy) | (12.0, 20.0] | 1005 | 26 | 4.8 | 3.9 | 2.9 |
| ext (busy) | (20.0, 40.0] | 669 | 18 | 6.0 | 3.0 | 7.3 |
| ext (busy) | (40.0, inf) | 162 | 8 | 4.8 | 2.2 | 12.8 |
| select+dev3+test3r1 | (0.0, 3.0] | 513 | 14 | 6.2 | 7.4 | 6.1 |
| select+dev3+test3r1 | (3.0, 5.0] | 530 | 28 | 5.0 | 3.2 | 1.6 |
| select+dev3+test3r1 | (5.0, 8.0] | 1298 | 44 | 4.9 | 5.0 | 2.5 |
| select+dev3+test3r1 | (8.0, 12.0] | 2090 | 74 | 5.8 | 9.6 | 8.9 |
| select+dev3+test3r1 | (12.0, 20.0] | 3304 | 120 | 6.4 | 10.6 | 14.5 |
| select+dev3+test3r1 | (20.0, 40.0] | 5225 | 173 | 6.6 | 8.5 | 12.1 |
| select+dev3+test3r1 | (40.0, inf) | 6729 | 150 | 7.3 | 9.0 | 10.4 |

### By hour, L = 0, test3 run 1 and ext: c/$ (fills, median delta)

| window | hour | taker1s | veto |
|---|---|---|---|
| ext | 14 | -1.9 (1, d 8) |  |
| ext | 15 | +13.8 (27, d 12) | +6.1 (36, d 3) |
| ext | 16 | +2.5 (74, d 6) | +2.9 (120, d 5) |
| ext | 17 | +8.7 (39, d 10) | +0.7 (61, d 8) |
| ext | 18 | +17.7 (17, d 16) | +10.3 (21, d 12) |
| test3r1 | 8 | +48.9 (13, d 15) | +29.6 (10, d 8) |
| test3r1 | 9 | +7.3 (28, d 28) | +28.7 (14, d 30) |
| test3r1 | 10 | -40.5 (10, d 219) | +5.9 (3, d 17) |
| test3r1 | 11 | +11.4 (9, d 36) | +10.0 (10, d 26) |
| test3r1 | 12 | +34.0 (14, d 32) | +44.5 (7, d 15) |
| test3r1 | 13 | +5.3 (25, d 39) | +14.6 (4, d 29) |
| test3r1 | 14 | +42.8 (36, d 104) | +23.8 (10, d 18) |

### Under the 50 ms competition sensitivity (test3 run 1, L = 0): c/$ (fills) by delta bin

| delta c/bp | micf final | micf final_comp | taker1s final | taker1s final_comp | veto final | veto final_comp |
|---|---|---|---|---|---|---|
| (0.0, 5.0] |  |  | -56.5 (1) |  | -34.1 (2) | -19.9 (1) |
| (5.0, 12.0] | +3.7 (15) | +6.2 (14) | +6.8 (16) | +6.3 (13) | +2.4 (13) | +1.3 (8) |
| (12.0, 40.0] | +5.2 (84) | +3.4 (73) | +16.1 (60) | +11.7 (51) | +31.4 (37) | +25.2 (26) |
| (40.0, inf) | +20.9 (14) | +10.6 (11) | +13.6 (58) | -0.3 (49) | +26.9 (6) | +23.4 (4) |

## 4. Worst markets

| arm | L | markets | usd_total | bottom5_usd | bottom5_fills | top5_usd | losing_mkts |
|---|---|---|---|---|---|---|---|
| micf | -40 | 312 | 2,050.39 | -190.46 | 26 | 400.26 | 0.33 |
| micf | 0 | 279 | 1,279.99 | -201.78 | 23 | 381.85 | 0.39 |
| veto | -40 | 360 | 3,154.48 | -172.06 | 117 | 425.40 | 0.25 |
| veto | 0 | 224 | 1,870.46 | -115.29 | 61 | 334.11 | 0.28 |
| taker1s | -40 | 365 | 4,106.98 | -499.81 | 194 | 732.23 | 0.28 |
| taker1s | 0 | 231 | 2,652.87 | -295.80 | 19 | 764.35 | 0.30 |


Per-market markout correlates across arms (Spearman 0.41-0.69), so bad markets are partly shared; whole-market regime (vol, message rate, Polymarket range and spread) separates losing markets with AUC <= 0.64 (`regime_auc.csv`). Worst markets of the 1 s taker at L = 0 (f_ = mean over its fills, m_range_c = Polymarket mid range in the market):

| window | m | hour | n | usd | c_usd | f_pred | f_abs_mid | f_secs_left | f_burst_pos | f_rv60 | m_range_c |
|---|---|---|---|---|---|---|---|---|---|---|---|
| test3r1 | 491 | 10 | 9 | -143.84 | -42.09 | 0.04 | 0.20 | 87.05 | 3.33 | 0.00 | 82.00 |
| select | 331 | 21 | 2 | -44.55 | -69.84 | 0.04 | 0.20 | 74.65 | 1.00 | 0.51 | 88.00 |
| select | 328 | 21 | 3 | -43.33 | -89.54 | 0.04 | 0.07 | 32.02 | 2.00 | 2.16 | 96.50 |
| test3r1 | 538 | 14 | 2 | -32.63 | -65.52 | 0.06 | 0.06 | 49.14 | 1.00 | 1.85 | 48.00 |
| dev3 | 358 | 23 | 3 | -31.45 | -45.98 | 0.04 | 0.09 | 111.35 | 2.00 | 0.00 | 55.00 |
| ext | 555 | 16 | 18 | -27.88 | -13.58 | 0.04 | 0.32 | 215.19 | 1.56 | 9.41 | 61.00 |
| test3r1 | 541 | 14 | 1 | -20.22 | -43.21 | 0.04 | 0.26 | 192.33 | 1.00 | 0.41 | 80.00 |
| ext | 545 | 15 | 3 | -19.34 | -41.68 | 0.03 | 0.19 | 105.84 | 1.33 | 0.64 | 54.00 |

## 5. Can a gate be selected?

Select-chosen tail cuts (10-30% of any of 52 decision-time variables, read on dev3 + test3 run 1 + ext): 20 of 208 add any markout on select, 0 have an unseen CI above 0. On select nearly every tail of every variable is net positive: the losing states are almost absent there.

Delta floor picked on select + dev3, read on test3 run 1 + ext ($/day of dropped fills' markout, market bootstrap; ignores knock-on effects on later orders):

| arm | L | thr | picked | fit_gain_day | read_dropped | read_gain_day | read_lo | read_hi | read_p_le0 | read_c_before | read_c_after |
|---|---|---|---|---|---|---|---|---|---|---|---|
| taker1s | 0 | 2.0 | False | 1.3 | 22 | 73.9 | 0.0 | 209.2 | 0.1 | 10.9 | 11.7 |
| taker1s | 0 | 3.0 | True | 8.3 | 26 | 61.1 | -45.4 | 217.0 | 0.2 | 10.9 | 11.8 |
| taker1s | 0 | 4.0 | False | 7.0 | 30 | 41.7 | -68.4 | 200.5 | 0.3 | 10.9 | 11.8 |
| taker1s | 0 | 5.0 | False | 6.8 | 42 | 16.1 | -166.7 | 207.8 | 0.4 | 10.9 | 11.9 |
| taker1s | 0 | 6.0 | False | 6.8 | 62 | 19.6 | -163.1 | 210.5 | 0.4 | 10.9 | 12.6 |
| taker1s | 0 | 8.0 | False | 0.4 | 82 | -31.3 | -257.7 | 183.2 | 0.6 | 10.9 | 12.8 |
| taker1s | -40 | 2.0 | False | 2.6 | 100 | 181.2 | -19.4 | 505.0 | 0.1 | 4.7 | 5.4 |
| taker1s | -40 | 3.0 | True | 15.0 | 137 | 269.5 | 2.3 | 641.6 | 0.0 | 4.7 | 5.7 |
| taker1s | -40 | 4.0 | False | 10.7 | 185 | 215.0 | -79.1 | 614.4 | 0.1 | 4.7 | 5.7 |
| taker1s | -40 | 5.0 | False | -13.7 | 250 | 128.1 | -302.0 | 590.6 | 0.3 | 4.7 | 5.9 |
| taker1s | -40 | 6.0 | False | -44.9 | 349 | 248.5 | -147.4 | 694.6 | 0.1 | 4.7 | 6.8 |
| taker1s | -40 | 8.0 | False | -168.7 | 498 | 279.6 | -226.6 | 810.3 | 0.1 | 4.7 | 7.9 |
| veto | 0 | 2.0 | False | 2.4 | 55 | 158.0 | 0.2 | 440.3 | 0.0 | 8.2 | 11.1 |
| veto | 0 | 3.0 | False | 6.1 | 65 | 191.3 | 8.7 | 501.3 | 0.0 | 8.2 | 11.8 |
| veto | 0 | 4.0 | True | 6.2 | 81 | 154.1 | -66.7 | 467.0 | 0.1 | 8.2 | 12.0 |
| veto | 0 | 5.0 | False | 0.7 | 100 | 71.5 | -231.9 | 415.2 | 0.3 | 8.2 | 11.9 |
| veto | 0 | 6.0 | False | -0.8 | 132 | 36.5 | -260.0 | 370.3 | 0.4 | 8.2 | 13.1 |
| veto | 0 | 8.0 | False | -70.5 | 162 | -14.3 | -338.0 | 354.5 | 0.5 | 8.2 | 14.2 |
| veto | -40 | 2.0 | False | 2.6 | 123 | 182.6 | -8.6 | 502.8 | 0.0 | 4.0 | 4.8 |
| veto | -40 | 3.0 | False | 9.1 | 170 | 280.9 | 16.5 | 640.5 | 0.0 | 4.0 | 5.3 |
| veto | -40 | 4.0 | False | 10.9 | 216 | 227.1 | -99.9 | 626.6 | 0.1 | 4.0 | 5.4 |
| veto | -40 | 5.0 | False | 11.8 | 283 | 188.9 | -189.6 | 599.1 | 0.2 | 4.0 | 5.7 |
| veto | -40 | 6.0 | True | 15.2 | 406 | 328.1 | -83.1 | 769.3 | 0.1 | 4.0 | 7.2 |
| veto | -40 | 8.0 | False | -159.3 | 545 | 398.0 | -30.3 | 851.7 | 0.0 | 4.0 | 9.4 |


Rules read window by window (round thresholds chosen after seeing all windows: diagnostic):

| rule | arm | L | select | dev3 | test3r1 | ext |
|---|---|---|---|---|---|---|
| delta < 3 c/bp | taker1s | -40 | +0 [+0, +0] (0) | +33 [-15, +119] (16) | +0 [+0, +0] (0) | +735 [-21, +1,718] (137) |
| delta < 3 c/bp | taker1s | 0 | +0 [+0, +0] (0) | +18 [+0, +55] (6) | +0 [+0, +0] (0) | +167 [-118, +592] (26) |
| delta < 3 c/bp | veto | -40 | +0 [+0, +0] (0) | +20 [-14, +78] (17) | +0 [+0, +0] (0) | +767 [+31, +1,671] (170) |
| delta < 3 c/bp | veto | 0 | +0 [+0, +0] (0) | +13 [+0, +40] (7) | +0 [+0, +0] (0) | +522 [+13, +1,342] (65) |
| delta < 5 c/bp | taker1s | -40 | -10 [-75, +31] (7) | -18 [-101, +65] (42) | -9 [-48, +19] (7) | +366 [-952, +1,551] (243) |
| delta < 5 c/bp | taker1s | 0 | +2 [+0, +5] (1) | +13 [-11, +54] (11) | +8 [+0, +25] (1) | +30 [-470, +555] (41) |
| delta < 5 c/bp | veto | -40 | +39 [-1, +101] (14) | -21 [-101, +54] (49) | +1 [-22, +25] (9) | +513 [-590, +1,581] (274) |
| delta < 5 c/bp | veto | 0 | -9 [-55, +21] (4) | +13 [-9, +46] (15) | +13 [+0, +34] (2) | +173 [-680, +1,111] (98) |
| pm_stale <= 0 | taker1s | -40 | -919 [-1,778, -210] (271) | -583 [-1,372, +28] (81) | -299 [-2,408, +1,845] (123) | -706 [-1,539, +195] (168) |
| pm_stale <= 0 | taker1s | 0 | -637 [-1,401, +31] (132) | -783 [-1,800, +12] (40) | -585 [-2,773, +1,046] (66) | -830 [-2,085, +24] (41) |
| pm_stale <= 0 | veto | -40 | -11 [-135, +79] (16) | +83 [-63, +281] (14) | +7 [-11, +31] (2) | +258 [-232, +928] (65) |
| pm_stale <= 0 | veto | 0 | -4 [-109, +76] (5) | -54 [-154, +15] (4) | +1 [+0, +2] (1) | +25 [-189, +270] (19) |
| pred_gap < select q20 | taker1s | -40 | -271 [-818, +350] (166) | -286 [-589, -43] (91) | +94 [-756, +1,228] (81) | +284 [-417, +1,047] (158) |
| pred_gap < select q20 | taker1s | 0 | -277 [-695, +130] (58) | -134 [-346, +5] (12) | -215 [-822, +300] (30) | -526 [-1,035, -129] (18) |
| pred_gap < select q20 | veto | -40 | +25 [-128, +206] (124) | -110 [-289, +74] (159) | -355 [-704, -59] (62) | +16 [-846, +792] (190) |
| pred_gap < select q20 | veto | 0 | -66 [-147, +17] (35) | +48 [-24, +132] (39) | -44 [-118, +22] (10) | -128 [-650, +259] (57) |
| rv60 > 4 bp | taker1s | -40 | -93 [-280, +67] (62) | -175 [-519, +82] (42) | -25 [-76, +3] (8) | +1,150 [+201, +2,242] (302) |
| rv60 > 4 bp | taker1s | 0 | -18 [-86, +31] (7) | -111 [-379, +65] (22) | +0 [+0, +0] (0) | +121 [-374, +629] (57) |
| rv60 > 4 bp | veto | -40 | -64 [-148, +6] (78) | -196 [-529, +20] (46) | -8 [-35, +6] (7) | +700 [-420, +1,822] (345) |
| rv60 > 4 bp | veto | 0 | -96 [-298, +41] (18) | -143 [-400, +52] (22) | +5 [+0, +14] (1) | +181 [-595, +1,181] (106) |
| seen > 0.80 | taker1s | -40 | -383 [-910, +34] (99) | -134 [-238, -21] (64) | +353 [-318, +1,438] (63) | +248 [-263, +897] (45) |
| seen > 0.80 | taker1s | 0 | -187 [-672, +207] (42) | -82 [-164, -28] (14) | -126 [-331, +46] (29) | -27 [-186, +155] (11) |
| seen > 0.80 | veto | -40 | +33 [-116, +199] (92) | -184 [-295, -51] (141) | -71 [-200, +68] (48) | +114 [-271, +522] (102) |
| seen > 0.80 | veto | 0 | -26 [-73, +21] (20) | -63 [-129, -6] (30) | +2 [-3, +9] (4) | -100 [-271, +9] (13) |

## 6. Ideas tested here and their status

| idea | status | evidence / premises |
|---|---|---|
| delta floor (no order below 3-6 c/bp) | **open, positive** (screen, not re-simulated) | picked on select + dev3, positive on test3 run 1 + ext in 4 of 4 arm x L, CI above 0 in 1 (taker1s L-40); zero cost in quiet windows |
| Binance vol gate (rv60 > 4 bp) | **lost a comparison** to the delta floor | helps ext (+$121 to +$1,150/day) but costs $18-196/day in select and dev3 |
| require Polymarket staleness (pm_stale > 0) | **lost a comparison** | removes the 1 s taker's early entries: -$300 to -$920/day in every window |
| drop expensive tokens (seen > 0.80) | **lost a comparison** | negative in 11 of 16 window reads |
| two-side gap cut (pred - pred_other < select q20) | **lost a comparison** as a cut; **never tested** as a model constraint | ranks losers better than pred in 6 of 6 arm x L (AUC) but the cut loses money in 11 of 16 reads |
| burst / own-history cap, no adding to a losing fill | **lost a comparison** | AUC 0.42-0.60 with sign flips by window; adding to a loser is +6 to +20 c/$ outside ext (agrees with the report's cap round) |
| select-chosen gate on any of 52 state variables | **lost a comparison** | the best select cut never had an unseen CI above 0: select has no busy hours |

## 7. Testable hypotheses (for the improvement round)

1. **Delta-aware value model.** Recalibrate the 1 s model's output on (pred, settlement delta,
   busy-state) with a monotone fit on train + select + dev3 rows (dev3 brings the low-delta states),
   or retrain with delta-interacted targets. Predicted: removes the low-delta busy fills (the
   floor screen alone: +$61 to +$328/day on test3 run 1 + ext) and raises the value of high-delta
   quiet rows (realized 1 s exceeds pred by 2-4 c there). Test: re-simulate on test3 run 1 + ext, paired vs the frozen arm;
   then on fresh hours after prereg2.
2. **Delta floor (cheapest form of 1).** No order when delta < 3 c/bp (pick 3-6 on select + dev3).
   Predicted: zero effect in quiet hours, positive in busy hours. Test: re-simulation on all allowed
   windows with paired CI vs the frozen arms; falsified if the busy-hour gain does not survive the
   knock-on fills.
3. **Busy-window selection rule.** Any regime-dependent margin must be selected on a window that
   contains busy hours. Test: the same gate family picked on select alone vs on select + dev3, read
   on ext: the select pick should keep failing.
4. **The ext shift is more than delta.** In ext the model over-predicts in every delta bin; the
   candidate cause is faster rival repricing (competition lens). Test: add the Polymarket top-change
   rate or rival taker flow as a calibration input and check the ext residual.
5. **High-value compression -> conditional size.** At pred >= 6 c and delta >= 12 c/bp (quiet hours)
   realized value exceeds pred; size up there (e.g. 150 sh) and keep 60 elsewhere. Test: re-sim; the
   50 ms competition table says the high-delta fills of the taker are the ones rivals take first,
   so test under J = 0.05 too.
6. **Two-side coherence as a model constraint.** value_up + value_dn = -(spread + both fees) at the
   match, whatever the mark; pred + pred_other drifts from it. Train or post-process the two sides
   jointly (antisymmetric part as the score). Test: AUC and re-sim vs pred alone.
