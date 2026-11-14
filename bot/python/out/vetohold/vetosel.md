# Veto selection vs depth survival (all trigger rows, i = 0, 60 sh)

| trigger rows | n | share % | surv i=0 % (real) | fill % (real) | value c/sh real | value c/sh 250 ms | value if filled c/sh | dep0 med | age med s | feed lag med ms |
|---|---|---|---|---|---|---|---|---|---|---|
| vetoed: v1 prefers other side | 60767 | 5.67 | 72.85 | 74.37 | -1.10 | -1.15 | -1.51 | 552.38 | 0.20 | 103.47 |
| vetoed: v1 value < 0 | 755379 | 70.45 | 19.58 | 21.76 | -0.16 | -0.13 | -0.80 | 124.70 | 0.17 | 29.94 |
| vetoed: 0 <= v1 < 2 c | 194701 | 18.16 | 13.20 | 15.12 | 0.06 | 0.10 | 0.47 | 154.99 | 0.10 | 16.82 |
| kept: 2-3 c | 31484 | 2.94 | 9.47 | 11.10 | 0.22 | 0.28 | 2.34 | 166.21 | 0.10 | 14.69 |
| kept: 3-5 c | 20822 | 1.94 | 8.12 | 9.64 | 0.54 | 0.64 | 6.63 | 179.88 | 0.11 | 15.23 |
| kept: >= 5 c | 9067 | 0.85 | 8.00 | 9.84 | 1.51 | 1.79 | 18.89 | 245.00 | 0.17 | 15.50 |

