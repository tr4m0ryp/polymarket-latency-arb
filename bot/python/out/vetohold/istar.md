# Needed offset i* (veto orders)

## Distribution (c)

| measure | n | p10 | p25 | p50 | p75 | p90 | <=0 % | <=2 % | <=5 % | <=10 % | none in +30 c % |
|---|---|---|---|---|---|---|---|---|---|---|---|
| i*1 at median hold | 9890 | 0.0 | 2.0 | 4.0 | 7.0 | 12.0 | 13.4 | 31.3 | 61.7 | 86.1 | 1.2 |
| i*60 at median hold | 9890 | 0.0 | 2.0 | 5.0 | 9.0 | 14.0 | 10.1 | 26.5 | 55.2 | 82.4 | 1.5 |
| i*1 mean over live-hold draws | 9890 | 0.4 | 2.0 | 4.2 | 7.7 | 12.2 | 6.9 | 26.8 | 57.9 | 84.7 | 0.9 |


## What i* moves with (Spearman, all veto orders, real hold)

| feature | spearman with i* |
|---|---|
| f_dep5 | -0.414 |
| f_fair_edge | 0.371 |
| f_pred_opp | -0.370 |
| f_dep2 | -0.342 |
| f_perp_0.5 | 0.284 |
| f_perp_1.0 | 0.267 |
| f_perp_0.25 | 0.249 |
| f_dep0 | -0.223 |
| f_fresh | 0.222 |
| f_value | 0.216 |
| f_edge | 0.216 |
| f_spot_1.0 | 0.216 |
| f_spot_0.5 | 0.203 |
| f_vol30 | -0.201 |
| f_perp_3.0 | 0.199 |


## By model edge quintile

| edge bin | edge c | hold-free value c | i* c | i* p50 c | edge - i* c | realized at seen + i* c | edge > i* % | realized > 0 at i* % |
|---|---|---|---|---|---|---|---|---|
| Q1 (+0.021) | 2.1 | 3.2 | 4.6 | 3.8 | -2.5 | -1.4 | 33.4 | 40.8 |
| Q2 (+0.022) | 2.3 | 3.8 | 4.8 | 3.8 | -2.5 | -1.0 | 33.8 | 42.2 |
| Q3 (+0.025) | 2.5 | 4.0 | 5.1 | 4.0 | -2.6 | -1.1 | 31.9 | 43.6 |
| Q4 (+0.029) | 2.9 | 4.9 | 5.8 | 4.6 | -2.9 | -1.0 | 30.9 | 41.3 |
| Q5 (+0.040) | 4.4 | 8.4 | 8.7 | 6.8 | -4.3 | -0.3 | 29.9 | 44.3 |


## By realized hold-free value quintile (what the move turned out to be)

| value bin | edge c | hold-free value c | i* c | i* p50 c | edge - i* c | realized at seen + i* c | edge > i* % | realized > 0 at i* % |
|---|---|---|---|---|---|---|---|---|
| Q1 (-0.086) | 2.7 | -11.0 | 3.9 | 3.3 | -1.2 | -15.0 | 42.1 | 0.3 |
| Q2 (-0.016) | 2.7 | -1.6 | 3.6 | 3.0 | -0.9 | -5.3 | 46.9 | 2.5 |
| Q3 (+0.030) | 2.7 | 3.1 | 4.7 | 4.0 | -2.0 | -1.6 | 33.6 | 39.1 |
| Q4 (+0.089) | 2.8 | 9.1 | 6.2 | 5.1 | -3.4 | 2.9 | 22.5 | 77.5 |
| Q5 (+0.207) | 3.2 | 24.7 | 10.5 | 8.5 | -7.3 | 14.1 | 14.7 | 92.9 |


- slope of i* on the realized move (mk - seen): +0.20 (intercept +4.6 c)
- slope of i* on the model edge: +1.86 (intercept +0.5 c)
