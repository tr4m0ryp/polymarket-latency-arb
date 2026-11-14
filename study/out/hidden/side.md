# Side models, ms-attributed fills (hours with perp data: 24; test = last 8 h)


## Leader A: 3026 fills, no-move share 0.762

| features | AUC all | acc all | AUC no-move | acc no-move |
|---|---|---|---|---|
| forensic (block time, 1 s closes) | 0.571 | 0.549 | 0.556 | 0.527 |
| spot trades, ms-aligned | 0.651 | 0.575 | 0.606 | 0.538 |
| + spot book and taker flow | 0.866 | 0.772 | 0.878 | 0.781 |
| perp book only | 0.922 | 0.836 | 0.930 | 0.837 |
| Polymarket only (book, flow, state) | 0.841 | 0.749 | 0.835 | 0.737 |
| own burst state (gap, last side) | 0.533 | 0.515 | 0.518 | 0.515 |
| peers (other leader's fills) | 0.876 | 0.755 | 0.878 | 0.758 |
| perp + spot + Polymarket | 0.954 | 0.876 | 0.956 | 0.881 |
| perp + spot + own burst state | 0.926 | 0.840 | 0.936 | 0.855 |
| all but peers | 0.956 | 0.890 | 0.958 | 0.878 |
| everything | 0.980 | 0.923 | 0.984 | 0.936 |

single rules (sign of feature = side), test hours, accuracy / coverage:

| feature | all | no-move |
|---|---|---|
| rule | 0.837 / 0.82 | 0.843 / 0.82 |
| blk_r3 | 0.605 / 0.66 | 0.601 / 0.57 |
| spot_r3.0 | 0.579 / 0.65 | 0.601 / 0.54 |
| spot_r0.5 | 0.664 / 0.41 | 0.607 / 0.36 |
| perp_mid_trig | 0.984 / 0.13 | 1.000 / 0.10 |
| perp_micro_trig | 0.799 / 0.93 | 0.806 / 0.93 |
| perp_micro_wide | 0.809 / 0.98 | 0.819 / 0.98 |
| perp_micro_pre | 0.658 / 0.99 | 0.669 / 0.99 |
| perp_micro_post | 0.507 / 0.96 | 0.509 / 0.95 |
| spot_micro_post | 0.551 / 0.80 | 0.553 / 0.78 |
| perp_imb_chg | 0.742 / 0.93 | 0.764 / 0.93 |
| spot_micro_trig | 0.763 / 0.77 | 0.770 / 0.75 |
| spot_flow_trig | 0.770 / 0.37 | 0.738 / 0.34 |
| book_r0.5 | 0.698 / 0.74 | 0.723 / 0.72 |
| flow0.5_other | 0.544 / 0.87 | 0.549 / 0.84 |
| flow0_B | 0.990 / 0.31 | 0.996 / 0.31 |

## Leader B: 5771 fills, no-move share 0.815

| features | AUC all | acc all | AUC no-move | acc no-move |
|---|---|---|---|---|
| forensic (block time, 1 s closes) | 0.552 | 0.530 | 0.542 | 0.520 |
| spot trades, ms-aligned | 0.576 | 0.559 | 0.495 | 0.523 |
| + spot book and taker flow | 0.843 | 0.746 | 0.844 | 0.744 |
| perp book only | 0.912 | 0.831 | 0.914 | 0.818 |
| Polymarket only (book, flow, state) | 0.703 | 0.646 | 0.682 | 0.626 |
| own burst state (gap, last side) | 0.563 | 0.537 | 0.561 | 0.533 |
| peers (other leader's fills) | 0.591 | 0.555 | 0.586 | 0.564 |
| perp + spot + Polymarket | 0.942 | 0.872 | 0.942 | 0.867 |
| perp + spot + own burst state | 0.924 | 0.837 | 0.933 | 0.844 |
| all but peers | 0.942 | 0.866 | 0.944 | 0.865 |
| everything | 0.946 | 0.870 | 0.947 | 0.876 |

single rules (sign of feature = side), test hours, accuracy / coverage:

| feature | all | no-move |
|---|---|---|
| rule | 0.805 / 0.81 | 0.807 / 0.81 |
| blk_r3 | 0.544 / 0.62 | 0.538 / 0.55 |
| spot_r3.0 | 0.552 / 0.60 | 0.570 / 0.50 |
| spot_r0.5 | 0.628 / 0.40 | 0.583 / 0.35 |
| perp_mid_trig | 0.979 / 0.08 | 1.000 / 0.06 |
| perp_micro_trig | 0.779 / 0.92 | 0.785 / 0.91 |
| perp_micro_wide | 0.795 / 0.98 | 0.808 / 0.98 |
| perp_micro_pre | 0.626 / 0.99 | 0.646 / 0.99 |
| perp_micro_post | 0.503 / 0.94 | 0.488 / 0.93 |
| spot_micro_post | 0.565 / 0.78 | 0.559 / 0.76 |
| perp_imb_chg | 0.741 / 0.92 | 0.754 / 0.91 |
| spot_micro_trig | 0.744 / 0.75 | 0.750 / 0.74 |
| spot_flow_trig | 0.698 / 0.34 | 0.670 / 0.30 |
| book_r0.5 | 0.569 / 0.54 | 0.592 / 0.50 |
| flow0.5_other | 0.525 / 0.87 | 0.534 / 0.84 |
| flow0_B | 1.000 / 0.00 | 1.000 / 0.00 |

## Side accuracy by |perp microprice change| in the trigger window, no-move fills, all hours

| change (bp) | A | B |
|---|---|---|
| (-1.0, 1e-06] | 0.278 (n 363) | 0.252 (n 803) |
| (1e-06, 0.0001] | 0.597 (n 566) | 0.590 (n 1216) |
| (0.0001, 0.0005] | 0.780 (n 373) | 0.845 (n 845) |
| (0.0005, 0.002] | 0.943 (n 547) | 0.951 (n 1188) |
| (0.002, 0.01] | 0.987 (n 234) | 0.986 (n 357) |
| (0.01, 100.0] | 0.996 (n 224) | 0.990 (n 292) |
