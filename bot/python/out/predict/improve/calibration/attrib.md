# Over-prediction and drift attribution, v1_L0


## Shift attribution, select mapped onto train marginals

| group | fire_share_pct | mean_pred_fire_c | d_fire_share_pct | d_pred_fire_c |
|---|---|---|---|---|
| (as observed) | 0.58 | 6.24 | 0.00 | 0.00 |
| (train reference) | 1.02 | 7.31 | 0.45 | 1.07 |
| perp microprice change | 0.58 | 6.23 | 0.00 | -0.00 |
| perp queue / imbalance | 0.58 | 6.24 | -0.00 | -0.00 |
| perp OFI (CKS) | 0.59 | 6.25 | 0.01 | 0.01 |
| perp depletion / time-to-depletion | 0.60 | 6.33 | 0.02 | 0.10 |
| perp intensities / last tick | 0.58 | 6.18 | -0.00 | -0.06 |
| spot book | 0.82 | 7.21 | 0.25 | 0.97 |
| spot trades | 0.58 | 6.10 | 0.00 | -0.14 |
| perp-spot basis | 0.58 | 6.24 | -0.00 | 0.00 |
| Polymarket state | 0.58 | 6.23 | -0.00 | -0.00 |
| settlement scale (sigma, zs, delta) | 0.57 | 6.10 | -0.01 | -0.14 |
| fair value (pzm, gap) | 0.52 | 5.39 | -0.06 | -0.85 |
| delta-scaled Binance | 0.61 | 6.43 | 0.03 | 0.19 |
| ALL | 0.80 | 6.24 | 0.22 | 0.00 |


## Shift attribution, dev3 mapped onto train marginals

| group | fire_share_pct | mean_pred_fire_c | d_fire_share_pct | d_pred_fire_c |
|---|---|---|---|---|
| (as observed) | 0.79 | 6.99 | 0.00 | 0.00 |
| (train reference) | 1.02 | 7.31 | 0.23 | 0.31 |
| perp microprice change | 0.80 | 7.00 | 0.01 | 0.00 |
| perp queue / imbalance | 0.79 | 6.99 | 0.00 | -0.00 |
| perp OFI (CKS) | 0.79 | 7.00 | -0.01 | 0.00 |
| perp depletion / time-to-depletion | 0.81 | 7.05 | 0.02 | 0.05 |
| perp intensities / last tick | 0.77 | 6.89 | -0.03 | -0.10 |
| spot book | 0.88 | 7.37 | 0.09 | 0.38 |
| spot trades | 0.79 | 6.85 | -0.01 | -0.14 |
| perp-spot basis | 0.79 | 6.99 | -0.00 | 0.00 |
| Polymarket state | 0.81 | 7.08 | 0.01 | 0.09 |
| settlement scale (sigma, zs, delta) | 0.75 | 6.64 | -0.05 | -0.35 |
| fair value (pzm, gap) | 0.80 | 6.96 | 0.01 | -0.03 |
| delta-scaled Binance | 0.79 | 6.98 | 0.00 | -0.01 |
| ALL | 0.84 | 6.82 | 0.05 | -0.17 |


## Shift attribution, final mapped onto train marginals

| group | fire_share_pct | mean_pred_fire_c | d_fire_share_pct | d_pred_fire_c |
|---|---|---|---|---|
| (as observed) | 0.67 | 6.65 | 0.00 | 0.00 |
| (train reference) | 1.02 | 7.31 | 0.36 | 0.66 |
| perp microprice change | 0.67 | 6.64 | 0.00 | -0.00 |
| perp queue / imbalance | 0.67 | 6.65 | 0.00 | -0.00 |
| perp OFI (CKS) | 0.68 | 6.66 | 0.01 | 0.01 |
| perp depletion / time-to-depletion | 0.69 | 6.80 | 0.02 | 0.15 |
| perp intensities / last tick | 0.64 | 6.32 | -0.03 | -0.33 |
| spot book | 0.93 | 8.01 | 0.26 | 1.36 |
| spot trades | 0.65 | 6.58 | -0.02 | -0.06 |
| perp-spot basis | 0.66 | 6.65 | -0.00 | 0.00 |
| Polymarket state | 0.67 | 6.60 | 0.00 | -0.04 |
| settlement scale (sigma, zs, delta) | 0.66 | 6.57 | -0.01 | -0.07 |
| fair value (pzm, gap) | 0.66 | 6.45 | -0.01 | -0.20 |
| delta-scaled Binance | 0.72 | 6.86 | 0.06 | 0.21 |
| ALL | 0.93 | 7.40 | 0.27 | 0.75 |


## Shift attribution, ext mapped onto train marginals

