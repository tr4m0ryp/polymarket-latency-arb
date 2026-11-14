# What triggers the BTC latency bots

Data: BTC Up/Down 5m and 15m fills (about 2 days), Binance BTCUSDT 1 s closes.
Bot set: every `latency_arb` row of `data/out/latency/wallets.csv` for the family.
Code: `research/trigger/` (`python3 research/trigger/run.py`). Tables
also as CSV under `data/out/latency/trigger/`.

Conventions: fill `ts` is the Polygon block timestamp, which lags the off-chain
match. S[t] is the Binance close of second [t, t+1). A move "j s before the fill"
is log(S[ts-j]/S[ts-j-1]). `fair` is P(Up) from driftless Brownian spot with the
trailing 300 s vol under the real settlement rule; `book` is the last YES print
before the fill; `edge` = fair value of the side taken minus price paid.

## Resolution source

Gamma description (5m and 15m): resolves Up if the Chainlink BTC/USD 60 s TWAP
data stream at the end of the range is >= the value at its start
(https://data.chain.link/streams/btc-usd-twap-60s-streams), "not according to
any other sources or spot markets". A Binance 60 s TWAP proxy reproduces
99.0% (5m) and 99.0% (15m) of outcomes. The Chainlink stream
itself needs Data Streams credentials, so a direct Binance-vs-Chainlink lead
was not measured. Structurally Binance leads the settlement number: a 60 s
TWAP lags spot by about 30 s on average, and Binance is one of the venues the
aggregate is built from. What was measured is that Binance leads the
Polymarket book by about 4 s (cross-correlation below).

## Answer

**btc-up-or-down-5m** (575 markets, 14 latency_arb wallets, BTC about $83,139, so 1 bp is about $8.31):
- **Trigger second:** the bots' side matches the Binance move of the single second 3 s before the fill's block time in 66.0% of USD (other takers 55.7%); seconds 6-8 back average 53.4%.
- **Speed:** bot flow peaks 3 s after the Binance second (cross-correlation), the YES last print peaks at 4 s. After a >= 3 bp jump (947 events) a bot fills on the jump side within 6 s in 78% of cases vs 52% at random seconds; median first fill 2 s (IQR 1-3 s).
- **Book staleness gates firing:** after a >= 2 bp 2 s move the top-5 bots fire in 18%-20% of seconds when the book already sits within 2 c of fair, 82% when fair is > 10 c ahead of the book (direction right 73%).
- **Edge per trade:** pooled bot taker fills pay 0.612 for a side worth 0.626 under the spot model, 1.40 c/share; realized 2.44 c per USD, 2 s markout 2.67 c per USD, median fill $13 (other takers: 0.08 c/share, -0.96 c per USD).
- **Edge sits in the triggered fills:** fills after an aligned 3 s move > 1 bp earn 10.7 c per USD on 20% of bot USD; fills against a > 1 bp move earn -10.4 c per USD.
- **Background rate:** with no move (|2 s move| < 0.25 bp) the top-5 bots still take in 33% of seconds at direction accuracy 55%; a >= 2 bp move lifts that to 56% at 71%.

**btc-up-or-down-15m** (383 markets, 14 latency_arb wallets, BTC about $85,325, so 1 bp is about $8.53):
- **Trigger second:** the bots' side matches the Binance move of the single second 3 s before the fill's block time in 70.8% of USD (other takers 56.6%); seconds 6-8 back average 56.8%.
- **Speed:** bot flow peaks 4 s after the Binance second (cross-correlation), the YES last print peaks at 4 s. After a >= 3 bp jump (1578 events) a bot fills on the jump side within 6 s in 66% of cases vs 25% at random seconds; median first fill 3 s (IQR 2-4 s).
- **Book staleness gates firing:** after a >= 2 bp 2 s move the top-5 bots fire in 15%-16% of seconds when the book already sits within 2 c of fair, 53% when fair is > 10 c ahead of the book (direction right 93%).
- **Edge per trade:** pooled bot taker fills pay 0.654 for a side worth 0.679 under the spot model, 2.47 c/share; realized 3.47 c per USD, 2 s markout 1.22 c per USD, median fill $12 (other takers: 0.90 c/share, 0.47 c per USD).
- **Edge sits in the triggered fills:** fills after an aligned 3 s move > 1 bp earn 8.2 c per USD on 24% of bot USD; fills against a > 1 bp move earn -4.6 c per USD.
- **Background rate:** with no move (|2 s move| < 0.25 bp) the top-5 bots still take in 9% of seconds at direction accuracy 58%; a >= 2 bp move lifts that to 37% at 86%.

## Decision rule (reconstructed)

1. Watch Binance BTCUSDT (or an equivalent fast feed) tick by tick.
2. When BTC moves, recompute P(Up) for the live market from the spot vs the
   strike, seconds left and short-term vol.
3. If the Polymarket ask on the side the move favours is still below that
   value (the book has not repriced), take it with a marketable buy, small
   size ($10-$30 a fill), and repeat on every further tick.
4. When spot reverses, buy the other side the same way. The top wallets
   never sell (taker buy share 1.00); they hold to resolution. Matched
   Up+Down pairs cost 0.95-1.08 per pair (decomposition table). For
   0xc53375ff94e96100f2b30a4b5775db35218d69a9 the pairs wash (-$204) and
   the residual exposure from the latest moves carries all of the +$20.9k;
   0x3048d65321be3497164cdfc2996f94f98a2e7537 gets $9.4k of its $20.7k from
   pairs at 0.99. In 15m, 0x32ed2e546b187ca15e2841edc82b22c713cf8ec3 and
   0xc2ad03f79ca3f3c17d8c7de2612ce0c89b7d40ed get about half their PnL from
   pairs bought at 0.95 with about 60% maker USD;
   0x3725d52f3c252e8374999cc8617292ea2608ad88 shares their fingerprint
   (same fill size, price paid and maker share) but its pairs wash.

The bots are not purely event-driven: they take continuously at a background
rate and lean with spot; a fresh move raises both the rate and the direction
accuracy.

The signal is the Binance move itself, not the cumulative move since open:
direction tracks the second about 3 s before the block time, the bots fire
more when the move is larger and much more when the book still lags fair, and
the edge per fill grows with the size of the aligned move. Copying fails
because the edge is a 2-4 s repricing window that a follower reading on-chain
fills sees only after it closed.

## btc-up-or-down-5m

### Who and what they pay (live taker fills)

| wallet | fills | usd | med_fill_usd | paid | fair_side | edge_c | edge_pos_share | pnl_per_usd_c | mo2_per_usd_c | mo10_per_usd_c |
|---|---|---|---|---|---|---|---|---|---|---|
| 0xc53375ff94e96100f2b30a4b5775db35218d69a9 | 19472 | 401,905.743 | 17.150 | 0.573 | 0.585 | 1.224 | 0.568 | 4.349 | 3.273 | 3.330 |
| 0x3048d65321be3497164cdfc2996f94f98a2e7537 | 33033 | 621,651.644 | 15.200 | 0.570 | 0.585 | 1.514 | 0.583 | 2.676 | 2.987 | 3.222 |
| 0x41e2e1ccf1e4940029af02259a31c6b89b9fa354 | 9089 | 255,362.510 | 17.782 | 0.687 | 0.705 | 1.888 | 0.643 | 2.144 | 1.926 | 2.481 |
| 0x0ca4e9d27ff826a109ecbf74754fb66b93f277a6 | 11395 | 262,618.715 | 18.900 | 0.572 | 0.582 | 0.977 | 0.549 | 2.480 | 3.351 | 3.102 |
| 0xd84403efd50b49a1d8a7181627e00307e6ea5908 | 7016 | 172,633.290 | 21.600 | 0.573 | 0.580 | 0.640 | 0.539 | 1.339 | 2.806 | 2.651 |
| 0x576b0696fd5a9225d66fd9500fd98f5be10b0cab | 3001 | 110,958.117 | 19.200 | 0.703 | 0.722 | 1.865 | 0.712 | 1.611 | 1.598 | 1.176 |
| all_bots | 104651 | 2,067,501.856 | 12.800 | 0.612 | 0.626 | 1.402 | 0.604 | 2.436 | 2.673 | 2.706 |
| other_takers | 768248 | 10,327,613.757 | 3.850 | 0.640 | 0.641 | 0.082 | 0.582 | -0.961 | -0.721 | -0.880 |

### Spot state at the fill (moves signed by the side taken; Brier of fair and of the prior print against the outcome, YES frame)

| wallet | r3_al_bp | move_open_al_bp | move_open_al_usd | secs_left_med | brier_fair | brier_book |
|---|---|---|---|---|---|---|
| 0xc53375ff94e96100f2b30a4b5775db35218d69a9 | 0.377 | 1.134 | 9.361 | 186.000 | 0.223 | 0.228 |
| 0x3048d65321be3497164cdfc2996f94f98a2e7537 | 0.262 | 1.014 | 8.380 | 190.000 | 0.222 | 0.225 |
| 0x41e2e1ccf1e4940029af02259a31c6b89b9fa354 | 0.222 | 2.348 | 19.447 | 147.000 | 0.176 | 0.172 |
| 0x0ca4e9d27ff826a109ecbf74754fb66b93f277a6 | 0.416 | 1.047 | 8.658 | 172.000 | 0.223 | 0.230 |
| 0xd84403efd50b49a1d8a7181627e00307e6ea5908 | 0.420 | 0.815 | 6.741 | 161.000 | 0.225 | 0.236 |
| 0x576b0696fd5a9225d66fd9500fd98f5be10b0cab | 0.696 | 3.455 | 28.587 | 201.000 | 0.157 | 0.157 |
| all_bots | 0.375 | 1.706 | 14.110 | 180.000 | 0.204 | 0.207 |
| other_takers | 0.152 | 2.231 | 18.486 | 168.000 | 0.134 | 0.133 |

### Which candidate trigger the side follows (USD share matching sign)

| wallet | r1 | r3 | r5 | r10 | r30 | move_since_open | move_vs_strike | fair_gt_book | fair_gt_paid | fresh10 |
|---|---|---|---|---|---|---|---|---|---|---|
| 0xc53375ff94e96100f2b30a4b5775db35218d69a9 | 0.586 | 0.677 | 0.643 | 0.615 | 0.593 | 0.629 | 0.660 | 0.627 | 0.568 | 0.615 |
| 0x3048d65321be3497164cdfc2996f94f98a2e7537 | 0.562 | 0.640 | 0.603 | 0.583 | 0.569 | 0.618 | 0.650 | 0.606 | 0.583 | 0.583 |
| 0x41e2e1ccf1e4940029af02259a31c6b89b9fa354 | 0.557 | 0.627 | 0.611 | 0.604 | 0.599 | 0.728 | 0.772 | 0.677 | 0.643 | 0.604 |
| 0x0ca4e9d27ff826a109ecbf74754fb66b93f277a6 | 0.585 | 0.690 | 0.661 | 0.625 | 0.593 | 0.635 | 0.657 | 0.626 | 0.549 | 0.625 |
| 0xd84403efd50b49a1d8a7181627e00307e6ea5908 | 0.571 | 0.672 | 0.643 | 0.619 | 0.584 | 0.606 | 0.648 | 0.634 | 0.539 | 0.619 |
| 0x576b0696fd5a9225d66fd9500fd98f5be10b0cab | 0.635 | 0.778 | 0.783 | 0.750 | 0.704 | 0.721 | 0.765 | 0.780 | 0.712 | 0.750 |
| all_bots | 0.581 | 0.678 | 0.655 | 0.631 | 0.610 | 0.660 | 0.691 | 0.656 | 0.604 | 0.631 |
| other_takers | 0.518 | 0.567 | 0.581 | 0.579 | 0.589 | 0.648 | 0.669 | 0.628 | 0.582 | 0.580 |

### Which Binance second the side follows (j = seconds before the fill's block ts)

| wallet | j=0 | j=1 | j=2 | j=3 | j=4 | j=5 | j=6 | j=7 | j=8 |
|---|---|---|---|---|---|---|---|---|---|
| 0xc53375ff94e96100f2b30a4b5775db35218d69a9 | 0.567 | 0.586 | 0.633 | 0.657 | 0.559 | 0.525 | 0.538 | 0.517 | 0.521 |
| 0x3048d65321be3497164cdfc2996f94f98a2e7537 | 0.551 | 0.562 | 0.606 | 0.622 | 0.539 | 0.519 | 0.527 | 0.518 | 0.520 |
| 0x41e2e1ccf1e4940029af02259a31c6b89b9fa354 | 0.551 | 0.557 | 0.591 | 0.607 | 0.545 | 0.534 | 0.550 | 0.529 | 0.546 |
| 0x0ca4e9d27ff826a109ecbf74754fb66b93f277a6 | 0.566 | 0.585 | 0.639 | 0.674 | 0.572 | 0.537 | 0.519 | 0.525 | 0.526 |
| 0xd84403efd50b49a1d8a7181627e00307e6ea5908 | 0.563 | 0.571 | 0.633 | 0.654 | 0.560 | 0.522 | 0.543 | 0.516 | 0.533 |
| 0x576b0696fd5a9225d66fd9500fd98f5be10b0cab | 0.547 | 0.635 | 0.622 | 0.769 | 0.684 | 0.584 | 0.547 | 0.549 | 0.540 |
| all_bots | 0.559 | 0.581 | 0.622 | 0.660 | 0.578 | 0.536 | 0.540 | 0.532 | 0.530 |
| other_takers | 0.508 | 0.518 | 0.547 | 0.557 | 0.556 | 0.535 | 0.535 | 0.526 | 0.527 |

### Cross-correlation, signed taker USD at t+k vs Binance 1 s return at t

| series | k=-2 | k=-1 | k=0 | k=1 | k=2 | k=3 | k=4 | k=5 | k=6 | k=7 | k=8 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| all_bots | 0.010 | 0.025 | 0.024 | 0.036 | 0.078 | 0.120 | 0.049 | 0.023 | 0.017 | 0.024 | 0.021 |
| other_takers | 0.006 | 0.004 | 0.002 | 0.012 | 0.022 | 0.056 | 0.049 | 0.025 | 0.019 | 0.018 | 0.016 |
| 0xc53375ff94e96100f2b30a4b5775db35218d69a9 | 0.009 | 0.018 | 0.023 | 0.028 | 0.060 | 0.084 | 0.026 | 0.007 | 0.007 | 0.011 | 0.014 |
| 0x3048d65321be3497164cdfc2996f94f98a2e7537 | 0.004 | 0.017 | 0.018 | 0.023 | 0.059 | 0.068 | 0.019 | 0.010 | 0.007 | 0.014 | 0.013 |
| 0x41e2e1ccf1e4940029af02259a31c6b89b9fa354 | 0.005 | 0.010 | 0.009 | 0.012 | 0.025 | 0.027 | 0.016 | 0.014 | 0.015 | 0.012 | 0.013 |
| book_last_print | 0.019 | 0.020 | 0.033 | 0.040 | 0.056 | 0.128 | 0.264 | 0.157 | 0.039 | 0.003 | -0.001 |

### Event study: mean jump-aligned USD / book change at t+k after a >= 3 bp 2 s jump

{'n_events': 947, 'jump_bp_med': 3.568585590262674, 'hit_within_6s': 0.7793030623020063, 'hit_within_6s_random': 0.5174234424498416, 'first_fill_lag_median': 2.0, 'first_fill_lag_p25': 1.0, 'first_fill_lag_p75': 3.0}

| lag_s | all_bots | other_takers | book_last_print |
|---|---|---|---|
| -2 | -1.099 | -2.141 | 0.000 |
| -1 | 0.730 | 12.192 | 0.001 |
| 0 | 3.100 | -3.399 | 0.002 |
| 1 | 4.214 | 11.302 | 0.003 |
| 2 | 16.116 | 18.928 | 0.006 |
| 3 | 18.439 | 62.093 | 0.025 |
| 4 | 7.575 | 49.422 | 0.042 |
| 5 | 3.400 | 12.076 | 0.021 |
| 6 | 3.335 | 29.633 | 0.007 |
| 7 | 3.896 | 6.096 | -0.000 |
| 8 | 2.951 | 3.374 | 0.001 |
| 9 | 3.829 | 10.096 | -0.002 |
| 10 | 0.900 | 0.044 | -0.000 |

### Fire curve (top 5 bots): fire rate in [u+1, u+3] by |2 s move| known at u

| m_bin | seconds | fire_rate | dir_accuracy |
|---|---|---|---|
| [0.0, 0.25) | 153294 | 0.334 | 0.551 |
| [0.25, 0.5) | 12106 | 0.435 | 0.671 |
| [0.5, 1.0) | 17639 | 0.456 | 0.670 |
| [1.0, 2.0) | 15306 | 0.500 | 0.686 |
| [2.0, 3.0) | 4293 | 0.531 | 0.715 |
| [3.0, 5.0) | 2057 | 0.546 | 0.675 |
| [5.0, 8.0) | 455 | 0.563 | 0.660 |
| [8.0, 1000000000.0) | 111 | 0.505 | 0.625 |

### Gap curve: |move| >= 2 bp, by fair - book in the move's direction

| gap_bin | seconds | fire_rate | dir_accuracy |
|---|---|---|---|
| (-1.0, -0.02] | 352 | 0.560 | 0.589 |
| (-0.02, 0.0] | 915 | 0.202 | 0.686 |
| (0.0, 0.02] | 1240 | 0.180 | 0.619 |
| (0.02, 0.05] | 919 | 0.478 | 0.658 |
| (0.05, 0.1] | 1439 | 0.694 | 0.703 |
| (0.1, 1.0] | 2051 | 0.816 | 0.729 |

### Edge by aligned 3 s move at the fill (all bots pooled)

| bin | fills | usd | pnl_per_usd_c | mo2_per_usd_c | mo10_per_usd_c | usd_share | edge_c |
|---|---|---|---|---|---|---|---|
| (-1000000000.0, -1.0] | 6565 | 140,080.20 | -10.42 | -13.38 | -14.21 | 0.07 | -5.67 |
| (-1.0, 0.0] | 41994 | 841,127.64 | -1.06 | 0.14 | -0.18 | 0.41 | 0.87 |
| (0.0, 0.5] | 23019 | 456,540.91 | 2.94 | 2.46 | 3.02 | 0.22 | -0.26 |
| (0.5, 1.0] | 11134 | 217,480.57 | 7.59 | 5.96 | 6.60 | 0.11 | 2.04 |
| (1.0, 2.0] | 13176 | 246,177.44 | 8.75 | 9.47 | 9.61 | 0.12 | 4.83 |
| (2.0, 4.0] | 6970 | 131,520.79 | 12.65 | 14.24 | 14.63 | 0.06 | 8.12 |
| (4.0, 1000000000.0] | 1793 | 34,574.30 | 16.66 | 19.13 | 18.30 | 0.02 | 10.90 |

### PnL decomposition (all fills): locked Up+Down pairs vs residual directional

| wallet | markets | pnl | locked_pairs | residual_directional | pair_cost | paired_share | maker_usd_share | win_rate_mkts |
|---|---|---|---|---|---|---|---|---|
| 0xc53375ff94e96100f2b30a4b5775db35218d69a9 | 571 | 20,856.76 | -203.59 | 21,060.35 | 1.00 | 0.85 | 0.13 | 0.61 |
| 0x3048d65321be3497164cdfc2996f94f98a2e7537 | 571 | 20,746.28 | 9,395.89 | 11,350.39 | 0.99 | 0.90 | 0.16 | 0.58 |
| 0x41e2e1ccf1e4940029af02259a31c6b89b9fa354 | 575 | 7,906.48 | 1,697.69 | 6,208.80 | 1.00 | 0.95 | 0.50 | 0.59 |
| 0x0ca4e9d27ff826a109ecbf74754fb66b93f277a6 | 569 | 7,777.20 | -1,287.76 | 9,064.96 | 1.01 | 0.81 | 0.12 | 0.52 |
| 0xd84403efd50b49a1d8a7181627e00307e6ea5908 | 561 | 3,893.68 | -1,928.06 | 5,821.74 | 1.01 | 0.78 | 0.12 | 0.56 |
| 0x576b0696fd5a9225d66fd9500fd98f5be10b0cab | 575 | 1,787.55 | 10,708.87 | -8,921.32 | 0.90 | 0.57 | 0.33 | 0.51 |

## btc-up-or-down-15m

### Who and what they pay (live taker fills)

| wallet | fills | usd | med_fill_usd | paid | fair_side | edge_c | edge_pos_share | pnl_per_usd_c | mo2_per_usd_c | mo10_per_usd_c |
|---|---|---|---|---|---|---|---|---|---|---|
| 0x32ed2e546b187ca15e2841edc82b22c713cf8ec3 | 975 | 59,579.644 | 29.950 | 0.627 | 0.644 | 1.693 | 0.600 | 9.980 | 1.797 | 2.415 |
| 0x3725d52f3c252e8374999cc8617292ea2608ad88 | 934 | 61,475.743 | 36.406 | 0.630 | 0.651 | 2.047 | 0.623 | 7.921 | 0.533 | -0.559 |
| 0xb55fa1296e6ec55d0ce53d93b9237389f11764d4 | 6368 | 320,538.344 | 22.325 | 0.646 | 0.667 | 2.034 | 0.629 | 2.614 | 0.781 | 0.498 |
| 0xc2ad03f79ca3f3c17d8c7de2612ce0c89b7d40ed | 839 | 52,783.885 | 28.800 | 0.626 | 0.646 | 2.021 | 0.605 | 9.636 | 1.001 | 0.950 |
| 0x21f4c1a1be34a39a7bc20985df4b7e5a39fb691d | 12201 | 240,457.165 | 16.990 | 0.699 | 0.731 | 3.150 | 0.729 | 1.285 | 0.585 | 0.798 |
| 0x41e2e1ccf1e4940029af02259a31c6b89b9fa354 | 8622 | 94,348.514 | 8.400 | 0.649 | 0.680 | 3.138 | 0.691 | 2.465 | 1.842 | 2.414 |
| all_bots | 51573 | 1,295,543.961 | 12.000 | 0.654 | 0.679 | 2.473 | 0.655 | 3.465 | 1.223 | 1.386 |
| other_takers | 373951 | 5,760,840.479 | 4.150 | 0.654 | 0.663 | 0.896 | 0.622 | 0.471 | 0.085 | 0.221 |

### Spot state at the fill (moves signed by the side taken; Brier of fair and of the prior print against the outcome, YES frame)

| wallet | r3_al_bp | move_open_al_bp | move_open_al_usd | secs_left_med | brier_fair | brier_book |
|---|---|---|---|---|---|---|
| 0x32ed2e546b187ca15e2841edc82b22c713cf8ec3 | 0.501 | 2.748 | 23.267 | 319.000 | 0.252 | 0.239 |
| 0x3725d52f3c252e8374999cc8617292ea2608ad88 | 0.449 | 2.299 | 19.529 | 305.500 | 0.232 | 0.217 |
| 0xb55fa1296e6ec55d0ce53d93b9237389f11764d4 | 0.553 | 5.356 | 44.869 | 477.000 | 0.205 | 0.208 |
| 0xc2ad03f79ca3f3c17d8c7de2612ce0c89b7d40ed | 0.548 | 2.163 | 18.316 | 315.000 | 0.258 | 0.245 |
| 0x21f4c1a1be34a39a7bc20985df4b7e5a39fb691d | 0.700 | 7.490 | 63.264 | 553.000 | 0.167 | 0.165 |
| 0x41e2e1ccf1e4940029af02259a31c6b89b9fa354 | 0.318 | 3.830 | 32.224 | 316.000 | 0.173 | 0.171 |
| all_bots | 0.538 | 5.355 | 45.090 | 442.000 | 0.188 | 0.185 |
| other_takers | 0.146 | 4.469 | 37.720 | 331.000 | 0.179 | 0.160 |

### Which candidate trigger the side follows (USD share matching sign)

| wallet | r1 | r3 | r5 | r10 | r30 | move_since_open | move_vs_strike | fair_gt_book | fair_gt_paid | fresh10 |
|---|---|---|---|---|---|---|---|---|---|---|
| 0x32ed2e546b187ca15e2841edc82b22c713cf8ec3 | 0.559 | 0.753 | 0.801 | 0.750 | 0.683 | 0.667 | 0.675 | 0.711 | 0.600 | 0.751 |
| 0x3725d52f3c252e8374999cc8617292ea2608ad88 | 0.521 | 0.710 | 0.772 | 0.720 | 0.667 | 0.677 | 0.695 | 0.755 | 0.623 | 0.727 |
| 0xb55fa1296e6ec55d0ce53d93b9237389f11764d4 | 0.604 | 0.718 | 0.791 | 0.790 | 0.762 | 0.782 | 0.797 | 0.747 | 0.629 | 0.790 |
| 0xc2ad03f79ca3f3c17d8c7de2612ce0c89b7d40ed | 0.531 | 0.760 | 0.792 | 0.768 | 0.699 | 0.680 | 0.682 | 0.710 | 0.605 | 0.766 |
| 0x21f4c1a1be34a39a7bc20985df4b7e5a39fb691d | 0.587 | 0.784 | 0.831 | 0.818 | 0.796 | 0.809 | 0.814 | 0.808 | 0.729 | 0.819 |
| 0x41e2e1ccf1e4940029af02259a31c6b89b9fa354 | 0.573 | 0.677 | 0.667 | 0.640 | 0.605 | 0.713 | 0.732 | 0.690 | 0.691 | 0.640 |
| all_bots | 0.570 | 0.725 | 0.762 | 0.743 | 0.698 | 0.749 | 0.758 | 0.729 | 0.655 | 0.744 |
| other_takers | 0.519 | 0.568 | 0.575 | 0.573 | 0.569 | 0.676 | 0.684 | 0.649 | 0.622 | 0.575 |

### Which Binance second the side follows (j = seconds before the fill's block ts)

| wallet | j=0 | j=1 | j=2 | j=3 | j=4 | j=5 | j=6 | j=7 | j=8 |
|---|---|---|---|---|---|---|---|---|---|
| 0x32ed2e546b187ca15e2841edc82b22c713cf8ec3 | 0.561 | 0.559 | 0.691 | 0.708 | 0.747 | 0.580 | 0.540 | 0.525 | 0.531 |
| 0x3725d52f3c252e8374999cc8617292ea2608ad88 | 0.565 | 0.521 | 0.637 | 0.699 | 0.689 | 0.587 | 0.577 | 0.518 | 0.573 |
| 0xb55fa1296e6ec55d0ce53d93b9237389f11764d4 | 0.565 | 0.604 | 0.632 | 0.704 | 0.735 | 0.663 | 0.634 | 0.569 | 0.599 |
| 0xc2ad03f79ca3f3c17d8c7de2612ce0c89b7d40ed | 0.584 | 0.531 | 0.664 | 0.710 | 0.721 | 0.613 | 0.509 | 0.532 | 0.558 |
| 0x21f4c1a1be34a39a7bc20985df4b7e5a39fb691d | 0.573 | 0.587 | 0.678 | 0.774 | 0.722 | 0.642 | 0.622 | 0.596 | 0.598 |
| 0x41e2e1ccf1e4940029af02259a31c6b89b9fa354 | 0.566 | 0.573 | 0.625 | 0.660 | 0.594 | 0.561 | 0.547 | 0.535 | 0.538 |
| all_bots | 0.559 | 0.570 | 0.648 | 0.708 | 0.692 | 0.611 | 0.591 | 0.547 | 0.566 |
| other_takers | 0.520 | 0.519 | 0.543 | 0.566 | 0.556 | 0.520 | 0.525 | 0.513 | 0.526 |

### Cross-correlation, signed taker USD at t+k vs Binance 1 s return at t

| series | k=-2 | k=-1 | k=0 | k=1 | k=2 | k=3 | k=4 | k=5 | k=6 | k=7 | k=8 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| all_bots | 0.005 | 0.005 | 0.009 | 0.021 | 0.047 | 0.094 | 0.103 | 0.072 | 0.038 | 0.030 | 0.020 |
| other_takers | 0.000 | 0.002 | 0.004 | 0.003 | 0.015 | 0.042 | 0.023 | 0.015 | 0.010 | 0.006 | 0.007 |
| 0x32ed2e546b187ca15e2841edc82b22c713cf8ec3 | -0.001 | 0.004 | 0.001 | 0.004 | 0.007 | 0.022 | 0.024 | 0.013 | 0.007 | 0.001 | 0.002 |
| 0x3725d52f3c252e8374999cc8617292ea2608ad88 | -0.001 | 0.002 | 0.002 | 0.004 | 0.010 | 0.018 | 0.024 | 0.009 | 0.018 | 0.004 | 0.006 |
| 0xb55fa1296e6ec55d0ce53d93b9237389f11764d4 | 0.002 | 0.000 | 0.001 | 0.017 | 0.017 | 0.039 | 0.069 | 0.073 | 0.022 | 0.020 | 0.015 |
| book_last_print | 0.017 | 0.020 | 0.029 | 0.034 | 0.049 | 0.113 | 0.242 | 0.179 | 0.072 | 0.031 | 0.014 |

### Event study: mean jump-aligned USD / book change at t+k after a >= 3 bp 2 s jump

{'n_events': 1578, 'jump_bp_med': 3.543679919286694, 'hit_within_6s': 0.6634980988593155, 'hit_within_6s_random': 0.24714828897338403, 'first_fill_lag_median': 3.0, 'first_fill_lag_p25': 2.0, 'first_fill_lag_p75': 4.0}

| lag_s | all_bots | other_takers | book_last_print |
|---|---|---|---|
| -2 | 0.688 | -2.446 | 0.001 |
| -1 | 0.377 | 2.014 | 0.000 |
| 0 | 1.363 | -0.530 | 0.000 |
| 1 | 1.853 | -0.729 | 0.002 |
| 2 | 8.308 | 8.786 | 0.002 |
| 3 | 17.161 | 23.673 | 0.012 |
| 4 | 18.996 | 9.583 | 0.023 |
| 5 | 9.921 | 10.096 | 0.016 |
| 6 | 8.400 | 5.767 | 0.006 |
| 7 | 4.698 | 5.839 | 0.003 |
| 8 | 3.800 | 6.227 | 0.001 |
| 9 | 5.803 | -1.632 | 0.000 |
| 10 | 2.070 | -0.438 | -0.001 |

### Fire curve (top 5 bots): fire rate in [u+1, u+3] by |2 s move| known at u

| m_bin | seconds | fire_rate | dir_accuracy |
|---|---|---|---|
| [0.0, 0.25) | 284334 | 0.092 | 0.585 |
| [0.25, 0.5) | 19687 | 0.190 | 0.807 |
| [0.5, 1.0) | 28627 | 0.231 | 0.826 |
| [1.0, 2.0) | 23772 | 0.277 | 0.850 |
| [2.0, 3.0) | 6465 | 0.318 | 0.859 |
| [3.0, 5.0) | 2838 | 0.370 | 0.868 |
| [5.0, 8.0) | 595 | 0.368 | 0.872 |
| [8.0, 1000000000.0) | 137 | 0.336 | 0.935 |

### Gap curve: |move| >= 2 bp, by fair - book in the move's direction

| gap_bin | seconds | fire_rate | dir_accuracy |
|---|---|---|---|
| (-1.0, -0.02] | 1004 | 0.279 | 0.729 |
| (-0.02, 0.0] | 1371 | 0.157 | 0.814 |
| (0.0, 0.02] | 1749 | 0.153 | 0.749 |
| (0.02, 0.05] | 1592 | 0.352 | 0.824 |
| (0.05, 0.1] | 2208 | 0.423 | 0.893 |
| (0.1, 1.0] | 2111 | 0.529 | 0.930 |

### Edge by aligned 3 s move at the fill (all bots pooled)

| bin | fills | usd | pnl_per_usd_c | mo2_per_usd_c | mo10_per_usd_c | usd_share | edge_c |
|---|---|---|---|---|---|---|---|
| (-1000000000.0, -1.0] | 2509 | 69,850.35 | -4.56 | -7.22 | -9.55 | 0.05 | -2.87 |
| (-1.0, 0.0] | 19358 | 484,250.82 | 0.73 | -0.58 | -0.37 | 0.37 | 1.79 |
| (0.0, 0.5] | 11496 | 285,530.43 | 1.42 | 1.16 | 1.07 | 0.22 | 1.89 |
| (0.5, 1.0] | 5994 | 149,376.50 | 10.37 | 2.81 | 3.83 | 0.12 | 3.39 |
| (1.0, 2.0] | 6997 | 171,390.73 | 6.11 | 4.19 | 4.42 | 0.13 | 4.12 |
| (2.0, 4.0] | 4004 | 99,419.49 | 13.35 | 6.32 | 6.98 | 0.08 | 5.68 |
| (4.0, 1000000000.0] | 1215 | 35,725.64 | 3.61 | 7.61 | 8.68 | 0.03 | 6.19 |

### PnL decomposition (all fills): locked Up+Down pairs vs residual directional

| wallet | markets | pnl | locked_pairs | residual_directional | pair_cost | paired_share | maker_usd_share | win_rate_mkts |
|---|---|---|---|---|---|---|---|---|
| 0x32ed2e546b187ca15e2841edc82b22c713cf8ec3 | 349 | 9,804.60 | 5,116.52 | 4,688.08 | 0.95 | 0.68 | 0.60 | 0.52 |
| 0x3725d52f3c252e8374999cc8617292ea2608ad88 | 332 | 9,687.15 | 473.02 | 9,214.13 | 1.00 | 0.68 | 0.60 | 0.51 |
| 0xb55fa1296e6ec55d0ce53d93b9237389f11764d4 | 251 | 8,943.58 | -7,173.55 | 16,117.13 | 1.03 | 0.83 | 0.05 | 0.62 |
| 0xc2ad03f79ca3f3c17d8c7de2612ce0c89b7d40ed | 339 | 8,583.85 | 4,678.80 | 3,905.05 | 0.95 | 0.65 | 0.61 | 0.50 |
| 0x21f4c1a1be34a39a7bc20985df4b7e5a39fb691d | 347 | 3,806.23 | -16,676.72 | 20,482.95 | 1.08 | 0.78 | 0.27 | 0.61 |
| 0x41e2e1ccf1e4940029af02259a31c6b89b9fa354 | 381 | 2,325.59 | 2,223.69 | 101.90 | 0.98 | 0.93 | 0.00 | 0.64 |
