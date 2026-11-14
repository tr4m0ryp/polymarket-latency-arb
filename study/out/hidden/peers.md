# Copying, cadence and the fastest wallets

## Lag from the latest same-side fill of ...

| leader after | < 50 ms | 50-150 | 150-300 | 300-600 | Binance trigger acc / cov at 150-300 ms |
|---|---|---|---|---|---|
| A after other leader | 0.325 | 0.076 | 0.128 | 0.042 | 0.74 / 0.76 (n 386) |
| A after anyone else | 0.369 | 0.159 | 0.154 | 0.112 | 0.82 / 0.80 (n 467) |
| B after other leader | 0.033 | 0.017 | 0.045 | 0.039 | 0.68 / 0.69 (n 257) |
| B after anyone else | 0.280 | 0.141 | 0.158 | 0.145 | 0.82 / 0.78 (n 912) |

## Shared isolated perp ticks: print gap (ms)

| pair | n | p25 | median | p75 | abs < 20 ms |
|---|---|---|---|---|---|
| A - B | 210 | 2 | 11 | 32 | 0.56 |
| A - 0x0ca4e9d2 | 160 | -23 | -10 | -3 | 0.57 |
| B - 0x0ca4e9d2 | 153 | -40 | -18 | 7 | 0.37 |
| A - 0x764fd57b | 31 | -23 | 9 | 68 | 0.26 |
| B - 0x764fd57b | 36 | -35 | 11 | 72 | 0.28 |

## Cadence

- A: phase chi2 5.9 (9 df); modal gap 0.3-0.4 s; openers (gap > 5 s) 0.54 of fills, weak trigger 0.22; follow-ups 0.2-0.6 s 0.12, weak 0.52, same side 0.78
- B: phase chi2 31.3 (9 df); modal gap 0.3-0.4 s; openers (gap > 5 s) 0.43 of fills, weak trigger 0.25; follow-ups 0.2-0.6 s 0.14, weak 0.49, same side 0.71

## Impulse-response peak per wallet (perp mid ticks, 25 most active takers)

| wallet | fills | peak ms | lift |
|---|---|---|---|
| 0x21f4c1a1be34a39a7bc20985df4b7e5a39fb691d | 2641 | 250 | 38x |
| 0x3048d65321be3497164cdfc2996f94f98a2e7537 | 5771 | 250 | 49x |
| 0x764fd57b0b885cbeada5a119cdf0a113ee4ec347 | 1495 | 260 | 85x |
| 0xc53375ff94e96100f2b30a4b5775db35218d69a9 | 3026 | 270 | 74x |
| 0x0ca4e9d27ff826a109ecbf74754fb66b93f277a6 | 1803 | 280 | 96x |
| 0x1b58d3de60d7f9e1aefdc9449e8d3733ea096f11 | 1526 | 280 | 24x |
| 0xd30d67e84ab372cde3990cb2500177f4a3104f6d | 1959 | 310 | 28x |
| 0x60c20ca0901f9d55992913064686b1b4112b4746 | 1289 | 330 | 10x |
| 0x355d54242b1fcbc20e6bb3f8d94a1ccaaf5d1c50 | 3755 | 360 | 12x |
| 0x881f273d5e061ff221146d5a51cc8add1f2ae773 | 1782 | 420 | 13x |
| 0x6b14096b2adad7da689b326d0a2fba4179b890e6 | 1777 | 450 | 12x |
| 0x4c3acceaa187d6bcd1157eff104b5a669f9e9395 | 3614 | 600 | 12x |
| 0x550ab889a1c51c6420c809240873c1dab6e08109 | 1992 | 890 | 13x |