| group | fire_share_pct | mean_pred_fire_c | d_fire_share_pct | d_pred_fire_c |
|---|---|---|---|---|
| (as observed) | 0.83 | 4.82 | 0.00 | 0.00 |
| (train reference) | 1.02 | 7.31 | 0.20 | 2.48 |
| perp microprice change | 0.78 | 4.72 | -0.05 | -0.11 |
| perp queue / imbalance | 0.83 | 4.83 | 0.00 | 0.00 |
| perp OFI (CKS) | 0.81 | 4.73 | -0.02 | -0.09 |
| perp depletion / time-to-depletion | 0.81 | 4.59 | -0.02 | -0.24 |
| perp intensities / last tick | 1.03 | 5.40 | 0.20 | 0.57 |
| spot book | 0.42 | 3.00 | -0.41 | -1.83 |
| spot trades | 0.82 | 4.75 | -0.01 | -0.08 |
| perp-spot basis | 0.80 | 4.80 | -0.03 | -0.02 |
| Polymarket state | 0.80 | 4.71 | -0.03 | -0.11 |
| settlement scale (sigma, zs, delta) | 1.01 | 5.27 | 0.18 | 0.44 |
| fair value (pzm, gap) | 0.91 | 4.95 | 0.08 | 0.13 |
| delta-scaled Binance | 0.91 | 5.06 | 0.08 | 0.24 |
| ALL | 0.54 | 2.97 | -0.29 | -1.86 |


## Importance by regime (pooled dev3 + final + ext, both sides, sampled rows)

| regime | group | rows | top2_c | drop_c | gap_fire_c | d_gap_c |
|---|---|---|---|---|---|---|
| quiet | (none) | 39513 | 17.19 | 0.00 | 3.28 | 0.00 |
| quiet | perp microprice change | 39513 | 17.84 | -0.65 | 4.22 | 0.94 |
| quiet | perp queue / imbalance | 39513 | 17.19 | 0.00 | 3.28 | -0.00 |
| quiet | perp OFI (CKS) | 39513 | 17.40 | -0.21 | 3.94 | 0.66 |
| quiet | perp depletion / time-to-depletion | 39513 | 17.04 | 0.15 | 4.97 | 1.69 |
| quiet | perp intensities / last tick | 39513 | 17.71 | -0.52 | 2.67 | -0.61 |
| quiet | spot book | 39513 | 9.16 | 8.03 | -0.69 | -3.97 |
| quiet | spot trades | 39513 | 16.93 | 0.26 | 3.28 | 0.00 |
| quiet | perp-spot basis | 39513 | 17.29 | -0.10 | 3.58 | 0.29 |
| quiet | Polymarket state | 39513 | 13.26 | 3.93 | 1.40 | -1.89 |
| quiet | settlement scale (sigma, zs, delta) | 39513 | 18.11 | -0.92 | 3.09 | -0.19 |
| quiet | fair value (pzm, gap) | 39513 | 17.56 | -0.37 | 3.76 | 0.48 |
| quiet | delta-scaled Binance | 39513 | 17.51 | -0.32 | 4.95 | 1.67 |
| busy | (none) | 98604 | 11.00 | 0.00 | 1.11 | 0.00 |
| busy | perp microprice change | 98604 | 11.12 | -0.11 | 1.33 | 0.22 |
| busy | perp queue / imbalance | 98604 | 11.00 | 0.00 | 1.13 | 0.01 |
| busy | perp OFI (CKS) | 98604 | 10.79 | 0.22 | 0.87 | -0.25 |
| busy | perp depletion / time-to-depletion | 98604 | 10.96 | 0.04 | 0.66 | -0.45 |
| busy | perp intensities / last tick | 98604 | 10.37 | 0.64 | 0.13 | -0.98 |
| busy | spot book | 98604 | 4.82 | 6.18 | -2.67 | -3.78 |
| busy | spot trades | 98604 | 11.34 | -0.34 | 0.50 | -0.62 |
| busy | perp-spot basis | 98604 | 10.83 | 0.18 | 0.92 | -0.19 |
| busy | Polymarket state | 98604 | 6.78 | 4.23 | -1.91 | -3.03 |
| busy | settlement scale (sigma, zs, delta) | 98604 | 9.68 | 1.32 | 0.02 | -1.09 |
| busy | fair value (pzm, gap) | 98604 | 10.89 | 0.11 | -0.62 | -1.73 |
| busy | delta-scaled Binance | 98604 | 8.90 | 2.10 | 1.17 | 0.05 |


## Residual drivers (realised 1 s - pred, rows with pred >= 2 c, pooled dev3 + final + ext)

| group | r2_drop |
|---|---|
| (held-out R2 of the residual model) | -0.0435 |
| regime (activity rates, vol) | 0.0536 |
| Polymarket state | 0.0386 |
| perp intensities / last tick | 0.0094 |
| settlement scale (sigma, zs, delta) | 0.0079 |
| perp queue / imbalance | 0.0039 |
| perp microprice change | 0.0033 |
| perp-spot basis | -0.0012 |
| delta-scaled Binance | -0.0020 |
| perp OFI (CKS) | -0.0023 |
| spot trades | -0.0045 |
| perp depletion / time-to-depletion | -0.0068 |
| spot book | -0.0083 |
| fair value (pzm, gap) | -0.0097 |
