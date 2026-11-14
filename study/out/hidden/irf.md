# Reaction latency (venue clocks: Binance T -> CLOB print)

| event | who | events | peak lag ms | lift at peak | excess p10 / p50 / p90 ms | excess < 150 ms (sent before the event) | share of fills in excess |
|---|---|---|---|---|---|---|---|
| perp mid tick | A | 7920 | 270 | 74x | 160 / 280 / 680 | 0.09 | 0.431 |
| perp micro >= 0.02 bp | A | 7062 | 270 | 77x | 160 / 290 / 690 | 0.09 | 0.385 |
| spot mid tick | A | 5866 | 270 | 53x | 90 / 280 / 690 | 0.14 | 0.260 |
| spot trade move >= 0.05 bp | A | 8806 | 260 | 33x | 130 / 270 / 590 | 0.11 | 0.177 |
| perp mid tick | B | 7920 | 250 | 49x | 160 / 280 / 720 | 0.09 | 0.252 |
| perp micro >= 0.02 bp | B | 7062 | 250 | 45x | 150 / 280 / 730 | 0.09 | 0.220 |
| spot mid tick | B | 5866 | 260 | 36x | 100 / 280 / 740 | 0.14 | 0.150 |
| spot trade move >= 0.05 bp | B | 8806 | 260 | 21x | 140 / 260 / 710 | 0.10 | 0.096 |
| perp mid tick | other takers | 7920 | 280 | 17x | 230 / 400 / 810 | 0.04 | 0.253 |
| perp micro >= 0.02 bp | other takers | 7062 | 280 | 17x | 240 / 400 / 800 | 0.04 | 0.230 |
| spot mid tick | other takers | 5866 | 310 | 15x | 180 / 400 / 790 | 0.07 | 0.186 |
| spot trade move >= 0.05 bp | other takers | 8806 | 300 | 9x | 250 / 400 / 760 | 0.03 | 0.125 |

Isolated perp mid ticks (none in the prior 1 s): delay to the first same-side fill within 1 s

- A: n 505, p5 106, p25 262, median 286, p75 369 ms; share within 200-350 ms 0.63
- B: n 602, p5 120, p25 255, median 273, p75 369 ms; share within 200-350 ms 0.62
- other takers: n 2882, p5 20, p25 164, median 258, p75 294 ms; share within 200-350 ms 0.58
