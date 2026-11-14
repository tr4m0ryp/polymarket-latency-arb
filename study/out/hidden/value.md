# Markout by trigger class (0% tier fee), c per $

| who | move | Binance book trigger | fills | USD | c/$ at 2 s | c/$ at 10 s |
|---|---|---|---|---|---|---|
| A | move | none | 9 | 224 | -3.48 | -10.43 |
| A | move | opposite | 100 | 2,311 | -4.13 | -5.43 |
| A | move | same | 461 | 8,835 | +1.92 | -0.19 |
| A | move | split | 149 | 3,432 | +1.49 | +0.21 |
| A | no-move | none | 91 | 2,050 | +1.57 | -0.18 |
| A | no-move | opposite | 286 | 6,309 | +0.78 | -0.16 |
| A | no-move | same | 1584 | 29,443 | +1.26 | +0.36 |
| A | no-move | split | 346 | 7,342 | +1.10 | +1.20 |
| B | move | none | 21 | 468 | -5.88 | -4.21 |
| B | move | opposite | 167 | 3,493 | -5.02 | -8.66 |
| B | move | same | 665 | 12,719 | +1.41 | -2.87 |
| B | move | split | 217 | 4,906 | -3.18 | -4.35 |
| B | no-move | none | 205 | 4,576 | -0.66 | -1.36 |
| B | no-move | opposite | 621 | 13,181 | -0.76 | -1.37 |
| B | no-move | same | 3136 | 54,209 | +1.34 | +0.93 |
| B | no-move | split | 739 | 15,123 | +0.57 | +2.85 |

## The 150 ms hold: ask of the side bought at send time (print - 0.27 s) vs 50 ms before the print

- A: ask moved >= 1 c against 0.45, >= 1 c in favour 0.14; paid minus ask at send: mean +0.55 c, p10 / p50 / p90 -1 / +1 / +3 c
- B: ask moved >= 1 c against 0.18, >= 1 c in favour 0.12; paid minus ask at send: mean +0.06 c, p10 / p50 / p90 -1 / +0 / +2 c
