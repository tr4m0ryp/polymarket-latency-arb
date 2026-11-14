# Earlier match instant (live limit)

| match_earlier_ms | fill_rate | mk10_c_per_$ | lo | hi | usd_per_order |
|---|---|---|---|---|---|
| 0 | 0.18 | -1.43 | -13.99 | 10.40 | -0.00 |
| 30 | 0.26 | -0.63 | -12.27 | 10.66 | -0.00 |
| 60 | 0.35 | 1.25 | -7.13 | 10.36 | 0.01 |
| 100 | 0.50 | 3.24 | -3.94 | 9.53 | 0.03 |
| 150 | 0.70 | 3.68 | -1.92 | 9.27 | 0.05 |
| 200 | 0.81 | 8.64 | 2.36 | 14.73 | 0.14 |
| 230 | 0.88 | 10.15 | 4.36 | 15.56 | 0.18 |


## When the depth at our limit vanished (orders that missed live), ms p10/25/50/75/90

- after our send: [43.0, 93.0, 146.0, 200.0, 331.0] (n 146 of 159)
- after the venue event that triggered us (book-triggered only): [158.0, 208.0, 265.0, 314.0, 400.0]
- our send after that event: [105.0, 107.0, 112.0, 126.0, 138.0]
