# Competition diagnostic: tables
Orders: 20,176; markets: select 144, dev3 120, final 83, ext 48

## Exposure to rivals, L = 0 (base fills)
| index | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| arm | micf | micf | micf | vt_v1_m0.03_any | vt_v1_m0.03_any | vt_v1_m0.03_any | vt_v1_m0.02_trigger | vt_v1_m0.02_trigger | vt_v1_m0.02_trigger | vt_v3p_m0.02_any | vt_v3p_m0.02_any | vt_v3p_m0.02_any |
| L | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| regime | select | quiet | busy | select | quiet | busy | select | quiet | busy | select | quiet | busy |
| orders/day | 1,470.000 | 1,098.089 | 2,172.000 | 1,212.000 | 1,103.764 | 2,298.000 | 1,040.000 | 1,078.227 | 3,282.000 | 4,040.000 | 2,685.635 | 5,508.000 |
| fill rate | 0.486 | 0.379 | 0.431 | 0.474 | 0.401 | 0.413 | 0.337 | 0.330 | 0.435 | 0.654 | 0.587 | 0.578 |
| shares/fill | 50.794 | 50.839 | 52.620 | 47.087 | 47.613 | 50.742 | 44.026 | 46.815 | 49.839 | 50.029 | 51.643 | 51.164 |
| rival in hold, our levels | 0.563 | 0.519 | 0.577 | 0.352 | 0.433 | 0.380 | 0.371 | 0.295 | 0.332 | 0.466 | 0.521 | 0.450 |
| rival in hold, any level | 0.563 | 0.522 | 0.577 | 0.355 | 0.433 | 0.380 | 0.371 | 0.295 | 0.336 | 0.468 | 0.524 | 0.452 |
| rival in hold, unfilled | 0.836 | 0.784 | 0.845 | 0.693 | 0.633 | 0.622 | 0.701 | 0.666 | 0.573 | 0.654 | 0.703 | 0.646 |
| leader share of hold prints |  | 0.040 | 0.033 |  | 0.000 | 0.036 |  | 0.069 | 0.119 |  | 0.025 | 0.041 |
| rival <= 25 ms after | 0.319 | 0.345 | 0.250 | 0.199 | 0.279 | 0.335 | 0.257 | 0.283 | 0.374 | 0.194 | 0.243 | 0.352 |
| our shares gone 50 ms later | 0.164 | 0.194 | 0.086 | 0.182 | 0.218 | 0.261 | 0.290 | 0.257 | 0.200 | 0.142 | 0.156 | 0.174 |
| ... taken by a print | 0.091 | 0.125 | 0.052 | 0.082 | 0.119 | 0.183 | 0.184 | 0.150 | 0.140 | 0.049 | 0.064 | 0.109 |
| our shares gone 100 ms later | 0.260 | 0.300 | 0.153 | 0.293 | 0.349 | 0.389 | 0.447 | 0.382 | 0.335 | 0.237 | 0.280 | 0.304 |
| depth kept through hold | 0.889 | 0.827 | 1.000 | 0.885 | 0.759 | 0.578 | 0.433 | 0.545 | 0.578 | 1.000 | 0.992 | 0.702 |
| traded share of hold drop | 0.228 | 0.226 | 0.294 | 0.095 | 0.128 | 0.047 | 0.072 | 0.055 | 0.074 | 0.231 | 0.258 | 0.075 |
| slip c | 0.382 | 0.529 | 0.278 | -0.399 | -0.348 | 0.391 | 0.735 | 0.495 | 0.803 | -0.920 | -1.070 | 0.039 |
| mk10 c/$ | 3.477 | 7.908 | 1.268 | 14.283 | 19.576 | 7.675 | 21.041 | 18.730 | 3.472 | 4.312 | 8.886 | -1.555 |

## Exposure to rivals, L = -40 (base fills)
| index | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 |
|---|---|---|---|---|---|---|---|---|---|
| arm | micf | micf | micf | vt_v1_m0.03_any | vt_v1_m0.03_any | vt_v1_m0.03_any | vt_v1_m0.02_trigger | vt_v1_m0.02_trigger | vt_v1_m0.02_trigger |
| L | -40 | -40 | -40 | -40 | -40 | -40 | -40 | -40 | -40 |
| regime | select | quiet | busy | select | quiet | busy | select | quiet | busy |
| orders/day | 1,470.000 | 1,098.089 | 2,172.000 | 2,402.000 | 2,105.379 | 6,666.000 | 2,010.000 | 1,858.522 | 6,972.000 |
| fill rate | 0.577 | 0.537 | 0.564 | 0.690 | 0.652 | 0.772 | 0.616 | 0.644 | 0.739 |
| shares/fill | 48.599 | 47.952 | 48.519 | 43.717 | 43.794 | 46.732 | 40.495 | 43.357 | 47.787 |
| rival in hold, our levels | 0.465 | 0.421 | 0.539 | 0.308 | 0.319 | 0.287 | 0.325 | 0.274 | 0.307 |
| rival in hold, any level | 0.467 | 0.421 | 0.539 | 0.308 | 0.320 | 0.287 | 0.326 | 0.275 | 0.307 |
| rival in hold, unfilled | 0.797 | 0.682 | 0.728 | 0.610 | 0.535 | 0.557 | 0.663 | 0.530 | 0.587 |
| leader share of hold prints |  | 0.016 | 0.044 |  | 0.033 | 0.066 |  | 0.026 | 0.068 |
| rival <= 25 ms after | 0.226 | 0.185 | 0.235 | 0.106 | 0.130 | 0.098 | 0.129 | 0.108 | 0.101 |
| our shares gone 50 ms later | 0.245 | 0.334 | 0.233 | 0.272 | 0.321 | 0.329 | 0.359 | 0.383 | 0.291 |
| ... taken by a print | 0.161 | 0.218 | 0.152 | 0.140 | 0.175 | 0.225 | 0.229 | 0.227 | 0.194 |
| our shares gone 100 ms later | 0.371 | 0.474 | 0.287 | 0.387 | 0.453 | 0.452 | 0.494 | 0.526 | 0.417 |
| depth kept through hold | 0.708 | 0.533 | 0.892 | 0.430 | 0.375 | 0.223 | 0.195 | 0.227 | 0.255 |
| traded share of hold drop | 0.083 | 0.072 | 0.145 | 0.030 | 0.029 | 0.017 | 0.026 | 0.018 | 0.018 |
| slip c | 0.452 | 0.637 | 0.347 | 0.345 | 0.441 | 0.788 | 0.730 | 0.716 | 0.786 |
| mk10 c/$ | 5.380 | 8.955 | 2.147 | 8.924 | 11.345 | 2.583 | 8.369 | 10.298 | 1.011 |

## Markout by exposure, L = 0
| arm | regime | split | group | fills | share | mk10 c/$ | lo | hi | mk10 $/day |
|---|---|---|---|---|---|---|---|---|---|
| micf | quiet | rival print in hold at our levels | no | 141 | 0.48 | 16.12 | 10.14 | 22.45 | 988.02 |
| micf | quiet | rival print in hold at our levels | yes | 152 | 0.52 | 1.91 | -1.06 | 5.07 | 160.21 |
| micf | quiet | rival print in hold, any level | no | 140 | 0.48 | 16.17 | 10.17 | 22.57 | 989.78 |
| micf | quiet | rival print in hold, any level | yes | 153 | 0.52 | 1.89 | -1.08 | 5.02 | 158.44 |
| micf | quiet | share of our fill a rival took <= 50 ms later | 0 | 217 | 0.74 | 8.67 | 4.58 | 13.01 | 958.68 |
| micf | quiet | share of our fill a rival took <= 50 ms later | 0-50% | 29 | 0.10 | 2.62 | -2.20 | 7.88 | 40.53 |
| micf | quiet | share of our fill a rival took <= 50 ms later | >50% | 47 | 0.16 | 7.78 | 4.34 | 12.03 | 149.01 |
| micf | quiet | share of our fill gone <= 50 ms later | 0 | 190 | 0.65 | 7.49 | 3.63 | 11.98 | 752.96 |
| micf | quiet | share of our fill gone <= 50 ms later | 0-50% | 34 | 0.12 | 5.11 | -2.44 | 16.42 | 87.62 |
| micf | quiet | share of our fill gone <= 50 ms later | >50% | 69 | 0.24 | 11.16 | 7.28 | 16.56 | 307.64 |
| micf | quiet | same-side prints in last 1 s (decision time) | 0 | 57 | 0.19 | 22.42 | 11.83 | 35.56 | 510.52 |
| micf | quiet | same-side prints in last 1 s (decision time) | 1-2 | 70 | 0.24 | 15.85 | 7.85 | 25.66 | 512.36 |
| micf | quiet | same-side prints in last 1 s (decision time) | 3+ | 166 | 0.57 | 1.39 | -0.90 | 3.91 | 125.34 |
| micf | quiet | our-view depth at seen price (decision time) | 120+ | 116 | 0.40 | 11.59 | 6.44 | 17.74 | 713.10 |
| micf | quiet | our-view depth at seen price (decision time) | 30-120 | 101 | 0.34 | 6.82 | 2.73 | 11.42 | 347.87 |
| micf | quiet | our-view depth at seen price (decision time) | <30 | 76 | 0.26 | 2.68 | -3.27 | 9.37 | 87.25 |
| micf | quiet | book messages in last 1 s (decision time) | 1500+ | 121 | 0.41 | 1.13 | -1.48 | 3.86 | 72.35 |
| micf | quiet | book messages in last 1 s (decision time) | 500-1500 | 92 | 0.31 | 5.74 | 1.43 | 11.17 | 266.54 |
| micf | quiet | book messages in last 1 s (decision time) | <500 | 80 | 0.27 | 23.26 | 13.50 | 34.19 | 809.34 |
| micf | quiet | fill fraction | 50-99% | 33 | 0.11 | 20.31 | 7.81 | 35.42 | 268.64 |
| micf | quiet | fill fraction | <50% | 52 | 0.18 | 28.26 | 15.22 | 46.26 | 177.63 |
| micf | quiet | fill fraction | full | 208 | 0.71 | 5.59 | 2.45 | 8.90 | 701.95 |
| micf | busy | rival print in hold at our levels | no | 66 | 0.42 | 2.95 | -4.46 | 9.68 | 360.47 |
| micf | busy | rival print in hold at our levels | yes | 90 | 0.58 | 0.08 | -5.75 | 6.02 | 14.68 |
| micf | busy | rival print in hold, any level | no | 66 | 0.42 | 2.95 | -4.46 | 9.68 | 360.47 |
| micf | busy | rival print in hold, any level | yes | 90 | 0.58 | 0.08 | -5.75 | 6.02 | 14.68 |
| micf | busy | share of our fill a rival took <= 50 ms later | 0 | 128 | 0.82 | 1.11 | -3.88 | 6.03 | 281.23 |
| micf | busy | share of our fill a rival took <= 50 ms later | 0-50% | 14 | 0.09 | 5.19 | -5.07 | 17.25 | 148.58 |
| micf | busy | share of our fill a rival took <= 50 ms later | >50% | 14 | 0.09 | -4.25 | -9.40 | 2.02 | -54.66 |
| micf | busy | share of our fill gone <= 50 ms later | 0 | 119 | 0.76 | 0.60 | -3.94 | 5.04 | 144.86 |
| micf | busy | share of our fill gone <= 50 ms later | 0-50% | 15 | 0.10 | 1.71 | -12.11 | 16.54 | 50.00 |
| micf | busy | share of our fill gone <= 50 ms later | >50% | 22 | 0.14 | 6.97 | -2.26 | 16.94 | 180.29 |
| micf | busy | same-side prints in last 1 s (decision time) | 0 | 10 | 0.06 | 10.75 | -8.13 | 28.24 | 172.65 |
| micf | busy | same-side prints in last 1 s (decision time) | 1-2 | 22 | 0.14 | 11.11 | -0.68 | 21.92 | 453.64 |
| micf | busy | same-side prints in last 1 s (decision time) | 3+ | 124 | 0.79 | -1.05 | -5.37 | 3.14 | -251.13 |
| micf | busy | our-view depth at seen price (decision time) | 120+ | 57 | 0.37 | -3.03 | -8.88 | 3.33 | -329.32 |
| micf | busy | our-view depth at seen price (decision time) | 30-120 | 54 | 0.35 | 0.72 | -6.47 | 6.78 | 74.83 |
| micf | busy | our-view depth at seen price (decision time) | <30 | 45 | 0.29 | 7.58 | -0.01 | 15.63 | 629.64 |
| micf | busy | book messages in last 1 s (decision time) | 1500+ | 107 | 0.69 | -1.75 | -6.80 | 3.04 | -353.09 |
| micf | busy | book messages in last 1 s (decision time) | 500-1500 | 40 | 0.26 | 7.21 | 0.67 | 14.71 | 563.77 |
| micf | busy | book messages in last 1 s (decision time) | <500 | 9 | 0.06 | 10.11 | -1.86 | 23.10 | 164.48 |
| micf | busy | fill fraction | 50-99% | 4 | 0.03 | 8.86 | -1.26 | 37.40 | 80.70 |
| micf | busy | fill fraction | <50% | 24 | 0.15 | 0.29 | -7.85 | 7.46 | 3.95 |
| micf | busy | fill fraction | full | 128 | 0.82 | 1.06 | -3.87 | 5.95 | 290.51 |
| vt_v1_m0.03_any | quiet | rival print in hold at our levels | no | 177 | 0.57 | 24.64 | 15.88 | 33.96 | 1,278.99 |
| vt_v1_m0.03_any | quiet | rival print in hold at our levels | yes | 135 | 0.43 | 14.03 | -2.37 | 32.69 | 664.94 |
| vt_v1_m0.03_any | quiet | rival print in hold, any level | no | 177 | 0.57 | 24.64 | 15.88 | 33.96 | 1,278.99 |
| vt_v1_m0.03_any | quiet | rival print in hold, any level | yes | 135 | 0.43 | 14.03 | -2.37 | 32.69 | 664.94 |
| vt_v1_m0.03_any | quiet | share of our fill a rival took <= 50 ms later | 0 | 235 | 0.75 | 19.21 | 8.88 | 30.71 | 1,489.79 |
| vt_v1_m0.03_any | quiet | share of our fill a rival took <= 50 ms later | 0-50% | 33 | 0.11 | 18.80 | -4.56 | 50.57 | 238.80 |
| vt_v1_m0.03_any | quiet | share of our fill a rival took <= 50 ms later | >50% | 44 | 0.14 | 23.78 | 11.42 | 39.75 | 215.34 |
| vt_v1_m0.03_any | quiet | share of our fill gone <= 50 ms later | 0 | 183 | 0.59 | 16.78 | 8.44 | 26.94 | 1,072.24 |
| vt_v1_m0.03_any | quiet | share of our fill gone <= 50 ms later | 0-50% | 44 | 0.14 | 25.24 | -2.11 | 55.32 | 429.30 |
| vt_v1_m0.03_any | quiet | share of our fill gone <= 50 ms later | >50% | 85 | 0.27 | 24.04 | 6.84 | 43.28 | 442.39 |
| vt_v1_m0.03_any | quiet | same-side prints in last 1 s (decision time) | 0 | 64 | 0.21 | 29.35 | 17.22 | 41.55 | 546.88 |
| vt_v1_m0.03_any | quiet | same-side prints in last 1 s (decision time) | 1-2 | 97 | 0.31 | 16.74 | 7.19 | 27.70 | 446.03 |
| vt_v1_m0.03_any | quiet | same-side prints in last 1 s (decision time) | 3+ | 151 | 0.48 | 17.60 | 0.19 | 38.15 | 951.02 |
| vt_v1_m0.03_any | quiet | our-view depth at seen price (decision time) | 120+ | 130 | 0.42 | 21.34 | 9.89 | 35.65 | 829.59 |
| vt_v1_m0.03_any | quiet | our-view depth at seen price (decision time) | 30-120 | 106 | 0.34 | 17.22 | 4.96 | 30.47 | 623.51 |
| vt_v1_m0.03_any | quiet | our-view depth at seen price (decision time) | <30 | 76 | 0.24 | 20.26 | 3.68 | 36.83 | 490.83 |
| vt_v1_m0.03_any | quiet | book messages in last 1 s (decision time) | 1500+ | 114 | 0.37 | 16.34 | -6.23 | 40.66 | 656.34 |
| vt_v1_m0.03_any | quiet | book messages in last 1 s (decision time) | 500-1500 | 107 | 0.34 | 15.28 | 8.52 | 24.65 | 534.54 |
| vt_v1_m0.03_any | quiet | book messages in last 1 s (decision time) | <500 | 91 | 0.29 | 31.18 | 19.49 | 43.58 | 753.04 |
| vt_v1_m0.03_any | quiet | fill fraction | 50-99% | 40 | 0.13 | 32.18 | 16.40 | 49.45 | 396.57 |
| vt_v1_m0.03_any | quiet | fill fraction | <50% | 73 | 0.23 | 36.34 | 20.31 | 57.74 | 223.99 |
| vt_v1_m0.03_any | quiet | fill fraction | full | 199 | 0.64 | 16.37 | 5.53 | 28.65 | 1,323.37 |
| vt_v1_m0.03_any | busy | rival print in hold at our levels | no | 98 | 0.62 | 8.83 | 0.84 | 17.55 | 928.25 |
| vt_v1_m0.03_any | busy | rival print in hold at our levels | yes | 60 | 0.38 | 6.22 | -0.88 | 14.34 | 521.99 |
| vt_v1_m0.03_any | busy | rival print in hold, any level | no | 98 | 0.62 | 8.83 | 0.84 | 17.55 | 928.25 |
| vt_v1_m0.03_any | busy | rival print in hold, any level | yes | 60 | 0.38 | 6.22 | -0.88 | 14.34 | 521.99 |
| vt_v1_m0.03_any | busy | share of our fill a rival took <= 50 ms later | 0 | 95 | 0.60 | 6.36 | -1.50 | 15.98 | 708.21 |
| vt_v1_m0.03_any | busy | share of our fill a rival took <= 50 ms later | 0-50% | 30 | 0.19 | 11.38 | 2.47 | 24.47 | 545.24 |
| vt_v1_m0.03_any | busy | share of our fill a rival took <= 50 ms later | >50% | 33 | 0.21 | 6.64 | -2.62 | 15.84 | 196.80 |
| vt_v1_m0.03_any | busy | share of our fill gone <= 50 ms later | 0 | 84 | 0.53 | 3.93 | -3.63 | 12.26 | 391.90 |
| vt_v1_m0.03_any | busy | share of our fill gone <= 50 ms later | 0-50% | 25 | 0.16 | 1.78 | -5.23 | 8.54 | 70.55 |
| vt_v1_m0.03_any | busy | share of our fill gone <= 50 ms later | >50% | 49 | 0.31 | 19.90 | 8.47 | 34.37 | 987.81 |
| vt_v1_m0.03_any | busy | same-side prints in last 1 s (decision time) | 0 | 32 | 0.20 | 8.08 | -5.02 | 20.89 | 262.05 |
| vt_v1_m0.03_any | busy | same-side prints in last 1 s (decision time) | 1-2 | 48 | 0.30 | 4.72 | -3.83 | 13.15 | 256.58 |
| vt_v1_m0.03_any | busy | same-side prints in last 1 s (decision time) | 3+ | 78 | 0.49 | 9.11 | -0.45 | 20.93 | 931.62 |
| vt_v1_m0.03_any | busy | our-view depth at seen price (decision time) | 120+ | 78 | 0.49 | 6.39 | -0.04 | 12.87 | 619.05 |
| vt_v1_m0.03_any | busy | our-view depth at seen price (decision time) | 30-120 | 49 | 0.31 | 4.12 | -3.56 | 12.66 | 234.40 |
| vt_v1_m0.03_any | busy | our-view depth at seen price (decision time) | <30 | 31 | 0.20 | 16.98 | -5.50 | 41.95 | 596.80 |
| vt_v1_m0.03_any | busy | book messages in last 1 s (decision time) | 1500+ | 61 | 0.39 | 11.70 | -0.13 | 26.98 | 922.40 |
| vt_v1_m0.03_any | busy | book messages in last 1 s (decision time) | 500-1500 | 79 | 0.50 | 3.00 | -2.90 | 9.50 | 262.39 |
| vt_v1_m0.03_any | busy | book messages in last 1 s (decision time) | <500 | 18 | 0.11 | 11.78 | -6.28 | 30.15 | 265.46 |
| vt_v1_m0.03_any | busy | fill fraction | 50-99% | 23 | 0.15 | 13.58 | 1.00 | 27.98 | 369.22 |
| vt_v1_m0.03_any | busy | fill fraction | <50% | 24 | 0.15 | 28.15 | 11.53 | 41.14 | 238.34 |
| vt_v1_m0.03_any | busy | fill fraction | full | 111 | 0.70 | 5.50 | -1.38 | 12.75 | 842.69 |
| vt_v1_m0.02_trigger | quiet | rival print in hold at our levels | no | 177 | 0.71 | 23.76 | 17.33 | 30.35 | 1,221.23 |
| vt_v1_m0.02_trigger | quiet | rival print in hold at our levels | yes | 74 | 0.29 | 7.33 | 1.05 | 15.22 | 166.23 |
| vt_v1_m0.02_trigger | quiet | rival print in hold, any level | no | 177 | 0.71 | 23.76 | 17.33 | 30.35 | 1,221.23 |
| vt_v1_m0.02_trigger | quiet | rival print in hold, any level | yes | 74 | 0.29 | 7.33 | 1.05 | 15.22 | 166.23 |
| vt_v1_m0.02_trigger | quiet | share of our fill a rival took <= 50 ms later | 0 | 184 | 0.73 | 21.23 | 14.65 | 28.44 | 1,174.66 |
| vt_v1_m0.02_trigger | quiet | share of our fill a rival took <= 50 ms later | 0-50% | 20 | 0.08 | 13.39 | 4.20 | 27.51 | 100.20 |
| vt_v1_m0.02_trigger | quiet | share of our fill a rival took <= 50 ms later | >50% | 47 | 0.19 | 10.01 | 3.86 | 18.62 | 112.60 |
| vt_v1_m0.02_trigger | quiet | share of our fill gone <= 50 ms later | 0 | 146 | 0.58 | 20.95 | 13.42 | 29.16 | 975.15 |
| vt_v1_m0.02_trigger | quiet | share of our fill gone <= 50 ms later | 0-50% | 25 | 0.10 | 16.61 | 5.46 | 36.36 | 137.63 |
| vt_v1_m0.02_trigger | quiet | share of our fill gone <= 50 ms later | >50% | 80 | 0.32 | 14.27 | 7.27 | 22.82 | 274.68 |
| vt_v1_m0.02_trigger | quiet | same-side prints in last 1 s (decision time) | 0 | 79 | 0.31 | 24.66 | 15.02 | 35.17 | 625.67 |
| vt_v1_m0.02_trigger | quiet | same-side prints in last 1 s (decision time) | 1-2 | 92 | 0.37 | 21.51 | 13.33 | 30.91 | 555.49 |
| vt_v1_m0.02_trigger | quiet | same-side prints in last 1 s (decision time) | 3+ | 80 | 0.32 | 9.02 | 2.67 | 17.26 | 206.30 |
| vt_v1_m0.02_trigger | quiet | our-view depth at seen price (decision time) | 120+ | 128 | 0.51 | 21.40 | 14.04 | 28.97 | 758.83 |
| vt_v1_m0.02_trigger | quiet | our-view depth at seen price (decision time) | 30-120 | 73 | 0.29 | 18.49 | 11.08 | 27.14 | 439.06 |
| vt_v1_m0.02_trigger | quiet | our-view depth at seen price (decision time) | <30 | 50 | 0.20 | 12.76 | 3.29 | 25.49 | 189.57 |
| vt_v1_m0.02_trigger | quiet | book messages in last 1 s (decision time) | 1500+ | 46 | 0.18 | 8.19 | 1.24 | 18.25 | 119.83 |
| vt_v1_m0.02_trigger | quiet | book messages in last 1 s (decision time) | 500-1500 | 98 | 0.39 | 15.88 | 9.03 | 24.94 | 414.31 |
| vt_v1_m0.02_trigger | quiet | book messages in last 1 s (decision time) | <500 | 107 | 0.43 | 25.58 | 17.95 | 33.67 | 853.31 |
| vt_v1_m0.02_trigger | quiet | fill fraction | 50-99% | 30 | 0.12 | 28.44 | 12.44 | 49.13 | 221.27 |
| vt_v1_m0.02_trigger | quiet | fill fraction | <50% | 65 | 0.26 | 39.06 | 23.79 | 59.80 | 218.27 |
| vt_v1_m0.02_trigger | quiet | fill fraction | full | 156 | 0.62 | 15.61 | 10.64 | 20.84 | 947.93 |
| vt_v1_m0.02_trigger | busy | rival print in hold at our levels | no | 159 | 0.67 | 4.17 | -1.07 | 10.52 | 689.79 |
| vt_v1_m0.02_trigger | busy | rival print in hold at our levels | yes | 79 | 0.33 | 2.10 | -3.62 | 9.09 | 176.58 |
| vt_v1_m0.02_trigger | busy | rival print in hold, any level | no | 158 | 0.66 | 4.65 | -1.00 | 11.46 | 761.98 |
| vt_v1_m0.02_trigger | busy | rival print in hold, any level | yes | 80 | 0.34 | 1.22 | -3.93 | 7.00 | 104.38 |
| vt_v1_m0.02_trigger | busy | share of our fill a rival took <= 50 ms later | 0 | 147 | 0.62 | 1.78 | -5.30 | 9.93 | 262.67 |
| vt_v1_m0.02_trigger | busy | share of our fill a rival took <= 50 ms later | 0-50% | 46 | 0.19 | 6.47 | 1.57 | 14.15 | 441.22 |
| vt_v1_m0.02_trigger | busy | share of our fill a rival took <= 50 ms later | >50% | 45 | 0.19 | 4.77 | -4.62 | 13.99 | 162.48 |
| vt_v1_m0.02_trigger | busy | share of our fill gone <= 50 ms later | 0 | 135 | 0.57 | 0.97 | -6.41 | 9.75 | 134.26 |
| vt_v1_m0.02_trigger | busy | share of our fill gone <= 50 ms later | 0-50% | 43 | 0.18 | 5.31 | -0.45 | 13.28 | 323.67 |
| vt_v1_m0.02_trigger | busy | share of our fill gone <= 50 ms later | >50% | 60 | 0.25 | 8.07 | 0.81 | 15.67 | 408.44 |
| vt_v1_m0.02_trigger | busy | same-side prints in last 1 s (decision time) | 0 | 51 | 0.21 | 4.81 | -7.15 | 15.27 | 214.40 |
| vt_v1_m0.02_trigger | busy | same-side prints in last 1 s (decision time) | 1-2 | 80 | 0.34 | 1.79 | -7.30 | 10.95 | 127.70 |
| vt_v1_m0.02_trigger | busy | same-side prints in last 1 s (decision time) | 3+ | 107 | 0.45 | 3.93 | -0.60 | 11.34 | 524.27 |
| vt_v1_m0.02_trigger | busy | our-view depth at seen price (decision time) | 120+ | 123 | 0.52 | 1.37 | -4.52 | 8.65 | 179.10 |
| vt_v1_m0.02_trigger | busy | our-view depth at seen price (decision time) | 30-120 | 69 | 0.29 | 3.89 | -3.73 | 11.10 | 288.08 |
| vt_v1_m0.02_trigger | busy | our-view depth at seen price (decision time) | <30 | 46 | 0.19 | 8.93 | -0.88 | 21.97 | 399.19 |
| vt_v1_m0.02_trigger | busy | book messages in last 1 s (decision time) | 1500+ | 71 | 0.30 | 4.63 | -2.52 | 14.49 | 370.65 |
| vt_v1_m0.02_trigger | busy | book messages in last 1 s (decision time) | 500-1500 | 138 | 0.58 | 1.56 | -3.14 | 6.91 | 218.26 |
| vt_v1_m0.02_trigger | busy | book messages in last 1 s (decision time) | <500 | 29 | 0.12 | 9.46 | -2.22 | 18.83 | 277.46 |
| vt_v1_m0.02_trigger | busy | fill fraction | 50-99% | 30 | 0.13 | 3.28 | -5.19 | 10.46 | 121.33 |
| vt_v1_m0.02_trigger | busy | fill fraction | <50% | 43 | 0.18 | 2.85 | -2.97 | 9.08 | 46.37 |
| vt_v1_m0.02_trigger | busy | fill fraction | full | 165 | 0.69 | 3.56 | -2.16 | 10.64 | 698.67 |
| vt_v3p_m0.02_any | quiet | rival print in hold at our levels | no | 532 | 0.48 | 12.46 | 1.92 | 24.53 | 2,425.35 |
| vt_v3p_m0.02_any | quiet | rival print in hold at our levels | yes | 579 | 0.52 | 5.93 | -4.09 | 16.56 | 1,398.53 |
| vt_v3p_m0.02_any | quiet | rival print in hold, any level | no | 529 | 0.48 | 12.34 | 1.99 | 24.25 | 2,390.41 |
| vt_v3p_m0.02_any | quiet | rival print in hold, any level | yes | 582 | 0.52 | 6.06 | -4.15 | 17.04 | 1,433.46 |
| vt_v3p_m0.02_any | quiet | share of our fill a rival took <= 50 ms later | 0 | 923 | 0.83 | 8.50 | -1.19 | 19.22 | 3,048.86 |
| vt_v3p_m0.02_any | quiet | share of our fill a rival took <= 50 ms later | 0-50% | 104 | 0.09 | 12.19 | 1.40 | 25.08 | 567.48 |
| vt_v3p_m0.02_any | quiet | share of our fill a rival took <= 50 ms later | >50% | 84 | 0.08 | 8.22 | 0.98 | 15.44 | 207.54 |
| vt_v3p_m0.02_any | quiet | share of our fill gone <= 50 ms later | 0 | 751 | 0.68 | 9.06 | -0.11 | 20.38 | 2,662.23 |
| vt_v3p_m0.02_any | quiet | share of our fill gone <= 50 ms later | 0-50% | 167 | 0.15 | 7.77 | -6.26 | 22.74 | 583.13 |
| vt_v3p_m0.02_any | quiet | share of our fill gone <= 50 ms later | >50% | 193 | 0.17 | 9.44 | -0.28 | 20.95 | 578.52 |
| vt_v3p_m0.02_any | quiet | same-side prints in last 1 s (decision time) | 0 | 148 | 0.13 | 24.43 | 8.34 | 43.07 | 1,323.36 |
| vt_v3p_m0.02_any | quiet | same-side prints in last 1 s (decision time) | 1-2 | 237 | 0.21 | 13.61 | 3.13 | 26.29 | 1,138.82 |
| vt_v3p_m0.02_any | quiet | same-side prints in last 1 s (decision time) | 3+ | 726 | 0.65 | 4.66 | -5.60 | 15.65 | 1,361.70 |
| vt_v3p_m0.02_any | quiet | our-view depth at seen price (decision time) | 120+ | 429 | 0.39 | 16.86 | 4.03 | 32.78 | 2,748.58 |
| vt_v3p_m0.02_any | quiet | our-view depth at seen price (decision time) | 30-120 | 403 | 0.36 | 4.84 | -5.28 | 14.67 | 796.00 |
| vt_v3p_m0.02_any | quiet | our-view depth at seen price (decision time) | <30 | 279 | 0.25 | 2.72 | -6.41 | 12.14 | 279.30 |
| vt_v3p_m0.02_any | quiet | book messages in last 1 s (decision time) | 1500+ | 624 | 0.56 | 4.96 | -5.49 | 16.35 | 1,230.61 |
| vt_v3p_m0.02_any | quiet | book messages in last 1 s (decision time) | 500-1500 | 316 | 0.28 | 7.59 | 0.15 | 16.58 | 905.48 |
| vt_v3p_m0.02_any | quiet | book messages in last 1 s (decision time) | <500 | 171 | 0.15 | 26.82 | 10.24 | 44.78 | 1,687.79 |
| vt_v3p_m0.02_any | quiet | fill fraction | 50-99% | 118 | 0.11 | 9.36 | 0.93 | 19.22 | 394.89 |
| vt_v3p_m0.02_any | quiet | fill fraction | <50% | 166 | 0.15 | 10.81 | -0.51 | 21.79 | 184.47 |
| vt_v3p_m0.02_any | quiet | fill fraction | full | 827 | 0.74 | 8.74 | -0.67 | 19.46 | 3,244.53 |
| vt_v3p_m0.02_any | busy | rival print in hold at our levels | no | 292 | 0.55 | -0.10 | -3.62 | 4.01 | -43.76 |
| vt_v3p_m0.02_any | busy | rival print in hold at our levels | yes | 239 | 0.45 | -3.08 | -10.82 | 4.52 | -1,225.01 |
| vt_v3p_m0.02_any | busy | rival print in hold, any level | no | 291 | 0.55 | 0.02 | -3.40 | 4.05 | 9.66 |
| vt_v3p_m0.02_any | busy | rival print in hold, any level | yes | 240 | 0.45 | -3.21 | -10.92 | 4.37 | -1,278.44 |
| vt_v3p_m0.02_any | busy | share of our fill a rival took <= 50 ms later | 0 | 371 | 0.70 | -3.27 | -9.68 | 3.00 | -1,921.06 |
| vt_v3p_m0.02_any | busy | share of our fill a rival took <= 50 ms later | 0-50% | 82 | 0.15 | 4.27 | -0.05 | 9.54 | 628.26 |
| vt_v3p_m0.02_any | busy | share of our fill a rival took <= 50 ms later | >50% | 78 | 0.15 | 0.29 | -8.08 | 7.71 | 24.02 |
| vt_v3p_m0.02_any | busy | share of our fill gone <= 50 ms later | 0 | 328 | 0.62 | -3.32 | -8.96 | 2.10 | -1,733.11 |
| vt_v3p_m0.02_any | busy | share of our fill gone <= 50 ms later | 0-50% | 91 | 0.17 | -1.27 | -8.65 | 5.93 | -200.05 |
| vt_v3p_m0.02_any | busy | share of our fill gone <= 50 ms later | >50% | 112 | 0.21 | 4.92 | 0.40 | 9.70 | 664.38 |
| vt_v3p_m0.02_any | busy | same-side prints in last 1 s (decision time) | 0 | 76 | 0.14 | 2.50 | -6.71 | 11.46 | 215.04 |
| vt_v3p_m0.02_any | busy | same-side prints in last 1 s (decision time) | 1-2 | 149 | 0.28 | -0.34 | -4.30 | 4.32 | -72.10 |
| vt_v3p_m0.02_any | busy | same-side prints in last 1 s (decision time) | 3+ | 306 | 0.58 | -2.73 | -9.95 | 4.32 | -1,411.72 |
| vt_v3p_m0.02_any | busy | our-view depth at seen price (decision time) | 120+ | 247 | 0.47 | -3.28 | -7.45 | 1.25 | -1,153.81 |
| vt_v3p_m0.02_any | busy | our-view depth at seen price (decision time) | 30-120 | 169 | 0.32 | -0.61 | -9.50 | 8.12 | -160.06 |
| vt_v3p_m0.02_any | busy | our-view depth at seen price (decision time) | <30 | 115 | 0.22 | 0.22 | -4.34 | 4.39 | 45.09 |
| vt_v3p_m0.02_any | busy | book messages in last 1 s (decision time) | 1500+ | 231 | 0.44 | -2.80 | -12.60 | 6.76 | -1,061.91 |
| vt_v3p_m0.02_any | busy | book messages in last 1 s (decision time) | 500-1500 | 246 | 0.46 | -1.36 | -4.07 | 1.42 | -496.31 |
| vt_v3p_m0.02_any | busy | book messages in last 1 s (decision time) | <500 | 54 | 0.10 | 4.01 | -5.23 | 12.97 | 289.45 |
| vt_v3p_m0.02_any | busy | fill fraction | 50-99% | 54 | 0.10 | 1.64 | -5.53 | 10.60 | 125.94 |
| vt_v3p_m0.02_any | busy | fill fraction | <50% | 88 | 0.17 | 7.61 | 2.74 | 12.28 | 306.45 |
| vt_v3p_m0.02_any | busy | fill fraction | full | 389 | 0.73 | -2.43 | -7.94 | 3.12 | -1,701.17 |

## Race curve: match e ms later than the simulator assumes (decisions fixed)
| group | arm | e ms | fills/day | sh/fill | mk10 c/$ | mk10 $/day | L |
|---|---|---|---|---|---|---|---|
| quiet | micf | -50 | 655.45 | 46.13 | 9.70 | 1,957.22 |  |
| quiet | micf | -25 | 516.41 | 49.14 | 8.42 | 1,460.50 |  |
| quiet | micf | 0 | 415.68 | 50.84 | 7.91 | 1,148.22 |  |
| quiet | micf | 10 | 397.24 | 50.52 | 7.50 | 1,030.22 |  |
| quiet | micf | 25 | 380.22 | 50.40 | 6.98 | 918.73 |  |
| quiet | micf | 50 | 363.19 | 51.25 | 6.73 | 858.36 |  |
| quiet | micf | 100 | 334.82 | 54.14 | 5.66 | 704.84 |  |
| quiet | micf | 200 | 317.79 | 55.69 | 4.19 | 514.02 |  |
| quiet | vt_v1_m0.03_any | -50 | 749.08 | 40.91 | 21.41 | 2,937.82 |  |
| quiet | vt_v1_m0.03_any | -25 | 557.56 | 44.10 | 19.48 | 2,226.19 |  |
| quiet | vt_v1_m0.03_any | 0 | 442.64 | 47.61 | 19.58 | 1,943.93 |  |
| quiet | vt_v1_m0.03_any | 10 | 421.36 | 48.37 | 19.14 | 1,854.07 |  |
| quiet | vt_v1_m0.03_any | 25 | 405.75 | 48.18 | 18.72 | 1,751.21 |  |
| quiet | vt_v1_m0.03_any | 50 | 368.87 | 49.62 | 18.08 | 1,605.22 |  |
| quiet | vt_v1_m0.03_any | 100 | 340.49 | 50.50 | 17.95 | 1,504.61 |  |
| quiet | vt_v1_m0.03_any | 200 | 316.37 | 50.79 | 15.06 | 1,186.01 |  |
| quiet | vt_v1_m0.02_trigger | -50 | 709.36 | 39.78 | 19.56 | 2,401.25 |  |
| quiet | vt_v1_m0.02_trigger | -25 | 478.11 | 43.50 | 19.18 | 1,807.39 |  |
| quiet | vt_v1_m0.02_trigger | 0 | 356.10 | 46.82 | 18.73 | 1,387.46 |  |
| quiet | vt_v1_m0.02_trigger | 10 | 326.31 | 47.41 | 18.91 | 1,299.00 |  |
| quiet | vt_v1_m0.02_trigger | 25 | 306.44 | 47.57 | 19.13 | 1,241.01 |  |
| quiet | vt_v1_m0.02_trigger | 50 | 272.39 | 49.75 | 19.45 | 1,165.39 |  |
| quiet | vt_v1_m0.02_trigger | 100 | 244.02 | 50.12 | 17.52 | 922.48 |  |
| quiet | vt_v1_m0.02_trigger | 200 | 212.81 | 51.79 | 12.82 | 606.48 |  |
| quiet | vt_v3p_m0.02_any | -50 | 1,979.11 | 48.54 | 9.92 | 4,937.77 |  |
| quiet | vt_v3p_m0.02_any | -25 | 1,740.77 | 49.91 | 9.20 | 4,201.81 |  |
| quiet | vt_v3p_m0.02_any | 0 | 1,576.20 | 51.64 | 8.89 | 3,823.88 |  |
| quiet | vt_v3p_m0.02_any | 10 | 1,526.54 | 52.24 | 8.88 | 3,742.24 |  |
| quiet | vt_v3p_m0.02_any | 25 | 1,493.91 | 52.29 | 8.81 | 3,646.19 |  |
| quiet | vt_v3p_m0.02_any | 50 | 1,432.91 | 52.81 | 9.40 | 3,769.21 |  |
| quiet | vt_v3p_m0.02_any | 100 | 1,390.34 | 53.07 | 8.29 | 3,211.62 |  |
| quiet | vt_v3p_m0.02_any | 200 | 1,346.36 | 53.33 | 7.82 | 2,932.18 |  |
| busy | micf | -50 | 1,290.00 | 48.44 | 2.52 | 935.34 |  |
| busy | micf | -25 | 1,098.00 | 50.20 | 0.75 | 247.37 |  |
| busy | micf | 0 | 936.00 | 52.62 | 1.27 | 375.15 |  |
| busy | micf | 10 | 918.00 | 52.79 | 0.96 | 277.45 |  |
| busy | micf | 25 | 888.00 | 54.39 | 1.03 | 296.01 |  |
| busy | micf | 50 | 876.00 | 55.04 | 0.39 | 111.94 |  |
| busy | micf | 100 | 852.00 | 55.47 | 1.13 | 315.05 |  |
| busy | micf | 200 | 840.00 | 54.63 | 0.02 | 5.61 |  |
| busy | vt_v1_m0.03_any | -50 | 1,704.00 | 42.41 | 10.84 | 3,184.73 |  |
| busy | vt_v1_m0.03_any | -25 | 1,386.00 | 43.37 | 8.23 | 1,991.47 |  |
| busy | vt_v1_m0.03_any | 0 | 948.00 | 50.74 | 7.68 | 1,450.25 |  |
| busy | vt_v1_m0.03_any | 10 | 882.00 | 51.94 | 4.50 | 805.51 |  |
| busy | vt_v1_m0.03_any | 25 | 804.00 | 54.01 | 4.63 | 787.35 |  |
| busy | vt_v1_m0.03_any | 50 | 762.00 | 53.29 | 3.25 | 516.57 |  |
| busy | vt_v1_m0.03_any | 100 | 714.00 | 53.04 | 3.76 | 559.85 |  |
| busy | vt_v1_m0.03_any | 200 | 660.00 | 54.16 | 5.55 | 769.05 |  |
| busy | vt_v1_m0.02_trigger | -50 | 2,340.00 | 44.02 | 5.86 | 2,243.87 |  |
| busy | vt_v1_m0.02_trigger | -25 | 1,908.00 | 45.83 | 4.33 | 1,399.19 |  |
| busy | vt_v1_m0.02_trigger | 0 | 1,428.00 | 49.84 | 3.47 | 866.37 |  |
| busy | vt_v1_m0.02_trigger | 10 | 1,344.00 | 50.93 | 2.53 | 601.42 |  |
| busy | vt_v1_m0.02_trigger | 25 | 1,278.00 | 51.30 | 2.69 | 603.94 |  |
| busy | vt_v1_m0.02_trigger | 50 | 1,224.00 | 51.37 | 1.74 | 368.22 |  |
| busy | vt_v1_m0.02_trigger | 100 | 1,098.00 | 52.12 | 1.33 | 251.02 |  |
| busy | vt_v1_m0.02_trigger | 200 | 990.00 | 55.54 | 0.61 | 107.82 |  |
| busy | vt_v3p_m0.02_any | -50 | 4,350.00 | 47.02 | 0.58 | 579.18 |  |
| busy | vt_v3p_m0.02_any | -25 | 3,852.00 | 48.03 | -0.59 | -539.91 |  |
| busy | vt_v3p_m0.02_any | 0 | 3,186.00 | 51.16 | -1.56 | -1,268.78 |  |
| busy | vt_v3p_m0.02_any | 10 | 3,054.00 | 51.95 | -1.95 | -1,546.04 |  |
| busy | vt_v3p_m0.02_any | 25 | 2,934.00 | 52.25 | -2.08 | -1,603.00 |  |
| busy | vt_v3p_m0.02_any | 50 | 2,844.00 | 52.18 | -2.15 | -1,601.24 |  |
| busy | vt_v3p_m0.02_any | 100 | 2,592.00 | 53.62 | -2.27 | -1,595.20 |  |
| busy | vt_v3p_m0.02_any | 200 | 2,418.00 | 54.04 | -2.33 | -1,526.27 |  |
| quiet | micf | -50 | 770.36 | 46.46 | 10.39 | 2,420.68 | -40.00 |
| quiet | micf | -25 | 699.43 | 46.00 | 9.88 | 2,110.97 | -40.00 |
| quiet | micf | 0 | 590.19 | 47.95 | 8.95 | 1,713.25 | -40.00 |
| quiet | micf | 10 | 544.79 | 48.43 | 8.57 | 1,541.25 | -40.00 |
| quiet | micf | 25 | 471.01 | 49.76 | 8.01 | 1,282.15 | -40.00 |
| quiet | micf | 50 | 397.24 | 50.52 | 7.50 | 1,030.22 | -40.00 |
| quiet | micf | 100 | 360.35 | 51.21 | 6.93 | 874.08 | -40.00 |
| quiet | micf | 200 | 327.72 | 55.27 | 4.77 | 599.25 | -40.00 |
| quiet | vt_v1_m0.03_any | -50 | 1,715.23 | 44.48 | 12.84 | 4,248.68 | -40.00 |
| quiet | vt_v1_m0.03_any | -25 | 1,588.97 | 43.51 | 12.48 | 3,798.23 | -40.00 |
| quiet | vt_v1_m0.03_any | 0 | 1,373.32 | 43.79 | 11.34 | 3,030.75 | -40.00 |
| quiet | vt_v1_m0.03_any | 10 | 1,234.29 | 45.07 | 10.55 | 2,644.23 | -40.00 |
| quiet | vt_v1_m0.03_any | 25 | 1,041.34 | 47.48 | 9.77 | 2,181.26 | -40.00 |
| quiet | vt_v1_m0.03_any | 50 | 906.56 | 49.26 | 8.33 | 1,680.17 | -40.00 |
| quiet | vt_v1_m0.03_any | 100 | 800.16 | 49.71 | 8.90 | 1,590.27 | -40.00 |
| quiet | vt_v1_m0.03_any | 200 | 734.90 | 50.56 | 7.98 | 1,319.92 | -40.00 |
| quiet | vt_v1_m0.02_trigger | -50 | 1,496.75 | 44.79 | 11.79 | 3,904.26 | -40.00 |
| quiet | vt_v1_m0.02_trigger | -25 | 1,396.02 | 42.87 | 11.09 | 3,328.23 | -40.00 |
| quiet | vt_v1_m0.02_trigger | 0 | 1,197.40 | 43.36 | 10.30 | 2,719.77 | -40.00 |
| quiet | vt_v1_m0.02_trigger | 10 | 1,045.60 | 45.23 | 9.90 | 2,411.77 | -40.00 |
| quiet | vt_v1_m0.02_trigger | 25 | 851.23 | 47.75 | 9.47 | 1,982.73 | -40.00 |
| quiet | vt_v1_m0.02_trigger | 50 | 702.27 | 50.29 | 8.93 | 1,618.98 | -40.00 |
| quiet | vt_v1_m0.02_trigger | 100 | 595.86 | 51.50 | 8.92 | 1,398.23 | -40.00 |
| quiet | vt_v1_m0.02_trigger | 200 | 524.93 | 54.44 | 6.93 | 1,006.40 | -40.00 |
| busy | micf | -50 | 1,500.00 | 48.24 | 3.92 | 1,672.90 | -40.00 |
| busy | micf | -25 | 1,368.00 | 48.66 | 3.02 | 1,204.28 | -40.00 |
| busy | micf | 0 | 1,224.00 | 48.52 | 2.15 | 759.50 | -40.00 |
| busy | micf | 10 | 1,134.00 | 50.05 | 1.29 | 439.65 | -40.00 |
| busy | micf | 25 | 990.00 | 52.35 | 1.18 | 367.98 | -40.00 |
| busy | micf | 50 | 918.00 | 52.79 | 0.96 | 277.45 | -40.00 |
| busy | micf | 100 | 876.00 | 54.85 | 0.41 | 116.03 | -40.00 |
| busy | micf | 200 | 828.00 | 55.80 | -0.15 | -41.69 | -40.00 |
| busy | vt_v1_m0.03_any | -50 | 5,700.00 | 48.97 | 4.48 | 4,674.42 | -40.00 |
| busy | vt_v1_m0.03_any | -25 | 5,490.00 | 47.06 | 3.62 | 3,481.30 | -40.00 |
| busy | vt_v1_m0.03_any | 0 | 5,148.00 | 46.73 | 2.58 | 2,301.45 | -40.00 |
| busy | vt_v1_m0.03_any | 10 | 4,854.00 | 47.15 | 2.00 | 1,690.08 | -40.00 |
| busy | vt_v1_m0.03_any | 25 | 4,224.00 | 49.16 | 1.02 | 769.55 | -40.00 |
| busy | vt_v1_m0.03_any | 50 | 3,564.00 | 52.05 | -0.28 | -184.64 | -40.00 |
| busy | vt_v1_m0.03_any | 100 | 3,168.00 | 52.91 | -1.56 | -917.01 | -40.00 |
| busy | vt_v1_m0.03_any | 200 | 2,994.00 | 53.95 | -1.44 | -810.57 | -40.00 |
| busy | vt_v1_m0.02_trigger | -50 | 5,844.00 | 48.85 | 2.76 | 3,386.06 | -40.00 |
| busy | vt_v1_m0.02_trigger | -25 | 5,526.00 | 48.12 | 1.66 | 1,902.92 | -40.00 |
| busy | vt_v1_m0.02_trigger | 0 | 5,154.00 | 47.79 | 1.01 | 1,080.80 | -40.00 |
| busy | vt_v1_m0.02_trigger | 10 | 4,884.00 | 48.32 | 0.47 | 479.56 | -40.00 |
| busy | vt_v1_m0.02_trigger | 25 | 4,338.00 | 50.14 | -0.35 | -324.84 | -40.00 |
| busy | vt_v1_m0.02_trigger | 50 | 3,750.00 | 52.16 | -1.04 | -861.16 | -40.00 |
| busy | vt_v1_m0.02_trigger | 100 | 3,378.00 | 53.04 | -1.46 | -1,104.66 | -40.00 |
| busy | vt_v1_m0.02_trigger | 200 | 3,156.00 | 54.19 | -1.88 | -1,338.60 | -40.00 |

## Fill models, L = 0
| group | fill model | arm | L | fills/day | mk10 c/$ | mk10 $/day | gain vs micf $/day |
|---|---|---|---|---|---|---|---|
| unseen | base | micf | 0 | 515.19 | +5.7 [+3.0, +8.5] | +1,000 [+509, +1,499] |  |
| unseen | base | vt_v1_m0.03_any | 0 | 539.28 | +15.9 [+8.7, +24.1] | +1,850 [+980, +2,878] | +849 [-51, +1,879] P<=0 0.03 |
| unseen | base | vt_v1_m0.02_trigger | 0 | 561.08 | +12.0 [+7.7, +16.4] | +1,288 [+862, +1,746] | +287 [-137, +639] P<=0 0.09 |
| unseen | base | vt_v3p_m0.02_any | 0 | 1,884.05 | +5.7 [-0.8, +12.9] | +2,850 [-438, +6,461] | +1,850 [-1,236, +5,345] P<=0 0.14 |
| unseen | comp | micf | 0 | 442.90 | +3.9 [+1.0, +6.8] | +540 [+139, +934] |  |
| unseen | comp | vt_v1_m0.03_any | 0 | 433.72 | +11.4 [+4.6, +18.7] | +946 [+392, +1,534] | +406 [-149, +982] P<=0 0.08 |
| unseen | comp | vt_v1_m0.02_trigger | 0 | 447.49 | +10.0 [+5.0, +15.5] | +763 [+402, +1,136] | +224 [-99, +511] P<=0 0.09 |
| unseen | comp | vt_v3p_m0.02_any | 0 | 1,648.83 | +4.1 [-2.6, +11.7] | +1,588 [-1,042, +4,682] | +1,048 [-1,457, +3,999] P<=0 0.24 |
| unseen | e+10 | micf | 0 | 496.83 | +5.3 [+2.6, +8.0] | +886 [+424, +1,350] |  |
| unseen | e+10 | vt_v1_m0.03_any | 0 | 509.45 | +14.7 [+7.6, +22.6] | +1,654 [+841, +2,631] | +767 [-60, +1,702] P<=0 0.04 |
| unseen | e+10 | vt_v1_m0.02_trigger | 0 | 520.92 | +11.5 [+7.2, +16.2] | +1,166 [+758, +1,598] | +279 [-120, +622] P<=0 0.09 |
| unseen | e+10 | vt_v3p_m0.02_any | 0 | 1,818.65 | +5.5 [-0.9, +12.8] | +2,731 [-466, +6,377] | +1,845 [-1,224, +5,327] P<=0 0.14 |
| unseen | e+25 | micf | 0 | 477.32 | +5.0 [+2.2, +7.7] | +800 [+350, +1,257] |  |
| unseen | e+25 | vt_v1_m0.03_any | 0 | 481.91 | +14.5 [+7.1, +22.6] | +1,567 [+759, +2,505] | +767 [-48, +1,685] P<=0 0.03 |
| unseen | e+25 | vt_v1_m0.02_trigger | 0 | 492.24 | +11.7 [+7.1, +16.8] | +1,119 [+706, +1,553] | +320 [-89, +683] P<=0 0.06 |
| unseen | e+25 | vt_v3p_m0.02_any | 0 | 1,769.31 | +5.5 [-0.9, +12.6] | +2,642 [-456, +6,218] | +1,843 [-1,142, +5,305] P<=0 0.13 |
| unseen | e+50 | micf | 0 | 461.26 | +4.5 [+1.7, +7.3] | +716 [+261, +1,157] |  |
| unseen | e+50 | vt_v1_m0.03_any | 0 | 444.05 | +13.7 [+5.4, +22.8] | +1,397 [+560, +2,352] | +681 [-156, +1,628] P<=0 0.05 |
| unseen | e+50 | vt_v1_m0.02_trigger | 0 | 454.37 | +11.4 [+6.7, +16.6] | +1,013 [+623, +1,428] | +297 [-93, +653] P<=0 0.07 |
| unseen | e+50 | vt_v3p_m0.02_any | 0 | 1,702.76 | +5.9 [-0.8, +13.3] | +2,742 [-376, +6,409] | +2,027 [-1,046, +5,531] P<=0 0.11 |
| unseen | e-25 | micf | 0 | 627.63 | +6.0 [+3.6, +8.4] | +1,229 [+718, +1,758] |  |
| unseen | e-25 | vt_v1_m0.03_any | 0 | 715.98 | +15.7 [+9.5, +22.2] | +2,181 [+1,316, +3,171] | +953 [+124, +1,909] P<=0 0.01 |
| unseen | e-25 | vt_v1_m0.02_trigger | 0 | 751.55 | +12.5 [+8.9, +16.6] | +1,729 [+1,247, +2,224] | +501 [+61, +873] P<=0 0.01 |
| unseen | e-25 | vt_v3p_m0.02_any | 0 | 2,144.51 | +6.1 [-0.1, +12.8] | +3,295 [-54, +6,952] | +2,067 [-1,058, +5,548] P<=0 0.12 |
| quiet | base | micf | 0 | 415.68 | +7.9 [+4.7, +11.3] | +1,148 [+675, +1,638] |  |
| quiet | base | vt_v1_m0.03_any | 0 | 442.64 | +19.6 [+9.6, +31.3] | +1,944 [+903, +3,091] | +796 [-232, +2,030] P<=0 0.09 |
| quiet | base | vt_v1_m0.02_trigger | 0 | 356.10 | +18.7 [+13.8, +24.0] | +1,387 [+948, +1,845] | +239 [-82, +513] P<=0 0.07 |
| quiet | base | vt_v3p_m0.02_any | 0 | 1,576.20 | +8.9 [+0.1, +18.6] | +3,824 [+39, +8,060] | +2,676 [-1,152, +6,923] P<=0 0.09 |
| quiet | comp | micf | 0 | 350.42 | +5.9 [+2.5, +9.6] | +645 [+268, +1,048] |  |
| quiet | comp | vt_v1_m0.03_any | 0 | 357.52 | +15.3 [+5.6, +26.2] | +1,089 [+410, +1,758] | +444 [-228, +1,137] P<=0 0.10 |
| quiet | comp | vt_v1_m0.02_trigger | 0 | 269.56 | +16.7 [+11.0, +22.8] | +884 [+543, +1,259] | +239 [+33, +446] P<=0 0.01 |
| quiet | comp | vt_v3p_m0.02_any | 0 | 1,383.25 | +7.6 [-1.5, +18.3] | +2,504 [-495, +6,054] | +1,859 [-1,199, +5,408] P<=0 0.13 |
| quiet | e+10 | micf | 0 | 397.24 | +7.5 [+4.3, +11.0] | +1,030 [+574, +1,513] |  |
| quiet | e+10 | vt_v1_m0.03_any | 0 | 421.36 | +19.1 [+9.1, +30.7] | +1,854 [+887, +2,942] | +824 [-159, +1,980] P<=0 0.07 |
| quiet | e+10 | vt_v1_m0.02_trigger | 0 | 326.31 | +18.9 [+14.1, +24.0] | +1,299 [+889, +1,737] | +269 [-40, +537] P<=0 0.04 |
| quiet | e+10 | vt_v3p_m0.02_any | 0 | 1,526.54 | +8.9 [+0.1, +18.6] | +3,742 [+38, +7,934] | +2,712 [-1,020, +6,896] P<=0 0.08 |
| quiet | e+25 | micf | 0 | 380.22 | +7.0 [+3.7, +10.7] | +919 [+475, +1,400] |  |
| quiet | e+25 | vt_v1_m0.03_any | 0 | 405.75 | +18.7 [+8.4, +30.6] | +1,751 [+793, +2,837] | +832 [-130, +1,982] P<=0 0.05 |
| quiet | e+25 | vt_v1_m0.02_trigger | 0 | 306.44 | +19.1 [+14.3, +24.3] | +1,241 [+834, +1,679] | +322 [+17, +590] P<=0 0.02 |
| quiet | e+25 | vt_v3p_m0.02_any | 0 | 1,493.91 | +8.8 [+0.1, +18.4] | +3,646 [+46, +7,730] | +2,727 [-884, +6,815] P<=0 0.08 |
| quiet | e+50 | micf | 0 | 363.19 | +6.7 [+3.4, +10.6] | +858 [+419, +1,329] |  |
| quiet | e+50 | vt_v1_m0.03_any | 0 | 368.87 | +18.1 [+6.8, +31.1] | +1,605 [+605, +2,687] | +747 [-268, +1,895] P<=0 0.09 |
| quiet | e+50 | vt_v1_m0.02_trigger | 0 | 272.39 | +19.5 [+13.9, +25.2] | +1,165 [+771, +1,599] | +307 [+1, +582] P<=0 0.03 |
| quiet | e+50 | vt_v3p_m0.02_any | 0 | 1,432.91 | +9.4 [+0.2, +19.4] | +3,769 [+99, +7,915] | +2,911 [-854, +7,133] P<=0 0.07 |
| quiet | e-25 | micf | 0 | 516.41 | +8.4 [+5.5, +11.5] | +1,460 [+928, +2,003] |  |
| quiet | e-25 | vt_v1_m0.03_any | 0 | 557.56 | +19.5 [+10.5, +29.7] | +2,226 [+1,206, +3,342] | +766 [-232, +1,854] P<=0 0.08 |
| quiet | e-25 | vt_v1_m0.02_trigger | 0 | 478.11 | +19.2 [+14.5, +24.3] | +1,807 [+1,308, +2,321] | +347 [-14, +627] P<=0 0.03 |
| quiet | e-25 | vt_v3p_m0.02_any | 0 | 1,740.77 | +9.2 [+0.9, +18.3] | +4,202 [+413, +8,474] | +2,741 [-1,199, +7,002] P<=0 0.09 |
| busy | base | micf | 0 | 936.00 | +1.3 [-3.5, +6.1] | +375 [-908, +1,983] |  |
| busy | base | vt_v1_m0.03_any | 0 | 948.00 | +7.7 [+1.2, +15.5] | +1,450 [+226, +2,834] | +1,075 [-622, +2,705] P<=0 0.10 |
| busy | base | vt_v1_m0.02_trigger | 0 | 1,428.00 | +3.5 [-1.6, +9.4] | +866 [-444, +2,171] | +491 [-1,257, +2,075] P<=0 0.28 |
| busy | base | vt_v3p_m0.02_any | 0 | 3,186.00 | -1.6 [-6.5, +3.5] | -1,269 [-5,677, +2,835] | -1,644 [-5,996, +2,287] P<=0 0.77 |
| busy | comp | micf | 0 | 834.00 | +0.4 [-4.5, +5.3] | +95 [-1,038, +1,402] |  |
| busy | comp | vt_v1_m0.03_any | 0 | 756.00 | +2.5 [-3.7, +9.2] | +342 [-539, +1,199] | +248 [-1,049, +1,377] P<=0 0.33 |
| busy | comp | vt_v1_m0.02_trigger | 0 | 1,200.00 | +1.5 [-4.3, +8.8] | +255 [-900, +1,353] | +161 [-1,221, +1,411] P<=0 0.41 |
| busy | comp | vt_v3p_m0.02_any | 0 | 2,772.00 | -3.6 [-8.5, +1.4] | -2,285 [-5,657, +870] | -2,380 [-5,870, +681] P<=0 0.92 |
| busy | e+10 | micf | 0 | 918.00 | +1.0 [-3.6, +5.5] | +277 [-940, +1,712] |  |
| busy | e+10 | vt_v1_m0.03_any | 0 | 882.00 | +4.5 [-0.9, +9.9] | +806 [-159, +1,786] | +528 [-891, +1,769] P<=0 0.21 |
| busy | e+10 | vt_v1_m0.02_trigger | 0 | 1,344.00 | +2.5 [-2.4, +8.3] | +601 [-656, +1,793] | +324 [-1,314, +1,802] P<=0 0.34 |
| busy | e+10 | vt_v3p_m0.02_any | 0 | 3,054.00 | -1.9 [-6.9, +3.3] | -1,546 [-5,936, +2,583] | -1,823 [-6,101, +2,085] P<=0 0.80 |
| busy | e+25 | micf | 0 | 888.00 | +1.0 [-3.6, +5.6] | +296 [-913, +1,736] |  |
| busy | e+25 | vt_v1_m0.03_any | 0 | 804.00 | +4.6 [-1.0, +10.4] | +787 [-182, +1,767] | +491 [-925, +1,711] P<=0 0.22 |
| busy | e+25 | vt_v1_m0.02_trigger | 0 | 1,278.00 | +2.7 [-2.8, +9.6] | +604 [-716, +1,922] | +308 [-1,289, +1,881] P<=0 0.36 |
| busy | e+25 | vt_v3p_m0.02_any | 0 | 2,934.00 | -2.1 [-7.1, +3.2] | -1,603 [-5,928, +2,415] | -1,899 [-6,051, +1,881] P<=0 0.82 |
| busy | e+50 | micf | 0 | 876.00 | +0.4 [-4.1, +5.1] | +112 [-1,086, +1,546] |  |
| busy | e+50 | vt_v1_m0.03_any | 0 | 762.00 | +3.3 [-2.3, +9.0] | +517 [-371, +1,434] | +405 [-913, +1,544] P<=0 0.25 |
| busy | e+50 | vt_v1_m0.02_trigger | 0 | 1,224.00 | +1.7 [-3.4, +7.7] | +368 [-820, +1,501] | +256 [-1,337, +1,672] P<=0 0.38 |
| busy | e+50 | vt_v3p_m0.02_any | 0 | 2,844.00 | -2.2 [-7.2, +3.0] | -1,601 [-5,650, +2,166] | -1,713 [-5,506, +1,779] P<=0 0.81 |
| busy | e-25 | micf | 0 | 1,098.00 | +0.7 [-3.4, +5.2] | +247 [-1,014, +1,870] |  |
| busy | e-25 | vt_v1_m0.03_any | 0 | 1,386.00 | +8.2 [+3.6, +12.6] | +1,991 [+818, +3,231] | +1,744 [+314, +3,033] P<=0 0.01 |
| busy | e-25 | vt_v1_m0.02_trigger | 0 | 1,908.00 | +4.3 [-0.0, +9.2] | +1,399 [-11, +2,766] | +1,152 [-560, +2,813] P<=0 0.09 |
| busy | e-25 | vt_v3p_m0.02_any | 0 | 3,852.00 | -0.6 [-5.6, +4.4] | -540 [-5,363, +3,948] | -787 [-5,518, +3,441] P<=0 0.60 |

## Fill models, L = -40
| group | fill model | arm | L | fills/day | mk10 c/$ | mk10 $/day | gain vs micf $/day |
|---|---|---|---|---|---|---|---|
| unseen | base | micf | -40 | 711.39 | +6.9 [+4.5, +9.3] | +1,531 [+992, +2,090] |  |
| unseen | base | vt_v1_m0.03_any | -40 | 2,095.17 | +7.5 [+4.6, +10.7] | +2,891 [+1,819, +4,035] | +1,360 [+360, +2,461] P<=0 0.00 |
| unseen | base | vt_v1_m0.02_trigger | -40 | 1,954.04 | +5.8 [+4.0, +7.9] | +2,406 [+1,755, +3,097] | +875 [+400, +1,282] P<=0 0.00 |
| unseen | comp | micf | -40 | 497.98 | +4.6 [+1.8, +7.4] | +690 [+268, +1,099] |  |
| unseen | comp | vt_v1_m0.03_any | -40 | 1,431.97 | +3.4 [-0.1, +7.2] | +839 [-24, +1,687] | +149 [-698, +938] P<=0 0.36 |
| unseen | comp | vt_v1_m0.02_trigger | -40 | 1,324.11 | +3.1 [+1.3, +5.3] | +841 [+367, +1,314] | +151 [-286, +537] P<=0 0.25 |
| unseen | e+10 | micf | -40 | 657.47 | +6.3 [+3.8, +8.7] | +1,331 [+797, +1,875] |  |
| unseen | e+10 | vt_v1_m0.03_any | -40 | 1,926.50 | +6.8 [+3.8, +10.1] | +2,462 [+1,424, +3,545] | +1,131 [+133, +2,177] P<=0 0.01 |
| unseen | e+10 | vt_v1_m0.02_trigger | -40 | 1,779.63 | +5.2 [+3.5, +7.3] | +2,042 [+1,434, +2,695] | +712 [+228, +1,122] P<=0 0.00 |
| unseen | e+25 | micf | -40 | 570.26 | +5.9 [+3.2, +8.3] | +1,107 [+605, +1,608] |  |
| unseen | e+25 | vt_v1_m0.03_any | -40 | 1,649.98 | +5.9 [+2.6, +9.5] | +1,911 [+876, +3,011] | +804 [-244, +1,851] P<=0 0.07 |
| unseen | e+25 | vt_v1_m0.02_trigger | -40 | 1,518.02 | +4.4 [+2.6, +6.6] | +1,541 [+977, +2,112] | +434 [-37, +831] P<=0 0.04 |
| unseen | e+50 | micf | -40 | 496.83 | +5.3 [+2.6, +8.0] | +886 [+424, +1,350] |  |
| unseen | e+50 | vt_v1_m0.03_any | -40 | 1,414.76 | +4.6 [+1.0, +8.6] | +1,324 [+315, +2,379] | +437 [-615, +1,453] P<=0 0.20 |
| unseen | e+50 | vt_v1_m0.02_trigger | -40 | 1,285.10 | +3.7 [+1.9, +6.0] | +1,145 [+606, +1,694] | +258 [-215, +668] P<=0 0.14 |
| unseen | e-25 | micf | -40 | 827.28 | +7.8 [+5.5, +10.1] | +1,938 [+1,339, +2,545] |  |
| unseen | e-25 | vt_v1_m0.03_any | -40 | 2,334.98 | +8.7 [+5.8, +11.7] | +3,738 [+2,561, +4,941] | +1,800 [+727, +2,948] P<=0 0.00 |
| unseen | e-25 | vt_v1_m0.02_trigger | -40 | 2,185.82 | +6.6 [+4.9, +8.7] | +3,056 [+2,356, +3,811] | +1,118 [+619, +1,567] P<=0 0.00 |
| quiet | base | micf | -40 | 590.19 | +9.0 [+6.2, +11.9] | +1,713 [+1,161, +2,279] |  |
| quiet | base | vt_v1_m0.03_any | -40 | 1,373.32 | +11.3 [+6.6, +16.6] | +3,031 [+1,784, +4,252] | +1,317 [+119, +2,548] P<=0 0.01 |
| quiet | base | vt_v1_m0.02_trigger | -40 | 1,197.40 | +10.3 [+8.0, +12.7] | +2,720 [+2,057, +3,415] | +1,007 [+685, +1,320] P<=0 0.00 |
| quiet | comp | micf | -40 | 407.17 | +6.4 [+3.3, +9.8] | +803 [+410, +1,226] |  |
| quiet | comp | vt_v1_m0.03_any | -40 | 906.56 | +6.8 [+1.0, +12.9] | +1,165 [+184, +2,048] | +362 [-588, +1,242] P<=0 0.23 |
| quiet | comp | vt_v1_m0.02_trigger | -40 | 732.06 | +8.0 [+5.5, +10.7] | +1,302 [+870, +1,780] | +499 [+262, +748] P<=0 0.00 |
| quiet | e+10 | micf | -40 | 544.79 | +8.6 [+5.7, +11.5] | +1,541 [+997, +2,095] |  |
| quiet | e+10 | vt_v1_m0.03_any | -40 | 1,234.29 | +10.5 [+5.5, +16.0] | +2,644 [+1,431, +3,841] | +1,103 [-58, +2,261] P<=0 0.03 |
| quiet | e+10 | vt_v1_m0.02_trigger | -40 | 1,045.60 | +9.9 [+7.6, +12.4] | +2,412 [+1,788, +3,042] | +871 [+583, +1,161] P<=0 0.00 |
| quiet | e+25 | micf | -40 | 471.01 | +8.0 [+5.0, +11.2] | +1,282 [+767, +1,807] |  |
| quiet | e+25 | vt_v1_m0.03_any | -40 | 1,041.34 | +9.8 [+4.0, +16.2] | +2,181 [+940, +3,363] | +899 [-322, +2,102] P<=0 0.08 |
| quiet | e+25 | vt_v1_m0.02_trigger | -40 | 851.23 | +9.5 [+6.9, +12.2] | +1,983 [+1,391, +2,601] | +701 [+419, +988] P<=0 0.00 |
| quiet | e+50 | micf | -40 | 397.24 | +7.5 [+4.3, +11.0] | +1,030 [+574, +1,513] |  |
| quiet | e+50 | vt_v1_m0.03_any | -40 | 906.56 | +8.3 [+2.2, +15.2] | +1,680 [+467, +2,858] | +650 [-556, +1,842] P<=0 0.15 |
| quiet | e+50 | vt_v1_m0.02_trigger | -40 | 702.27 | +8.9 [+6.3, +11.8] | +1,619 [+1,098, +2,179] | +589 [+330, +851] P<=0 0.00 |
| quiet | e-25 | micf | -40 | 699.43 | +9.9 [+7.2, +12.6] | +2,111 [+1,504, +2,732] |  |
| quiet | e-25 | vt_v1_m0.03_any | -40 | 1,588.97 | +12.5 [+8.0, +17.2] | +3,798 [+2,491, +5,086] | +1,687 [+420, +2,933] P<=0 0.01 |
| quiet | e-25 | vt_v1_m0.02_trigger | -40 | 1,396.02 | +11.1 [+8.9, +13.3] | +3,328 [+2,597, +4,068] | +1,217 [+825, +1,577] P<=0 0.00 |
| busy | base | micf | -40 | 1,224.00 | +2.1 [-2.1, +6.6] | +760 [-704, +2,473] |  |
| busy | base | vt_v1_m0.03_any | -40 | 5,148.00 | +2.6 [+0.0, +5.2] | +2,301 [+9, +4,496] | +1,542 [-346, +3,514] P<=0 0.06 |
| busy | base | vt_v1_m0.02_trigger | -40 | 5,154.00 | +1.0 [-0.7, +3.0] | +1,081 [-878, +2,999] | +321 [-1,583, +2,065] P<=0 0.37 |
| busy | comp | micf | -40 | 882.00 | +0.8 [-4.2, +5.9] | +215 [-975, +1,638] |  |
| busy | comp | vt_v1_m0.03_any | -40 | 3,654.00 | -1.0 [-4.0, +2.2] | -540 [-2,399, +1,254] | -754 [-2,650, +1,060] P<=0 0.79 |
| busy | comp | vt_v1_m0.02_trigger | -40 | 3,828.00 | -1.5 [-3.5, +0.7] | -1,107 [-2,719, +461] | -1,322 [-3,240, +250] P<=0 0.94 |
| busy | e+10 | micf | -40 | 1,134.00 | +1.3 [-3.0, +5.9] | +440 [-951, +2,132] |  |
| busy | e+10 | vt_v1_m0.03_any | -40 | 4,854.00 | +2.0 [-0.6, +4.6] | +1,690 [-520, +3,734] | +1,250 [-733, +3,276] P<=0 0.10 |
| busy | e+10 | vt_v1_m0.02_trigger | -40 | 4,884.00 | +0.5 [-1.3, +2.6] | +480 [-1,447, +2,410] | +40 [-1,991, +1,923] P<=0 0.49 |
| busy | e+25 | micf | -40 | 990.00 | +1.2 [-3.3, +5.8] | +368 [-908, +1,977] |  |
| busy | e+25 | vt_v1_m0.03_any | -40 | 4,224.00 | +1.0 [-1.5, +3.8] | +770 [-1,203, +2,745] | +402 [-1,647, +2,409] P<=0 0.34 |
| busy | e+25 | vt_v1_m0.02_trigger | -40 | 4,338.00 | -0.3 [-2.0, +1.5] | -325 [-2,014, +1,271] | -693 [-2,653, +1,030] P<=0 0.76 |
| busy | e+50 | micf | -40 | 918.00 | +1.0 [-3.6, +5.5] | +277 [-940, +1,712] |  |
| busy | e+50 | vt_v1_m0.03_any | -40 | 3,564.00 | -0.3 [-3.0, +2.7] | -185 [-2,068, +1,659] | -462 [-2,424, +1,405] P<=0 0.69 |
| busy | e+50 | vt_v1_m0.02_trigger | -40 | 3,750.00 | -1.0 [-3.0, +1.1] | -861 [-2,691, +839] | -1,139 [-3,202, +624] P<=0 0.88 |
| busy | e-25 | micf | -40 | 1,368.00 | +3.0 [-1.0, +7.3] | +1,204 [-377, +3,043] |  |
| busy | e-25 | vt_v1_m0.03_any | -40 | 5,490.00 | +3.6 [+1.0, +6.5] | +3,481 [+945, +6,099] | +2,277 [+63, +4,566] P<=0 0.02 |
| busy | e-25 | vt_v1_m0.02_trigger | -40 | 5,526.00 | +1.7 [-0.2, +3.8] | +1,903 [-228, +3,960] | +699 [-1,314, +2,523] P<=0 0.24 |

## Bottom / top 5 markets (unseen windows, L = 0)
| arm | markets | fills | mk10 $ | mk10 c/$ | windows | rival in hold (our levels) | taken <= 50 ms later | pre1 mean | ev1 mean | mk10 $ at e+25 | mk10 $ comp | mk10 $ at e-25 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| micf | bottom 5 | 21 | -130.74 | -27.44 | dev3,ext,final | 0.38 | 0.04 | 10.24 | 2,233.86 | -133.60 | -131.10 | -129.54 |
| micf | top 5 | 38 | 327.85 | 29.00 | dev3,ext,final | 0.58 | 0.12 | 10.87 | 1,917.32 | 300.62 | 226.52 | 338.40 |
| micf | rest | 390 | 674.76 | 4.98 | dev3,ext,final | 0.54 | 0.10 | 9.25 | 1,895.53 | 529.94 | 374.88 | 827.85 |
| vt_v1_m0.03_any | bottom 5 | 33 | -256.02 | -35.96 | dev3,ext,final | 0.45 | 0.07 | 6.21 | 1,887.94 | -249.45 | -231.50 | -271.56 |
| vt_v1_m0.03_any | top 5 | 38 | 670.87 | 80.35 | dev3,ext,final | 0.71 | 0.06 | 22.32 | 3,517.84 | 558.36 | 356.49 | 572.87 |
| vt_v1_m0.03_any | rest | 399 | 1,197.06 | 13.92 | dev3,ext,final | 0.38 | 0.16 | 5.36 | 1,416.51 | 1,061.11 | 699.36 | 1,511.89 |
| vt_v1_m0.02_trigger | bottom 5 | 65 | -114.37 | -11.56 | ext,final | 0.32 | 0.08 | 3.75 | 1,368.46 | -119.02 | -111.27 | -96.34 |
| vt_v1_m0.02_trigger | top 5 | 28 | 269.43 | 50.00 | dev3,final | 0.32 | 0.12 | 4.46 | 1,129.64 | 249.98 | 193.78 | 288.67 |
| vt_v1_m0.02_trigger | rest | 396 | 967.30 | 12.32 | dev3,ext,final | 0.31 | 0.16 | 3.53 | 1,145.89 | 847.96 | 582.79 | 1,194.87 |
| vt_v3p_m0.02_any | bottom 5 | 140 | -1,407.42 | -35.16 | dev3,ext,final | 0.63 | 0.10 | 13.83 | 2,476.89 | -1,317.67 | -1,014.29 | -1,469.06 |
| vt_v3p_m0.02_any | top 5 | 127 | 2,476.88 | 76.85 | dev3,final | 0.59 | 0.04 | 13.30 | 2,599.14 | 2,367.10 | 1,942.25 | 2,466.58 |
| vt_v3p_m0.02_any | rest | 1375 | 1,414.37 | 3.85 | dev3,ext,final | 0.48 | 0.08 | 7.48 | 1,855.78 | 1,253.46 | 456.05 | 1,811.27 |

## Size rules: vt_v1_m0.03_any, L = 0
| group | arm | L | fill model | size | fills/day | sh/fill | mk10 c/$ | mk10 $/day | vs 60 sh $/day | gain vs micf $/day |
|---|---|---|---|---|---|---|---|---|---|---|
| select | vt_v1_m0.03_any | 0 | base | 60 | 574.00 | 47.09 | +14.3 [+7.8, +23.8] | +2,082 [+1,169, +3,103] |  |  |
| select | vt_v1_m0.03_any | 0 | base | s20 | 584.00 | 18.11 | +15.5 [+9.5, +24.5] | +884 [+531, +1,275] | -1,198 [-1,866, -648] P<=0 1.00 | +68 [-754, +844] P<=0 0.44 |
| select | vt_v1_m0.03_any | 0 | base | s40 | 580.00 | 33.41 | +14.7 [+8.4, +23.8] | +1,534 [+890, +2,250] | -548 [-868, -283] P<=0 1.00 | +717 [-141, +1,621] P<=0 0.05 |
| select | vt_v1_m0.03_any | 0 | base | s100 | 564.00 | 72.06 | +13.4 [+6.9, +23.4] | +2,956 [+1,559, +4,503] | +874 [+394, +1,422] P<=0 0.00 | +2,140 [+793, +3,710] P<=0 0.00 |
| select | vt_v1_m0.03_any | 0 | base | dk0.5 | 518.00 | 38.17 | +16.2 [+8.8, +28.1] | +1,696 [+1,014, +2,466] | -386 [-790, +1] P<=0 0.97 | +880 [+80, +1,744] P<=0 0.01 |
| select | vt_v1_m0.03_any | 0 | base | dk1 | 560.00 | 40.55 | +16.0 [+8.9, +26.8] | +1,931 [+1,148, +2,791] | -151 [-410, +123] P<=0 0.89 | +1,115 [+264, +2,089] P<=0 0.01 |
| select | vt_v1_m0.03_any | 0 | base | dk2 | 566.00 | 43.43 | +15.5 [+8.4, +25.9] | +2,032 [+1,196, +2,975] | -50 [-201, +136] P<=0 0.75 | +1,216 [+316, +2,237] P<=0 0.00 |
| select | vt_v1_m0.03_any | 0 | base | rv1_30 | 584.00 | 29.95 | +16.8 [+9.7, +28.8] | +1,545 [+914, +2,210] | -537 [-948, -166] P<=0 1.00 | +728 [-71, +1,582] P<=0 0.04 |
| select | vt_v1_m0.03_any | 0 | base | rv1_0 | 108.00 | 49.09 | +30.5 [+13.1, +73.2] | +717 [+330, +1,156] | -1,365 [-2,274, -588] P<=0 1.00 | -99 [-884, +630] P<=0 0.60 |
| select | vt_v1_m0.03_any | 0 | base | rv3_30 | 580.00 | 35.43 | +16.2 [+8.4, +28.5] | +1,763 [+992, +2,596] | -319 [-599, -73] P<=0 0.99 | +947 [+104, +1,875] P<=0 0.01 |
| select | vt_v1_m0.03_any | 0 | base | rv3_0 | 262.00 | 47.51 | +20.1 [+8.3, +43.5] | +1,250 [+559, +1,967] | -832 [-1,460, -300] P<=0 1.00 | +433 [-367, +1,246] P<=0 0.16 |
| select | vt_v1_m0.03_any | 0 | base | dk1_rv1 | 568.00 | 27.59 | +17.9 [+10.1, +30.9] | +1,445 [+874, +2,072] | -637 [-1,116, -210] P<=0 1.00 | +629 [-138, +1,418] P<=0 0.06 |
| select | vt_v1_m0.03_any | 0 | base | sl0 | 404.00 | 47.85 | +13.5 [+6.2, +25.5] | +1,432 [+653, +2,294] | -650 [-1,046, -332] P<=0 1.00 | +615 [-322, +1,609] P<=0 0.10 |
| select | vt_v1_m0.03_any | 0 | base | sl1 | 478.00 | 47.19 | +13.4 [+6.7, +23.7] | +1,636 [+816, +2,531] | -446 [-795, -174] P<=0 1.00 | +820 [-134, +1,862] P<=0 0.05 |
| select | vt_v1_m0.03_any | 0 | comp | 60 | 480.00 | 42.80 | +9.2 [+3.2, +17.7] | +1,050 [+356, +1,799] |  |  |
| select | vt_v1_m0.03_any | 0 | comp | s20 | 492.00 | 17.22 | +12.0 [+5.9, +20.8] | +561 [+270, +878] | -488 [-951, -100] P<=0 0.99 | +339 [-342, +995] P<=0 0.16 |
| select | vt_v1_m0.03_any | 0 | comp | s40 | 484.00 | 30.95 | +10.3 [+4.2, +18.8] | +854 [+342, +1,402] | -196 [-402, -13] P<=0 0.98 | +631 [-76, +1,380] P<=0 0.04 |
| select | vt_v1_m0.03_any | 0 | comp | s100 | 474.00 | 64.14 | +7.5 [+1.6, +15.9] | +1,278 [+266, +2,369] | +228 [-102, +586] P<=0 0.09 | +1,055 [+34, +2,174] P<=0 0.02 |
| select | vt_v1_m0.03_any | 0 | comp | dk0.5 | 434.00 | 36.36 | +11.1 [+4.7, +21.4] | +966 [+459, +1,581] | -83 [-346, +228] P<=0 0.74 | +744 [+66, +1,448] P<=0 0.01 |
| select | vt_v1_m0.03_any | 0 | comp | dk1 | 466.00 | 37.68 | +10.4 [+4.2, +20.1] | +1,014 [+446, +1,667] | -35 [-233, +200] P<=0 0.65 | +792 [+92, +1,552] P<=0 0.01 |
| select | vt_v1_m0.03_any | 0 | comp | dk2 | 472.00 | 39.79 | +9.7 [+3.5, +18.9] | +1,011 [+381, +1,704] | -39 [-187, +145] P<=0 0.71 | +788 [+56, +1,590] P<=0 0.02 |
| select | vt_v1_m0.03_any | 0 | comp | rv1_30 | 484.00 | 27.87 | +10.7 [+4.8, +20.2] | +788 [+346, +1,261] | -262 [-559, +3] P<=0 0.97 | +565 [-92, +1,260] P<=0 0.05 |
| select | vt_v1_m0.03_any | 0 | comp | rv1_0 | 84.00 | 46.74 | +16.1 [+4.6, +53.7] | +304 [+88, +569] | -746 [-1,424, -135] P<=0 0.99 | +81 [-569, +692] P<=0 0.41 |
| select | vt_v1_m0.03_any | 0 | comp | rv3_30 | 482.00 | 32.79 | +10.2 [+3.3, +20.9] | +889 [+308, +1,505] | -160 [-360, +19] P<=0 0.96 | +667 [-28, +1,404] P<=0 0.03 |
| select | vt_v1_m0.03_any | 0 | comp | rv3_0 | 210.00 | 45.07 | +12.0 [+2.0, +33.5] | +607 [+110, +1,119] | -443 [-895, -28] P<=0 0.98 | +384 [-293, +1,051] P<=0 0.13 |
| select | vt_v1_m0.03_any | 0 | comp | dk1_rv1 | 468.00 | 26.27 | +11.2 [+4.9, +21.7] | +751 [+351, +1,201] | -299 [-645, +27] P<=0 0.96 | +528 [-111, +1,179] P<=0 0.06 |
| select | vt_v1_m0.03_any | 0 | comp | sl0 | 350.00 | 42.86 | +8.5 [+1.0, +21.0] | +701 [+63, +1,377] | -349 [-558, -172] P<=0 1.00 | +478 [-297, +1,266] P<=0 0.11 |
| select | vt_v1_m0.03_any | 0 | comp | sl1 | 414.00 | 42.60 | +8.6 [+1.8, +18.8] | +825 [+173, +1,522] | -225 [-387, -95] P<=0 1.00 | +602 [-192, +1,414] P<=0 0.07 |
| select | vt_v1_m0.03_any | 0 | e+25 | 60 | 528.00 | 48.50 | +13.1 [+6.9, +21.9] | +1,844 [+940, +2,868] |  |  |
| select | vt_v1_m0.03_any | 0 | e+25 | s20 | 536.00 | 18.41 | +14.4 [+8.5, +23.0] | +786 [+439, +1,188] | -1,058 [-1,712, -509] P<=0 1.00 | +256 [-539, +1,021] P<=0 0.26 |
| select | vt_v1_m0.03_any | 0 | e+25 | s40 | 530.00 | 34.47 | +13.8 [+7.7, +22.4] | +1,388 [+731, +2,130] | -455 [-761, -196] P<=0 1.00 | +858 [-5, +1,772] P<=0 0.03 |
| select | vt_v1_m0.03_any | 0 | e+25 | s100 | 518.00 | 74.89 | +12.0 [+5.5, +20.9] | +2,563 [+1,166, +4,103] | +719 [+236, +1,269] P<=0 0.00 | +2,033 [+681, +3,626] P<=0 0.00 |
| select | vt_v1_m0.03_any | 0 | e+25 | dk0.5 | 468.00 | 39.43 | +14.6 [+7.7, +25.4] | +1,464 [+823, +2,215] | -380 [-800, +35] P<=0 0.97 | +934 [+138, +1,802] P<=0 0.01 |
| select | vt_v1_m0.03_any | 0 | e+25 | dk1 | 514.00 | 41.45 | +14.5 [+7.8, +24.3] | +1,688 [+963, +2,540] | -156 [-430, +137] P<=0 0.88 | +1,158 [+310, +2,128] P<=0 0.00 |
| select | vt_v1_m0.03_any | 0 | e+25 | dk2 | 518.00 | 44.71 | +14.1 [+7.3, +23.7] | +1,778 [+942, +2,720] | -65 [-234, +129] P<=0 0.78 | +1,248 [+333, +2,298] P<=0 0.00 |
| select | vt_v1_m0.03_any | 0 | e+25 | rv1_30 | 534.00 | 30.63 | +15.3 [+8.6, +26.1] | +1,354 [+745, +2,026] | -489 [-899, -125] P<=0 1.00 | +824 [+13, +1,704] P<=0 0.02 |
| select | vt_v1_m0.03_any | 0 | e+25 | rv1_0 | 94.00 | 50.74 | +27.2 [+10.5, +71.6] | +602 [+257, +997] | -1,242 [-2,152, -464] P<=0 1.00 | +72 [-700, +801] P<=0 0.43 |
| select | vt_v1_m0.03_any | 0 | e+25 | rv3_30 | 532.00 | 36.46 | +14.9 [+7.4, +26.3] | +1,574 [+814, +2,402] | -269 [-545, -16] P<=0 0.98 | +1,044 [+192, +1,988] P<=0 0.01 |
| select | vt_v1_m0.03_any | 0 | e+25 | rv3_0 | 234.00 | 50.24 | +18.7 [+7.1, +41.1] | +1,139 [+493, +1,831] | -705 [-1,326, -154] P<=0 0.99 | +609 [-202, +1,455] P<=0 0.07 |
| select | vt_v1_m0.03_any | 0 | e+25 | dk1_rv1 | 520.00 | 27.89 | +16.1 [+8.9, +28.0] | +1,245 [+708, +1,847] | -599 [-1,097, -155] P<=0 1.00 | +715 [-57, +1,525] P<=0 0.04 |
| select | vt_v1_m0.03_any | 0 | e+25 | sl0 | 378.00 | 49.28 | +12.2 [+4.9, +23.8] | +1,259 [+464, +2,110] | -584 [-974, -272] P<=0 1.00 | +729 [-183, +1,729] P<=0 0.06 |
| select | vt_v1_m0.03_any | 0 | e+25 | sl1 | 444.00 | 48.41 | +11.8 [+5.2, +21.2] | +1,390 [+569, +2,273] | -453 [-812, -173] P<=0 1.00 | +860 [-71, +1,908] P<=0 0.04 |
| quiet | vt_v1_m0.03_any | 0 | base | 60 | 442.64 | 47.61 | +19.6 [+9.6, +31.3] | +1,944 [+903, +3,091] |  |  |
| quiet | vt_v1_m0.03_any | 0 | base | s20 | 453.99 | 18.64 | +22.5 [+12.0, +34.3] | +886 [+470, +1,352] | -1,058 [-1,806, -446] P<=0 1.00 | -262 [-857, +330] P<=0 0.81 |
| quiet | vt_v1_m0.03_any | 0 | base | s40 | 448.32 | 34.28 | +20.9 [+10.7, +32.5] | +1,512 [+765, +2,378] | -431 [-771, -146] P<=0 1.00 | +364 [-430, +1,310] P<=0 0.23 |
| quiet | vt_v1_m0.03_any | 0 | base | s100 | 438.38 | 70.00 | +17.2 [+7.2, +29.0] | +2,494 [+1,050, +4,040] | +550 [+109, +1,009] P<=0 0.01 | +1,346 [-58, +2,919] P<=0 0.03 |
| quiet | vt_v1_m0.03_any | 0 | base | dk0.5 | 411.43 | 35.77 | +20.2 [+10.2, +32.2] | +1,330 [+687, +2,009] | -614 [-1,180, -160] P<=0 1.00 | +182 [-524, +906] P<=0 0.33 |
| quiet | vt_v1_m0.03_any | 0 | base | dk1 | 442.64 | 39.44 | +20.2 [+9.8, +32.1] | +1,605 [+802, +2,481] | -339 [-700, -63] P<=0 1.00 | +457 [-358, +1,339] P<=0 0.16 |
| quiet | vt_v1_m0.03_any | 0 | base | dk2 | 439.80 | 43.08 | +20.3 [+9.9, +32.1] | +1,773 [+871, +2,789] | -171 [-408, +7] P<=0 0.96 | +625 [-265, +1,659] P<=0 0.12 |
| quiet | vt_v1_m0.03_any | 0 | base | rv1_30 | 453.99 | 31.17 | +22.4 [+12.9, +32.8] | +1,454 [+809, +2,163] | -490 [-1,006, -53] P<=0 0.99 | +305 [-363, +1,066] P<=0 0.23 |
| quiet | vt_v1_m0.03_any | 0 | base | rv1_0 | 90.80 | 51.92 | +29.1 [+17.1, +41.3] | +545 [+287, +837] | -1,399 [-2,584, -392] P<=0 1.00 | -604 [-1,049, -226] P<=0 1.00 |
| quiet | vt_v1_m0.03_any | 0 | base | rv3_30 | 451.15 | 37.13 | +20.3 [+11.8, +29.7] | +1,565 [+886, +2,304] | -379 [-881, +37] P<=0 0.96 | +417 [-247, +1,175] P<=0 0.14 |
| quiet | vt_v1_m0.03_any | 0 | base | rv3_0 | 229.83 | 47.34 | +21.7 [+13.4, +30.0] | +999 [+581, +1,423] | -945 [-2,125, +2] P<=0 0.97 | -149 [-503, +172] P<=0 0.82 |
| quiet | vt_v1_m0.03_any | 0 | base | dk1_rv1 | 445.48 | 27.77 | +22.9 [+13.5, +33.4] | +1,267 [+718, +1,868] | -677 [-1,307, -140] P<=0 1.00 | +119 [-488, +767] P<=0 0.39 |
| quiet | vt_v1_m0.03_any | 0 | base | sl0 | 319.21 | 43.78 | +20.0 [+7.5, +34.7] | +1,331 [+518, +2,204] | -613 [-1,029, -284] P<=0 1.00 | +183 [-685, +1,109] P<=0 0.37 |
| quiet | vt_v1_m0.03_any | 0 | base | sl1 | 375.96 | 46.60 | +20.9 [+9.3, +34.3] | +1,723 [+788, +2,733] | -221 [-484, -49] P<=0 1.00 | +575 [-373, +1,656] P<=0 0.15 |
| quiet | vt_v1_m0.03_any | 0 | comp | 60 | 357.52 | 41.01 | +15.3 [+5.6, +26.2] | +1,089 [+410, +1,758] |  |  |
| quiet | vt_v1_m0.03_any | 0 | comp | s20 | 364.61 | 17.51 | +19.0 [+8.7, +31.3] | +598 [+272, +974] | -491 [-854, -124] P<=0 1.00 | -47 [-510, +450] P<=0 0.59 |
| quiet | vt_v1_m0.03_any | 0 | comp | s40 | 360.35 | 30.55 | +16.7 [+6.8, +28.2] | +892 [+359, +1,442] | -196 [-378, -20] P<=0 0.99 | +248 [-333, +882] P<=0 0.23 |
| quiet | vt_v1_m0.03_any | 0 | comp | s100 | 354.68 | 56.68 | +13.3 [+3.6, +24.2] | +1,301 [+383, +2,184] | +212 [-69, +501] P<=0 0.06 | +656 [-217, +1,535] P<=0 0.07 |
| quiet | vt_v1_m0.03_any | 0 | comp | dk0.5 | 329.14 | 33.25 | +18.4 [+7.5, +31.4] | +928 [+394, +1,484] | -161 [-398, +42] P<=0 0.94 | +283 [-262, +835] P<=0 0.15 |
| quiet | vt_v1_m0.03_any | 0 | comp | dk1 | 353.26 | 35.08 | +17.1 [+6.9, +28.7] | +1,001 [+406, +1,598] | -88 [-284, +59] P<=0 0.85 | +356 [-219, +954] P<=0 0.12 |
| quiet | vt_v1_m0.03_any | 0 | comp | dk2 | 354.68 | 36.98 | +16.4 [+6.0, +27.7] | +1,021 [+391, +1,642] | -68 [-227, +38] P<=0 0.84 | +376 [-239, +1,012] P<=0 0.12 |
| quiet | vt_v1_m0.03_any | 0 | comp | rv1_30 | 361.77 | 28.54 | +18.9 [+9.4, +29.6] | +928 [+441, +1,454] | -160 [-408, +81] P<=0 0.91 | +283 [-219, +858] P<=0 0.17 |
| quiet | vt_v1_m0.03_any | 0 | comp | rv1_0 | 75.19 | 45.93 | +29.1 [+14.9, +44.7] | +398 [+180, +654] | -691 [-1,339, -73] P<=0 0.98 | -247 [-558, +35] P<=0 0.95 |
| quiet | vt_v1_m0.03_any | 0 | comp | rv3_30 | 360.35 | 33.58 | +17.1 [+8.1, +27.0] | +974 [+447, +1,513] | -115 [-330, +118] P<=0 0.86 | +329 [-187, +911] P<=0 0.12 |
| quiet | vt_v1_m0.03_any | 0 | comp | rv3_0 | 180.18 | 43.83 | +18.2 [+9.1, +27.8] | +624 [+295, +972] | -465 [-1,096, +123] P<=0 0.94 | -21 [-295, +264] P<=0 0.58 |
| quiet | vt_v1_m0.03_any | 0 | comp | dk1_rv1 | 357.52 | 25.62 | +20.0 [+10.3, +31.1] | +851 [+413, +1,325] | -237 [-530, +46] P<=0 0.95 | +206 [-249, +718] P<=0 0.21 |
| quiet | vt_v1_m0.03_any | 0 | comp | sl0 | 270.98 | 35.17 | +16.0 [+3.1, +30.5] | +745 [+159, +1,324] | -343 [-526, -178] P<=0 1.00 | +101 [-522, +729] P<=0 0.38 |
| quiet | vt_v1_m0.03_any | 0 | comp | sl1 | 314.96 | 38.84 | +16.9 [+5.5, +30.2] | +989 [+339, +1,641] | -99 [-190, -17] P<=0 0.99 | +345 [-313, +1,021] P<=0 0.16 |
| quiet | vt_v1_m0.03_any | 0 | e+25 | 60 | 405.75 | 48.18 | +18.7 [+8.4, +30.6] | +1,751 [+793, +2,837] |  |  |
| quiet | vt_v1_m0.03_any | 0 | e+25 | s20 | 414.27 | 18.72 | +21.6 [+10.9, +33.9] | +789 [+394, +1,245] | -962 [-1,642, -394] P<=0 1.00 | -130 [-690, +465] P<=0 0.68 |
| quiet | vt_v1_m0.03_any | 0 | e+25 | s40 | 407.17 | 34.73 | +19.9 [+9.6, +31.9] | +1,346 [+639, +2,161] | -405 [-699, -145] P<=0 1.00 | +428 [-333, +1,339] P<=0 0.18 |
| quiet | vt_v1_m0.03_any | 0 | e+25 | s100 | 398.66 | 70.79 | +17.1 [+7.1, +28.8] | +2,285 [+974, +3,675] | +534 [+131, +947] P<=0 0.00 | +1,367 [+89, +2,780] P<=0 0.02 |
| quiet | vt_v1_m0.03_any | 0 | e+25 | dk0.5 | 374.54 | 36.01 | +20.0 [+9.9, +32.3] | +1,225 [+619, +1,889] | -526 [-1,041, -114] P<=0 1.00 | +306 [-389, +1,029] P<=0 0.21 |
| quiet | vt_v1_m0.03_any | 0 | e+25 | dk1 | 401.50 | 39.75 | +19.6 [+9.2, +31.6] | +1,444 [+672, +2,277] | -307 [-632, -49] P<=0 0.99 | +526 [-260, +1,394] P<=0 0.12 |
| quiet | vt_v1_m0.03_any | 0 | e+25 | dk2 | 402.92 | 43.17 | +19.5 [+9.0, +31.5] | +1,587 [+746, +2,528] | -164 [-390, +4] P<=0 0.97 | +669 [-191, +1,658] P<=0 0.08 |
| quiet | vt_v1_m0.03_any | 0 | e+25 | rv1_30 | 411.43 | 31.61 | +21.7 [+11.9, +32.3] | +1,305 [+698, +1,972] | -447 [-897, -47] P<=0 0.98 | +386 [-253, +1,128] P<=0 0.15 |
| quiet | vt_v1_m0.03_any | 0 | e+25 | rv1_0 | 83.70 | 51.39 | +28.5 [+16.0, +41.9] | +476 [+231, +758] | -1,275 [-2,385, -344] P<=0 1.00 | -442 [-868, -94] P<=0 0.99 |
| quiet | vt_v1_m0.03_any | 0 | e+25 | rv3_30 | 408.59 | 37.78 | +19.6 [+11.0, +29.0] | +1,405 [+748, +2,094] | -346 [-787, +43] P<=0 0.96 | +486 [-152, +1,240] P<=0 0.09 |
| quiet | vt_v1_m0.03_any | 0 | e+25 | rv3_0 | 205.71 | 48.43 | +20.6 [+12.2, +29.2] | +871 [+464, +1,281] | -881 [-1,955, +15] P<=0 0.97 | -48 [-393, +280] P<=0 0.63 |
| quiet | vt_v1_m0.03_any | 0 | e+25 | dk1_rv1 | 405.75 | 27.91 | +22.3 [+12.5, +33.6] | +1,141 [+618, +1,722] | -610 [-1,168, -122] P<=0 1.00 | +222 [-368, +867] P<=0 0.27 |
| quiet | vt_v1_m0.03_any | 0 | e+25 | sl0 | 292.26 | 44.73 | +20.2 [+7.7, +35.3] | +1,283 [+501, +2,144] | -468 [-821, -194] P<=0 1.00 | +364 [-457, +1,293] P<=0 0.22 |
| quiet | vt_v1_m0.03_any | 0 | e+25 | sl1 | 343.33 | 47.32 | +20.2 [+8.6, +33.7] | +1,582 [+698, +2,558] | -169 [-377, -26] P<=0 1.00 | +663 [-253, +1,687] P<=0 0.10 |
| busy | vt_v1_m0.03_any | 0 | base | 60 | 948.00 | 50.74 | +7.7 [+1.2, +15.5] | +1,450 [+226, +2,834] |  |  |
| busy | vt_v1_m0.03_any | 0 | base | s20 | 948.00 | 18.78 | +9.7 [+3.2, +17.5] | +686 [+215, +1,247] | -764 [-1,677, +8] P<=0 0.97 | +311 [-1,248, +1,548] P<=0 0.31 |
| busy | vt_v1_m0.03_any | 0 | base | s40 | 948.00 | 35.59 | +8.5 [+2.1, +16.4] | +1,132 [+255, +2,138] | -319 [-736, +43] P<=0 0.95 | +756 [-837, +2,148] P<=0 0.14 |
| busy | vt_v1_m0.03_any | 0 | base | s100 | 948.00 | 76.05 | +6.1 [-0.3, +13.4] | +1,707 [-82, +3,642] | +257 [-344, +921] P<=0 0.22 | +1,332 [-732, +3,376] P<=0 0.09 |
| busy | vt_v1_m0.03_any | 0 | base | dk0.5 | 888.00 | 38.91 | +6.5 [+1.0, +12.6] | +872 [+138, +1,642] | -579 [-1,693, +210] P<=0 0.90 | +497 [-1,122, +1,825] P<=0 0.24 |
| busy | vt_v1_m0.03_any | 0 | base | dk1 | 930.00 | 43.64 | +6.1 [+0.7, +12.0] | +957 [+104, +1,836] | -493 [-1,480, +178] P<=0 0.88 | +582 [-1,039, +1,936] P<=0 0.21 |
| busy | vt_v1_m0.03_any | 0 | base | dk2 | 930.00 | 47.36 | +5.7 [+0.4, +11.5] | +974 [+65, +1,889] | -477 [-1,359, +106] P<=0 0.92 | +598 [-1,006, +1,976] P<=0 0.20 |
| busy | vt_v1_m0.03_any | 0 | base | rv1_30 | 948.00 | 32.79 | +8.9 [+2.6, +16.5] | +1,056 [+281, +1,929] | -394 [-1,000, +77] P<=0 0.94 | +681 [-922, +1,973] P<=0 0.17 |
| busy | vt_v1_m0.03_any | 0 | base | rv1_0 | 192.00 | 55.63 | +8.1 [-5.0, +20.9] | +262 [-128, +703] | -1,188 [-2,526, -141] P<=0 0.99 | -113 [-1,681, +1,117] P<=0 0.55 |
| busy | vt_v1_m0.03_any | 0 | base | rv3_30 | 948.00 | 39.94 | +8.0 [+1.9, +14.8] | +1,140 [+228, +2,124] | -310 [-888, +114] P<=0 0.91 | +765 [-833, +2,111] P<=0 0.15 |
| busy | vt_v1_m0.03_any | 0 | base | rv3_0 | 480.00 | 52.93 | +6.0 [-2.0, +13.4] | +519 [-158, +1,261] | -932 [-2,238, -2] P<=0 0.97 | +143 [-1,426, +1,481] P<=0 0.40 |
| busy | vt_v1_m0.03_any | 0 | base | dk1_rv1 | 930.00 | 30.16 | +7.8 [+2.4, +13.7] | +827 [+253, +1,430] | -623 [-1,658, +128] P<=0 0.93 | +452 [-1,097, +1,675] P<=0 0.24 |
| busy | vt_v1_m0.03_any | 0 | base | sl0 | 540.00 | 45.40 | +10.7 [+1.3, +20.1] | +961 [+113, +1,915] | -489 [-1,180, +147] P<=0 0.93 | +586 [-1,124, +2,008] P<=0 0.21 |
| busy | vt_v1_m0.03_any | 0 | base | sl1 | 762.00 | 48.00 | +8.3 [+1.6, +15.5] | +1,162 [+218, +2,234] | -289 [-886, +230] P<=0 0.86 | +786 [-935, +2,227] P<=0 0.16 |
| busy | vt_v1_m0.03_any | 0 | comp | 60 | 756.00 | 46.51 | +2.5 [-3.7, +9.2] | +342 [-539, +1,199] |  |  |
| busy | vt_v1_m0.03_any | 0 | comp | s20 | 756.00 | 18.36 | +4.2 [-1.9, +11.0] | +225 [-108, +573] | -117 [-680, +409] P<=0 0.65 | +131 [-1,081, +1,156] P<=0 0.39 |
| busy | vt_v1_m0.03_any | 0 | comp | s40 | 756.00 | 33.91 | +3.0 [-3.2, +9.8] | +293 [-325, +911] | -50 [-320, +199] P<=0 0.64 | +198 [-1,021, +1,227] P<=0 0.35 |
| busy | vt_v1_m0.03_any | 0 | comp | s100 | 756.00 | 67.16 | +2.3 [-4.4, +9.3] | +435 [-845, +1,755] | +93 [-366, +596] P<=0 0.35 | +341 [-1,187, +1,714] P<=0 0.32 |
| busy | vt_v1_m0.03_any | 0 | comp | dk0.5 | 708.00 | 37.28 | +2.0 [-3.9, +8.6] | +203 [-400, +805] | -140 [-664, +342] P<=0 0.70 | +108 [-1,158, +1,197] P<=0 0.42 |
| busy | vt_v1_m0.03_any | 0 | comp | dk1 | 738.00 | 41.22 | +1.8 [-4.2, +8.4] | +204 [-484, +875] | -139 [-628, +298] P<=0 0.72 | +109 [-1,176, +1,215] P<=0 0.41 |
| busy | vt_v1_m0.03_any | 0 | comp | dk2 | 738.00 | 44.02 | +1.2 [-4.6, +7.6] | +146 [-576, +865] | -196 [-638, +170] P<=0 0.84 | +51 [-1,231, +1,174] P<=0 0.46 |
| busy | vt_v1_m0.03_any | 0 | comp | rv1_30 | 756.00 | 31.77 | +3.5 [-2.8, +10.4] | +316 [-244, +919] | -27 [-376, +287] P<=0 0.56 | +221 [-984, +1,246] P<=0 0.33 |
| busy | vt_v1_m0.03_any | 0 | comp | rv1_0 | 162.00 | 54.15 | +5.2 [-8.0, +19.4] | +142 [-191, +513] | -200 [-975, +485] P<=0 0.70 | +48 [-1,216, +1,122] P<=0 0.46 |
| busy | vt_v1_m0.03_any | 0 | comp | rv3_30 | 756.00 | 37.85 | +2.8 [-3.2, +9.3] | +292 [-341, +981] | -51 [-373, +222] P<=0 0.63 | +197 [-1,035, +1,234] P<=0 0.35 |
| busy | vt_v1_m0.03_any | 0 | comp | rv3_0 | 384.00 | 49.88 | +1.4 [-8.2, +9.8] | +85 [-419, +664] | -257 [-982, +360] P<=0 0.77 | -9 [-1,242, +1,074] P<=0 0.50 |
| busy | vt_v1_m0.03_any | 0 | comp | dk1_rv1 | 738.00 | 29.53 | +3.0 [-2.6, +9.1] | +247 [-200, +715] | -95 [-647, +388] P<=0 0.63 | +153 [-1,061, +1,200] P<=0 0.38 |
| busy | vt_v1_m0.03_any | 0 | comp | sl0 | 414.00 | 42.60 | +7.1 [-2.6, +16.9] | +458 [-150, +1,102] | +116 [-380, +621] P<=0 0.35 | +363 [-946, +1,455] P<=0 0.26 |
| busy | vt_v1_m0.03_any | 0 | comp | sl1 | 588.00 | 43.34 | +5.6 [-2.3, +13.3] | +520 [-203, +1,282] | +178 [-203, +530] P<=0 0.17 | +426 [-912, +1,559] P<=0 0.24 |
| busy | vt_v1_m0.03_any | 0 | e+25 | 60 | 804.00 | 54.01 | +4.6 [-1.0, +10.4] | +787 [-182, +1,767] |  |  |
| busy | vt_v1_m0.03_any | 0 | e+25 | s20 | 804.00 | 19.49 | +6.2 [+0.7, +11.7] | +381 [+42, +742] | -406 [-1,045, +204] P<=0 0.90 | +85 [-1,292, +1,179] P<=0 0.42 |
| busy | vt_v1_m0.03_any | 0 | e+25 | s40 | 804.00 | 37.27 | +5.2 [-0.4, +10.8] | +609 [-48, +1,288] | -178 [-498, +128] P<=0 0.88 | +313 [-1,048, +1,424] P<=0 0.30 |
| busy | vt_v1_m0.03_any | 0 | e+25 | s100 | 804.00 | 82.97 | +3.8 [-1.9, +9.6] | +974 [-528, +2,472] | +187 [-350, +759] P<=0 0.26 | +678 [-1,002, +2,241] P<=0 0.20 |
| busy | vt_v1_m0.03_any | 0 | e+25 | dk0.5 | 756.00 | 40.60 | +3.5 [-2.0, +9.6] | +414 [-247, +1,097] | -373 [-1,088, +202] P<=0 0.89 | +118 [-1,289, +1,318] P<=0 0.41 |
| busy | vt_v1_m0.03_any | 0 | e+25 | dk1 | 786.00 | 46.42 | +2.9 [-2.7, +9.0] | +412 [-370, +1,223] | -375 [-1,118, +177] P<=0 0.89 | +116 [-1,294, +1,357] P<=0 0.42 |
| busy | vt_v1_m0.03_any | 0 | e+25 | dk2 | 786.00 | 50.69 | +2.8 [-2.6, +8.5] | +437 [-404, +1,281] | -350 [-1,028, +128] P<=0 0.90 | +141 [-1,259, +1,360] P<=0 0.40 |
| busy | vt_v1_m0.03_any | 0 | e+25 | rv1_30 | 804.00 | 34.40 | +5.7 [-0.1, +11.5] | +602 [-7, +1,254] | -185 [-583, +184] P<=0 0.83 | +306 [-1,061, +1,419] P<=0 0.30 |
| busy | vt_v1_m0.03_any | 0 | e+25 | rv1_0 | 180.00 | 54.61 | +7.2 [-5.9, +21.9] | +212 [-155, +632] | -575 [-1,404, +180] P<=0 0.93 | -84 [-1,505, +1,109] P<=0 0.54 |
| busy | vt_v1_m0.03_any | 0 | e+25 | rv3_30 | 804.00 | 41.54 | +4.6 [-0.9, +10.5] | +575 [-105, +1,337] | -213 [-591, +141] P<=0 0.88 | +278 [-1,066, +1,396] P<=0 0.32 |
| busy | vt_v1_m0.03_any | 0 | e+25 | rv3_0 | 408.00 | 54.09 | +2.5 [-6.3, +11.0] | +181 [-378, +823] | -607 [-1,427, +123] P<=0 0.95 | -115 [-1,524, +1,050] P<=0 0.56 |
| busy | vt_v1_m0.03_any | 0 | e+25 | dk1_rv1 | 786.00 | 31.68 | +4.8 [-0.7, +10.5] | +452 [-67, +996] | -335 [-1,007, +228] P<=0 0.86 | +156 [-1,193, +1,275] P<=0 0.39 |
| busy | vt_v1_m0.03_any | 0 | e+25 | sl0 | 444.00 | 49.40 | +9.7 [+1.3, +17.2] | +802 [+82, +1,585] | +14 [-531, +528] P<=0 0.46 | +506 [-1,033, +1,764] P<=0 0.22 |
| busy | vt_v1_m0.03_any | 0 | e+25 | sl1 | 630.00 | 50.86 | +6.6 [+0.1, +12.8] | +819 [+6, +1,711] | +32 [-465, +474] P<=0 0.44 | +523 [-1,033, +1,772] P<=0 0.22 |
| unseen | vt_v1_m0.03_any | 0 | base | 60 | 539.28 | 48.66 | +15.9 [+8.7, +24.1] | +1,850 [+980, +2,878] |  |  |
| unseen | vt_v1_m0.03_any | 0 | base | s20 | 548.46 | 18.69 | +18.7 [+11.2, +27.1] | +848 [+489, +1,264] | -1,002 [-1,597, -496] P<=0 1.00 | -153 [-677, +399] P<=0 0.73 |
| unseen | vt_v1_m0.03_any | 0 | base | s40 | 543.87 | 34.72 | +17.1 [+9.8, +25.2] | +1,440 [+800, +2,196] | -410 [-674, -176] P<=0 1.00 | +439 [-273, +1,236] P<=0 0.13 |
| unseen | vt_v1_m0.03_any | 0 | base | s100 | 535.84 | 72.04 | +13.7 [+6.6, +21.6] | +2,344 [+1,121, +3,753] | +494 [+117, +865] P<=0 0.01 | +1,343 [+160, +2,651] P<=0 0.01 |
| unseen | vt_v1_m0.03_any | 0 | base | dk0.5 | 502.57 | 36.83 | +15.8 [+8.9, +23.5] | +1,242 [+695, +1,869] | -607 [-1,082, -196] P<=0 1.00 | +242 [-355, +900] P<=0 0.24 |
| unseen | vt_v1_m0.03_any | 0 | base | dk1 | 535.84 | 40.83 | +15.7 [+8.7, +23.3] | +1,481 [+813, +2,254] | -368 [-698, -88] P<=0 1.00 | +481 [-223, +1,242] P<=0 0.10 |
| unseen | vt_v1_m0.03_any | 0 | base | dk2 | 533.55 | 44.51 | +15.7 [+8.5, +23.6] | +1,620 [+886, +2,498] | -229 [-480, -33] P<=0 0.99 | +620 [-156, +1,485] P<=0 0.06 |
| unseen | vt_v1_m0.03_any | 0 | base | rv1_30 | 548.46 | 31.70 | +18.3 [+11.5, +25.8] | +1,378 [+842, +2,005] | -472 [-894, -114] P<=0 0.99 | +377 [-212, +1,050] P<=0 0.12 |
| unseen | vt_v1_m0.03_any | 0 | base | rv1_0 | 110.15 | 53.16 | +23.0 [+14.1, +33.3] | +491 [+265, +742] | -1,359 [-2,319, -531] P<=0 1.00 | -510 [-948, -95] P<=0 0.99 |
| unseen | vt_v1_m0.03_any | 0 | base | rv3_30 | 546.17 | 38.06 | +16.5 [+10.5, +23.2] | +1,484 [+915, +2,149] | -366 [-786, -12] P<=0 0.98 | +483 [-104, +1,166] P<=0 0.06 |
| unseen | vt_v1_m0.03_any | 0 | base | rv3_0 | 277.67 | 49.19 | +16.8 [+11.2, +23.1] | +907 [+569, +1,277] | -942 [-1,899, -149] P<=0 0.99 | -93 [-497, +274] P<=0 0.69 |
| unseen | vt_v1_m0.03_any | 0 | base | dk1_rv1 | 538.14 | 28.56 | +18.2 [+11.6, +25.6] | +1,183 [+740, +1,716] | -667 [-1,195, -212] P<=0 1.00 | +183 [-344, +775] P<=0 0.28 |
| unseen | vt_v1_m0.03_any | 0 | base | sl0 | 361.43 | 44.24 | +17.7 [+8.0, +27.9] | +1,260 [+584, +2,027] | -589 [-958, -306] P<=0 1.00 | +260 [-505, +1,041] P<=0 0.27 |
| unseen | vt_v1_m0.03_any | 0 | base | sl1 | 449.78 | 47.06 | +17.3 [+8.9, +26.1] | +1,616 [+834, +2,492] | -234 [-478, -52] P<=0 1.00 | +615 [-201, +1,494] P<=0 0.07 |
| unseen | vt_v1_m0.03_any | 0 | comp | 60 | 433.72 | 42.84 | +11.4 [+4.6, +18.7] | +946 [+392, +1,534] |  |  |
| unseen | vt_v1_m0.03_any | 0 | comp | s20 | 439.46 | 17.79 | +14.7 [+7.2, +23.5] | +527 [+253, +866] | -419 [-742, -108] P<=0 1.00 | -13 [-430, +441] P<=0 0.54 |
| unseen | vt_v1_m0.03_any | 0 | comp | s40 | 436.02 | 31.66 | +12.5 [+5.4, +20.2] | +778 [+348, +1,262] | -168 [-323, -18] P<=0 0.98 | +238 [-245, +783] P<=0 0.20 |
| unseen | vt_v1_m0.03_any | 0 | comp | s100 | 431.43 | 60.19 | +9.8 [+3.3, +17.1] | +1,135 [+369, +1,927] | +189 [-51, +433] P<=0 0.06 | +596 [-137, +1,299] P<=0 0.06 |
| unseen | vt_v1_m0.03_any | 0 | comp | dk0.5 | 401.59 | 34.61 | +13.2 [+5.5, +21.5] | +789 [+341, +1,280] | -157 [-363, +29] P<=0 0.95 | +249 [-228, +731] P<=0 0.16 |
| unseen | vt_v1_m0.03_any | 0 | comp | dk1 | 426.84 | 37.11 | +12.3 [+5.1, +20.1] | +849 [+367, +1,376] | -97 [-276, +48] P<=0 0.89 | +309 [-192, +830] P<=0 0.12 |
| unseen | vt_v1_m0.03_any | 0 | comp | dk2 | 427.98 | 39.30 | +11.5 [+4.4, +19.1] | +853 [+342, +1,405] | -93 [-242, +28] P<=0 0.93 | +314 [-218, +869] P<=0 0.13 |
| unseen | vt_v1_m0.03_any | 0 | comp | rv1_30 | 437.16 | 29.61 | +14.2 [+7.5, +21.8] | +811 [+416, +1,283] | -135 [-340, +77] P<=0 0.90 | +271 [-163, +788] P<=0 0.14 |
| unseen | vt_v1_m0.03_any | 0 | comp | rv1_0 | 91.79 | 48.70 | +21.5 [+11.0, +33.7] | +349 [+162, +574] | -597 [-1,130, -84] P<=0 0.99 | -191 [-536, +141] P<=0 0.87 |
| unseen | vt_v1_m0.03_any | 0 | comp | rv3_30 | 436.02 | 34.99 | +12.7 [+6.5, +19.7] | +844 [+415, +1,347] | -102 [-291, +90] P<=0 0.85 | +304 [-141, +808] P<=0 0.10 |
| unseen | vt_v1_m0.03_any | 0 | comp | rv3_0 | 219.16 | 45.86 | +13.1 [+6.5, +20.3] | +521 [+245, +824] | -425 [-926, +74] P<=0 0.96 | -19 [-323, +279] P<=0 0.56 |
| unseen | vt_v1_m0.03_any | 0 | comp | dk1_rv1 | 430.28 | 26.90 | +14.7 [+7.8, +22.6] | +736 [+384, +1,147] | -210 [-463, +37] P<=0 0.95 | +196 [-218, +655] P<=0 0.20 |
| unseen | vt_v1_m0.03_any | 0 | comp | sl0 | 298.33 | 37.14 | +13.8 [+4.1, +24.4] | +690 [+219, +1,203] | -255 [-423, -87] P<=0 1.00 | +151 [-380, +686] P<=0 0.30 |
| unseen | vt_v1_m0.03_any | 0 | comp | sl1 | 367.17 | 40.22 | +13.8 [+5.4, +22.9] | +900 [+371, +1,481] | -46 [-149, +53] P<=0 0.82 | +360 [-212, +910] P<=0 0.10 |
| unseen | vt_v1_m0.03_any | 0 | e+25 | 60 | 481.91 | 50.04 | +14.5 [+7.1, +22.6] | +1,567 [+759, +2,505] |  |  |
| unseen | vt_v1_m0.03_any | 0 | e+25 | s20 | 488.80 | 18.96 | +17.2 [+9.5, +25.9] | +711 [+378, +1,116] | -856 [-1,386, -397] P<=0 1.00 | -89 [-564, +441] P<=0 0.65 |
| unseen | vt_v1_m0.03_any | 0 | e+25 | s40 | 483.06 | 35.54 | +15.6 [+8.1, +24.0] | +1,205 [+615, +1,919] | -361 [-598, -147] P<=0 1.00 | +406 [-242, +1,150] P<=0 0.13 |
| unseen | vt_v1_m0.03_any | 0 | e+25 | s100 | 476.18 | 74.72 | +12.9 [+6.0, +20.4] | +2,035 [+917, +3,267] | +468 [+133, +812] P<=0 0.00 | +1,235 [+180, +2,374] P<=0 0.01 |
| unseen | vt_v1_m0.03_any | 0 | e+25 | dk0.5 | 447.49 | 37.49 | +14.8 [+7.8, +23.2] | +1,070 [+551, +1,687] | -497 [-928, -136] P<=0 1.00 | +270 [-290, +883] P<=0 0.19 |
| unseen | vt_v1_m0.03_any | 0 | e+25 | dk1 | 475.03 | 41.86 | +14.4 [+7.4, +22.7] | +1,247 [+621, +2,000] | -320 [-609, -70] P<=0 1.00 | +447 [-194, +1,201] P<=0 0.10 |
| unseen | vt_v1_m0.03_any | 0 | e+25 | dk2 | 476.18 | 45.55 | +14.4 [+7.1, +22.6] | +1,367 [+670, +2,203] | -199 [-419, -26] P<=0 0.99 | +568 [-138, +1,396] P<=0 0.06 |
| unseen | vt_v1_m0.03_any | 0 | e+25 | rv1_30 | 486.50 | 32.49 | +17.0 [+10.1, +24.6] | +1,170 [+668, +1,772] | -397 [-763, -68] P<=0 0.99 | +371 [-175, +1,007] P<=0 0.11 |
| unseen | vt_v1_m0.03_any | 0 | e+25 | rv1_0 | 102.12 | 52.48 | +22.2 [+12.4, +33.3] | +426 [+212, +669] | -1,141 [-2,030, -378] P<=0 1.00 | -374 [-798, +13] P<=0 0.97 |
| unseen | vt_v1_m0.03_any | 0 | e+25 | rv3_30 | 484.21 | 38.97 | +15.3 [+9.1, +22.2] | +1,246 [+709, +1,873] | -321 [-676, -2] P<=0 0.98 | +447 [-106, +1,090] P<=0 0.06 |
| unseen | vt_v1_m0.03_any | 0 | e+25 | rv3_0 | 244.40 | 50.24 | +15.4 [+9.3, +21.9] | +739 [+420, +1,090] | -828 [-1,673, -88] P<=0 0.99 | -61 [-429, +298] P<=0 0.64 |
| unseen | vt_v1_m0.03_any | 0 | e+25 | dk1_rv1 | 478.47 | 29.09 | +17.0 [+10.1, +24.9] | +1,009 [+585, +1,516] | -558 [-1,014, -165] P<=0 1.00 | +210 [-286, +780] P<=0 0.23 |
| unseen | vt_v1_m0.03_any | 0 | e+25 | sl0 | 321.27 | 45.96 | +17.7 [+8.0, +28.1] | +1,191 [+533, +1,927] | -376 [-689, -143] P<=0 1.00 | +391 [-324, +1,141] P<=0 0.15 |
| unseen | vt_v1_m0.03_any | 0 | e+25 | sl1 | 398.15 | 48.39 | +16.5 [+8.0, +25.8] | +1,436 [+681, +2,289] | -131 [-330, +16] P<=0 0.95 | +637 [-134, +1,459] P<=0 0.06 |

## Size rules: vt_v1_m0.02_trigger, L = 0
| group | arm | L | fill model | size | fills/day | sh/fill | mk10 c/$ | mk10 $/day | vs 60 sh $/day | gain vs micf $/day |
|---|---|---|---|---|---|---|---|---|---|---|
| select | vt_v1_m0.02_trigger | 0 | base | 60 | 350.00 | 44.03 | +21.0 [+13.3, +29.9] | +1,496 [+892, +2,158] |  |  |
| select | vt_v1_m0.02_trigger | 0 | base | s20 | 354.00 | 17.30 | +21.1 [+14.3, +28.7] | +593 [+376, +832] | -903 [-1,355, -513] P<=0 1.00 | -223 [-944, +451] P<=0 0.74 |
| select | vt_v1_m0.02_trigger | 0 | base | s40 | 352.00 | 31.66 | +21.1 [+13.8, +29.5] | +1,081 [+664, +1,538] | -415 [-638, -228] P<=0 1.00 | +265 [-392, +926] P<=0 0.21 |
| select | vt_v1_m0.02_trigger | 0 | base | s100 | 348.00 | 64.15 | +21.0 [+13.0, +30.5] | +2,177 [+1,282, +3,203] | +681 [+354, +1,048] P<=0 0.00 | +1,361 [+633, +2,166] P<=0 0.00 |
| select | vt_v1_m0.02_trigger | 0 | base | dk0.5 | 324.00 | 38.50 | +23.6 [+14.5, +33.9] | +1,344 [+780, +1,987] | -153 [-365, -18] P<=0 0.99 | +527 [-157, +1,195] P<=0 0.07 |
| select | vt_v1_m0.02_trigger | 0 | base | dk1 | 344.00 | 40.42 | +22.5 [+14.3, +31.9] | +1,455 [+850, +2,130] | -41 [-196, +68] P<=0 0.70 | +639 [-25, +1,333] P<=0 0.03 |
| select | vt_v1_m0.02_trigger | 0 | base | dk2 | 344.00 | 42.33 | +22.1 [+14.2, +31.1] | +1,497 [+886, +2,166] | +0 [-75, +60] P<=0 0.47 | +680 [+51, +1,356] P<=0 0.02 |
| select | vt_v1_m0.02_trigger | 0 | base | rv1_30 | 352.00 | 30.06 | +24.4 [+15.7, +34.6] | +1,149 [+681, +1,668] | -347 [-561, -161] P<=0 1.00 | +332 [-329, +1,020] P<=0 0.16 |
| select | vt_v1_m0.02_trigger | 0 | base | rv1_0 | 90.00 | 47.29 | +43.0 [+22.4, +72.6] | +675 [+308, +1,123] | -822 [-1,281, -421] P<=0 1.00 | -142 [-892, +563] P<=0 0.65 |
| select | vt_v1_m0.02_trigger | 0 | base | rv3_30 | 350.00 | 35.63 | +23.2 [+15.0, +33.3] | +1,333 [+786, +1,948] | -163 [-335, -24] P<=0 0.99 | +517 [-146, +1,177] P<=0 0.06 |
| select | vt_v1_m0.02_trigger | 0 | base | rv3_0 | 192.00 | 45.43 | +27.2 [+15.8, +42.7] | +1,089 [+578, +1,725] | -408 [-773, -112] P<=0 1.00 | +272 [-438, +944] P<=0 0.23 |
| select | vt_v1_m0.02_trigger | 0 | base | dk1_rv1 | 346.00 | 28.65 | +25.6 [+16.4, +36.5] | +1,127 [+659, +1,664] | -369 [-606, -174] P<=0 1.00 | +311 [-356, +993] P<=0 0.18 |
| select | vt_v1_m0.02_trigger | 0 | base | sl0 | 194.00 | 43.05 | +27.8 [+16.8, +41.6] | +1,080 [+597, +1,630] | -416 [-742, -145] P<=0 1.00 | +264 [-392, +865] P<=0 0.21 |
| select | vt_v1_m0.02_trigger | 0 | base | sl1 | 276.00 | 41.16 | +24.6 [+15.8, +35.8] | +1,255 [+738, +1,835] | -241 [-478, -60] P<=0 1.00 | +438 [-160, +1,027] P<=0 0.08 |
| select | vt_v1_m0.02_trigger | 0 | comp | 60 | 250.00 | 38.32 | +19.8 [+10.8, +30.6] | +871 [+439, +1,370] |  |  |
| select | vt_v1_m0.02_trigger | 0 | comp | s20 | 252.00 | 16.76 | +19.8 [+11.8, +29.2] | +382 [+205, +577] | -489 [-815, -224] P<=0 1.00 | +159 [-446, +732] P<=0 0.31 |
| select | vt_v1_m0.02_trigger | 0 | comp | s40 | 252.00 | 28.56 | +20.0 [+11.5, +30.0] | +660 [+351, +1,010] | -211 [-374, -84] P<=0 1.00 | +437 [-99, +971] P<=0 0.06 |
| select | vt_v1_m0.02_trigger | 0 | comp | s100 | 244.00 | 55.32 | +17.6 [+9.1, +28.5] | +1,111 [+539, +1,791] | +240 [+63, +456] P<=0 0.00 | +888 [+351, +1,444] P<=0 0.00 |
| select | vt_v1_m0.02_trigger | 0 | comp | dk0.5 | 234.00 | 34.16 | +21.0 [+11.4, +32.6] | +780 [+384, +1,243] | -91 [-286, +21] P<=0 0.91 | +557 [+16, +1,083] P<=0 0.02 |
| select | vt_v1_m0.02_trigger | 0 | comp | dk1 | 244.00 | 36.35 | +20.0 [+11.1, +30.6] | +836 [+421, +1,312] | -35 [-182, +48] P<=0 0.64 | +613 [+78, +1,132] P<=0 0.01 |
| select | vt_v1_m0.02_trigger | 0 | comp | dk2 | 244.00 | 37.66 | +20.2 [+11.3, +30.9] | +868 [+451, +1,347] | -3 [-74, +41] P<=0 0.50 | +645 [+121, +1,162] P<=0 0.00 |
| select | vt_v1_m0.02_trigger | 0 | comp | rv1_30 | 252.00 | 27.76 | +20.4 [+11.6, +30.9] | +635 [+329, +998] | -236 [-411, -92] P<=0 1.00 | +412 [-131, +957] P<=0 0.07 |
| select | vt_v1_m0.02_trigger | 0 | comp | rv1_0 | 64.00 | 42.70 | +30.8 [+10.6, +60.6] | +310 [+98, +595] | -561 [-937, -246] P<=0 1.00 | +87 [-541, +674] P<=0 0.39 |
| select | vt_v1_m0.02_trigger | 0 | comp | rv3_30 | 252.00 | 31.68 | +20.8 [+11.4, +32.6] | +758 [+381, +1,210] | -113 [-244, -12] P<=0 0.99 | +535 [-3, +1,055] P<=0 0.03 |
| select | vt_v1_m0.02_trigger | 0 | comp | rv3_0 | 140.00 | 39.01 | +24.9 [+11.8, +43.1] | +625 [+266, +1,091] | -246 [-536, -25] P<=0 0.99 | +402 [-177, +959] P<=0 0.09 |
| select | vt_v1_m0.02_trigger | 0 | comp | dk1_rv1 | 246.00 | 26.99 | +21.2 [+12.2, +31.9] | +635 [+329, +997] | -236 [-434, -81] P<=0 1.00 | +412 [-133, +960] P<=0 0.07 |
| select | vt_v1_m0.02_trigger | 0 | comp | sl0 | 142.00 | 39.24 | +24.6 [+12.1, +40.9] | +654 [+293, +1,087] | -217 [-471, -48] P<=0 1.00 | +431 [-111, +938] P<=0 0.06 |
| select | vt_v1_m0.02_trigger | 0 | comp | sl1 | 198.00 | 35.64 | +22.8 [+12.2, +36.4] | +733 [+353, +1,180] | -138 [-332, -11] P<=0 0.99 | +511 [-12, +1,004] P<=0 0.03 |
| select | vt_v1_m0.02_trigger | 0 | e+25 | 60 | 288.00 | 44.52 | +20.9 [+12.8, +30.4] | +1,248 [+696, +1,858] |  |  |
| select | vt_v1_m0.02_trigger | 0 | e+25 | s20 | 292.00 | 17.30 | +20.8 [+13.7, +29.5] | +494 [+298, +714] | -754 [-1,162, -392] P<=0 1.00 | -36 [-714, +619] P<=0 0.54 |
| select | vt_v1_m0.02_trigger | 0 | e+25 | s40 | 288.00 | 32.26 | +20.7 [+13.0, +29.7] | +898 [+512, +1,324] | -350 [-539, -178] P<=0 1.00 | +368 [-263, +994] P<=0 0.13 |
| select | vt_v1_m0.02_trigger | 0 | e+25 | s100 | 286.00 | 65.53 | +20.8 [+12.1, +31.1] | +1,817 [+981, +2,746] | +569 [+259, +923] P<=0 0.00 | +1,287 [+549, +2,103] P<=0 0.00 |
| select | vt_v1_m0.02_trigger | 0 | e+25 | dk0.5 | 268.00 | 38.13 | +23.5 [+14.1, +33.8] | +1,112 [+597, +1,672] | -135 [-344, -10] P<=0 0.98 | +582 [-105, +1,263] P<=0 0.05 |
| select | vt_v1_m0.02_trigger | 0 | e+25 | dk1 | 284.00 | 40.53 | +22.5 [+13.9, +32.1] | +1,220 [+675, +1,824] | -28 [-182, +77] P<=0 0.62 | +690 [+11, +1,382] P<=0 0.02 |
| select | vt_v1_m0.02_trigger | 0 | e+25 | dk2 | 282.00 | 42.89 | +22.1 [+13.8, +31.5] | +1,255 [+705, +1,857] | +7 [-67, +66] P<=0 0.39 | +725 [+67, +1,408] P<=0 0.01 |
| select | vt_v1_m0.02_trigger | 0 | e+25 | rv1_30 | 290.00 | 30.28 | +23.7 [+14.6, +34.5] | +937 [+512, +1,421] | -311 [-514, -139] P<=0 1.00 | +407 [-247, +1,066] P<=0 0.12 |
| select | vt_v1_m0.02_trigger | 0 | e+25 | rv1_0 | 74.00 | 47.39 | +41.4 [+18.9, +72.5] | +545 [+218, +938] | -703 [-1,130, -339] P<=0 1.00 | +15 [-723, +735] P<=0 0.48 |
| select | vt_v1_m0.02_trigger | 0 | e+25 | rv3_30 | 288.00 | 36.16 | +22.7 [+14.1, +33.2] | +1,106 [+617, +1,669] | -142 [-302, -16] P<=0 0.99 | +576 [-81, +1,219] P<=0 0.04 |
| select | vt_v1_m0.02_trigger | 0 | e+25 | rv3_0 | 160.00 | 45.40 | +27.7 [+15.3, +44.7] | +940 [+464, +1,508] | -308 [-639, -46] P<=0 0.99 | +410 [-298, +1,082] P<=0 0.13 |
| select | vt_v1_m0.02_trigger | 0 | e+25 | dk1_rv1 | 286.00 | 28.76 | +25.0 [+15.3, +36.1] | +927 [+503, +1,413] | -321 [-542, -140] P<=0 1.00 | +397 [-267, +1,067] P<=0 0.12 |
| select | vt_v1_m0.02_trigger | 0 | e+25 | sl0 | 154.00 | 45.41 | +28.4 [+16.6, +43.2] | +940 [+486, +1,450] | -308 [-637, -49] P<=0 0.99 | +410 [-220, +995] P<=0 0.11 |
| select | vt_v1_m0.02_trigger | 0 | e+25 | sl1 | 212.00 | 43.56 | +24.8 [+15.1, +37.0] | +1,038 [+567, +1,566] | -210 [-499, -9] P<=0 0.98 | +508 [-84, +1,083] P<=0 0.05 |
| quiet | vt_v1_m0.02_trigger | 0 | base | 60 | 356.10 | 46.82 | +18.7 [+13.8, +24.0] | +1,387 [+948, +1,845] |  |  |
| quiet | vt_v1_m0.02_trigger | 0 | base | s20 | 358.94 | 18.68 | +22.4 [+16.5, +28.7] | +646 [+440, +870] | -741 [-1,012, -508] P<=0 1.00 | -502 [-896, -169] P<=0 1.00 |
| quiet | vt_v1_m0.02_trigger | 0 | base | s40 | 356.10 | 33.94 | +20.5 [+15.1, +26.1] | +1,091 [+742, +1,459] | -297 [-417, -192] P<=0 1.00 | -57 [-379, +213] P<=0 0.67 |
| quiet | vt_v1_m0.02_trigger | 0 | base | s100 | 353.26 | 70.10 | +16.9 [+12.2, +22.1] | +1,895 [+1,281, +2,550] | +508 [+300, +746] P<=0 0.00 | +747 [+342, +1,125] P<=0 0.00 |
| quiet | vt_v1_m0.02_trigger | 0 | base | dk0.5 | 334.82 | 37.91 | +20.7 [+15.0, +26.5] | +1,102 [+726, +1,510] | -285 [-445, -144] P<=0 1.00 | -46 [-390, +253] P<=0 0.63 |
| quiet | vt_v1_m0.02_trigger | 0 | base | dk1 | 353.26 | 41.13 | +20.3 [+15.0, +25.9] | +1,272 [+849, +1,724] | -116 [-205, -34] P<=0 1.00 | +123 [-209, +397] P<=0 0.24 |
| quiet | vt_v1_m0.02_trigger | 0 | base | dk2 | 353.26 | 43.84 | +20.2 [+14.9, +25.7] | +1,370 [+932, +1,827] | -18 [-68, +25] P<=0 0.79 | +221 [-111, +489] P<=0 0.08 |
| quiet | vt_v1_m0.02_trigger | 0 | base | rv1_30 | 357.52 | 34.46 | +21.6 [+15.9, +27.5] | +1,155 [+785, +1,545] | -232 [-351, -133] P<=0 1.00 | +7 [-329, +306] P<=0 0.51 |
| quiet | vt_v1_m0.02_trigger | 0 | base | rv1_0 | 112.08 | 54.13 | +24.5 [+15.0, +34.9] | +625 [+355, +930] | -763 [-1,107, -484] P<=0 1.00 | -524 [-971, -130] P<=0 1.00 |
| quiet | vt_v1_m0.02_trigger | 0 | base | rv3_30 | 356.10 | 40.88 | +20.4 [+15.3, +26.1] | +1,317 [+911, +1,751] | -70 [-151, -0] P<=0 0.98 | +169 [-162, +458] P<=0 0.15 |
| quiet | vt_v1_m0.02_trigger | 0 | base | rv3_0 | 244.02 | 47.62 | +23.0 [+16.9, +29.5] | +1,181 [+797, +1,597] | -206 [-375, -60] P<=0 1.00 | +33 [-324, +337] P<=0 0.44 |
| quiet | vt_v1_m0.02_trigger | 0 | base | dk1_rv1 | 354.68 | 31.41 | +22.5 [+16.7, +28.6] | +1,065 [+719, +1,435] | -323 [-466, -193] P<=0 1.00 | -84 [-421, +216] P<=0 0.72 |
| quiet | vt_v1_m0.02_trigger | 0 | base | sl0 | 228.41 | 42.81 | +22.3 [+15.7, +29.1] | +988 [+641, +1,387] | -399 [-593, -237] P<=0 1.00 | -160 [-531, +145] P<=0 0.85 |
| quiet | vt_v1_m0.02_trigger | 0 | base | sl1 | 279.49 | 46.34 | +22.0 [+16.2, +27.9] | +1,270 [+861, +1,705] | -118 [-232, -28] P<=0 1.00 | +122 [-218, +411] P<=0 0.23 |
| quiet | vt_v1_m0.02_trigger | 0 | comp | 60 | 269.56 | 42.72 | +16.7 [+11.0, +22.8] | +884 [+543, +1,259] |  |  |
| quiet | vt_v1_m0.02_trigger | 0 | comp | s20 | 273.81 | 17.38 | +20.5 [+14.3, +26.8] | +434 [+285, +604] | -450 [-680, -257] P<=0 1.00 | -211 [-499, +56] P<=0 0.93 |
| quiet | vt_v1_m0.02_trigger | 0 | comp | s40 | 272.39 | 31.19 | +17.7 [+12.2, +23.5] | +682 [+438, +952] | -201 [-318, -104] P<=0 1.00 | +38 [-196, +258] P<=0 0.40 |
| quiet | vt_v1_m0.02_trigger | 0 | comp | s100 | 265.30 | 59.67 | +14.7 [+9.0, +21.0] | +1,089 [+626, +1,605] | +206 [+68, +357] P<=0 0.00 | +444 [+187, +713] P<=0 0.00 |
| quiet | vt_v1_m0.02_trigger | 0 | comp | dk0.5 | 249.69 | 36.42 | +20.3 [+13.3, +27.5] | +796 [+474, +1,154] | -88 [-178, -8] P<=0 0.98 | +151 [-78, +375] P<=0 0.10 |
| quiet | vt_v1_m0.02_trigger | 0 | comp | dk1 | 265.30 | 37.89 | +19.4 [+12.9, +25.9] | +867 [+529, +1,241] | -16 [-77, +34] P<=0 0.71 | +222 [+6, +437] P<=0 0.02 |
| quiet | vt_v1_m0.02_trigger | 0 | comp | dk2 | 266.72 | 39.54 | +18.4 [+12.2, +25.0] | +883 [+546, +1,265] | -1 [-45, +37] P<=0 0.50 | +238 [+24, +453] P<=0 0.01 |
| quiet | vt_v1_m0.02_trigger | 0 | comp | rv1_30 | 273.81 | 31.38 | +19.8 [+13.5, +26.5] | +748 [+468, +1,077] | -135 [-239, -44] P<=0 1.00 | +103 [-133, +336] P<=0 0.21 |
| quiet | vt_v1_m0.02_trigger | 0 | comp | rv1_0 | 96.47 | 46.47 | +24.5 [+13.4, +37.0] | +443 [+220, +717] | -440 [-688, -229] P<=0 1.00 | -202 [-514, +90] P<=0 0.91 |
| quiet | vt_v1_m0.02_trigger | 0 | comp | rv3_30 | 270.98 | 37.01 | +18.9 [+13.0, +25.0] | +853 [+543, +1,206] | -31 [-109, +40] P<=0 0.79 | +208 [-0, +430] P<=0 0.03 |
| quiet | vt_v1_m0.02_trigger | 0 | comp | rv3_0 | 187.27 | 43.14 | +21.7 [+14.9, +29.3] | +773 [+473, +1,123] | -111 [-275, +30] P<=0 0.93 | +128 [-117, +386] P<=0 0.16 |
| quiet | vt_v1_m0.02_trigger | 0 | comp | dk1_rv1 | 269.56 | 29.15 | +21.9 [+15.1, +28.9] | +740 [+458, +1,064] | -144 [-258, -39] P<=0 1.00 | +95 [-146, +336] P<=0 0.24 |
| quiet | vt_v1_m0.02_trigger | 0 | comp | sl0 | 187.27 | 33.78 | +20.7 [+13.0, +28.9] | +616 [+357, +917] | -268 [-413, -146] P<=0 1.00 | -29 [-284, +206] P<=0 0.61 |
| quiet | vt_v1_m0.02_trigger | 0 | comp | sl1 | 225.58 | 39.36 | +20.0 [+12.9, +27.5] | +807 [+482, +1,176] | -76 [-144, -11] P<=0 0.99 | +162 [-63, +383] P<=0 0.08 |
| quiet | vt_v1_m0.02_trigger | 0 | e+25 | 60 | 306.44 | 47.57 | +19.1 [+14.3, +24.3] | +1,241 [+834, +1,679] |  |  |
| quiet | vt_v1_m0.02_trigger | 0 | e+25 | s20 | 309.28 | 18.65 | +22.4 [+16.4, +29.0] | +556 [+375, +762] | -685 [-939, -454] P<=0 1.00 | -363 [-740, -48] P<=0 0.99 |
| quiet | vt_v1_m0.02_trigger | 0 | e+25 | s40 | 306.44 | 34.09 | +20.6 [+15.2, +26.2] | +943 [+633, +1,277] | -298 [-414, -193] P<=0 1.00 | +24 [-294, +298] P<=0 0.46 |
| quiet | vt_v1_m0.02_trigger | 0 | e+25 | s100 | 305.02 | 71.21 | +17.5 [+12.5, +22.9] | +1,716 [+1,130, +2,377] | +475 [+277, +714] P<=0 0.00 | +797 [+408, +1,183] P<=0 0.00 |
| quiet | vt_v1_m0.02_trigger | 0 | e+25 | dk0.5 | 285.16 | 38.99 | +21.4 [+15.5, +27.4] | +1,007 [+645, +1,402] | -234 [-371, -112] P<=0 1.00 | +89 [-245, +390] P<=0 0.32 |
| quiet | vt_v1_m0.02_trigger | 0 | e+25 | dk1 | 303.61 | 41.60 | +21.1 [+15.6, +26.7] | +1,155 [+758, +1,579] | -86 [-169, -14] P<=0 0.99 | +236 [-87, +521] P<=0 0.08 |
| quiet | vt_v1_m0.02_trigger | 0 | e+25 | dk2 | 303.61 | 44.35 | +20.8 [+15.5, +26.2] | +1,233 [+823, +1,683] | -8 [-54, +33] P<=0 0.64 | +314 [+2, +590] P<=0 0.02 |
| quiet | vt_v1_m0.02_trigger | 0 | e+25 | rv1_30 | 307.86 | 34.74 | +21.8 [+16.0, +27.7] | +1,003 [+664, +1,370] | -238 [-354, -137] P<=0 1.00 | +84 [-232, +370] P<=0 0.32 |
| quiet | vt_v1_m0.02_trigger | 0 | e+25 | rv1_0 | 102.15 | 52.73 | +24.0 [+14.0, +35.4] | +526 [+285, +812] | -715 [-1,037, -444] P<=0 1.00 | -393 [-812, -27] P<=0 0.98 |
| quiet | vt_v1_m0.02_trigger | 0 | e+25 | rv3_30 | 306.44 | 41.46 | +20.7 [+15.5, +26.2] | +1,161 [+785, +1,566] | -80 [-163, -9] P<=0 0.99 | +243 [-65, +514] P<=0 0.06 |
| quiet | vt_v1_m0.02_trigger | 0 | e+25 | rv3_0 | 211.39 | 48.49 | +23.0 [+17.0, +29.9] | +1,032 [+668, +1,421] | -209 [-387, -63] P<=0 1.00 | +113 [-206, +409] P<=0 0.26 |
| quiet | vt_v1_m0.02_trigger | 0 | e+25 | dk1_rv1 | 305.02 | 31.56 | +23.1 [+16.8, +29.4] | +937 [+616, +1,294] | -304 [-440, -182] P<=0 1.00 | +18 [-308, +315] P<=0 0.48 |
| quiet | vt_v1_m0.02_trigger | 0 | e+25 | sl0 | 204.30 | 42.82 | +22.5 [+15.7, +29.8] | +915 [+586, +1,301] | -326 [-488, -186] P<=0 1.00 | -4 [-329, +274] P<=0 0.53 |
| quiet | vt_v1_m0.02_trigger | 0 | e+25 | sl1 | 246.86 | 46.02 | +22.3 [+16.1, +28.6] | +1,154 [+771, +1,581] | -87 [-169, -15] P<=0 0.99 | +236 [-82, +524] P<=0 0.07 |
| busy | vt_v1_m0.02_trigger | 0 | base | 60 | 1,428.00 | 49.84 | +3.5 [-1.6, +9.4] | +866 [-444, +2,171] |  |  |
| busy | vt_v1_m0.02_trigger | 0 | base | s20 | 1,434.00 | 18.68 | +4.3 [-0.8, +9.9] | +405 [-86, +887] | -461 [-1,260, +379] P<=0 0.86 | +30 [-1,472, +1,216] P<=0 0.46 |
| busy | vt_v1_m0.02_trigger | 0 | base | s40 | 1,428.00 | 35.22 | +3.8 [-1.4, +9.7] | +672 [-269, +1,595] | -195 [-570, +204] P<=0 0.84 | +297 [-1,291, +1,644] P<=0 0.34 |
| busy | vt_v1_m0.02_trigger | 0 | base | s100 | 1,428.00 | 73.96 | +2.7 [-2.4, +8.8] | +994 [-939, +2,824] | +128 [-522, +776] P<=0 0.34 | +619 [-1,496, +2,584] P<=0 0.28 |
| busy | vt_v1_m0.02_trigger | 0 | base | dk0.5 | 1,362.00 | 38.60 | +2.3 [-2.9, +8.3] | +414 [-575, +1,334] | -452 [-977, +18] P<=0 0.97 | +39 [-1,619, +1,372] P<=0 0.46 |
| busy | vt_v1_m0.02_trigger | 0 | base | dk1 | 1,428.00 | 42.94 | +2.6 [-2.2, +8.0] | +560 [-525, +1,587] | -306 [-777, +61] P<=0 0.94 | +185 [-1,504, +1,600] P<=0 0.39 |
| busy | vt_v1_m0.02_trigger | 0 | base | dk2 | 1,428.00 | 46.98 | +2.7 [-2.0, +8.0] | +650 [-486, +1,753] | -216 [-643, +66] P<=0 0.89 | +275 [-1,418, +1,750] P<=0 0.36 |
| busy | vt_v1_m0.02_trigger | 0 | base | rv1_30 | 1,428.00 | 32.59 | +4.0 [-1.4, +10.0] | +643 [-222, +1,531] | -223 [-667, +270] P<=0 0.82 | +268 [-1,333, +1,610] P<=0 0.36 |
| busy | vt_v1_m0.02_trigger | 0 | base | rv1_0 | 306.00 | 53.54 | +4.9 [-7.1, +15.3] | +217 [-258, +768] | -649 [-1,627, +390] P<=0 0.89 | -158 [-1,772, +1,179] P<=0 0.57 |
| busy | vt_v1_m0.02_trigger | 0 | base | rv3_30 | 1,428.00 | 40.26 | +3.6 [-2.4, +9.9] | +681 [-470, +1,819] | -186 [-500, +111] P<=0 0.88 | +306 [-1,386, +1,779] P<=0 0.34 |
| busy | vt_v1_m0.02_trigger | 0 | base | rv3_0 | 786.00 | 51.57 | +3.1 [-6.0, +11.2] | +359 [-626, +1,379] | -507 [-1,234, +119] P<=0 0.93 | -16 [-1,701, +1,450] P<=0 0.50 |
| busy | vt_v1_m0.02_trigger | 0 | base | dk1_rv1 | 1,428.00 | 30.11 | +3.4 [-1.7, +8.9] | +500 [-277, +1,271] | -367 [-1,002, +249] P<=0 0.88 | +124 [-1,468, +1,450] P<=0 0.42 |
| busy | vt_v1_m0.02_trigger | 0 | base | sl0 | 654.00 | 45.78 | +6.9 [-1.1, +16.6] | +644 [-101, +1,467] | -222 [-858, +528] P<=0 0.75 | +269 [-1,337, +1,542] P<=0 0.34 |
| busy | vt_v1_m0.02_trigger | 0 | base | sl1 | 1,062.00 | 48.36 | +4.4 [-1.6, +11.9] | +761 [-327, +1,886] | -105 [-429, +266] P<=0 0.74 | +386 [-1,344, +1,846] P<=0 0.31 |
| busy | vt_v1_m0.02_trigger | 0 | comp | 60 | 1,200.00 | 43.86 | +1.5 [-4.3, +8.8] | +255 [-900, +1,353] |  |  |
| busy | vt_v1_m0.02_trigger | 0 | comp | s20 | 1,212.00 | 17.67 | +2.6 [-2.9, +9.4] | +190 [-247, +624] | -66 [-761, +661] P<=0 0.57 | +95 [-1,107, +1,140] P<=0 0.42 |
| busy | vt_v1_m0.02_trigger | 0 | comp | s40 | 1,212.00 | 31.83 | +1.9 [-3.7, +9.1] | +247 [-566, +1,028] | -8 [-355, +334] P<=0 0.52 | +153 [-1,099, +1,279] P<=0 0.40 |
| busy | vt_v1_m0.02_trigger | 0 | comp | s100 | 1,200.00 | 63.79 | +0.9 [-5.0, +8.8] | +223 [-1,504, +1,881] | -33 [-652, +590] P<=0 0.55 | +128 [-1,607, +1,735] P<=0 0.45 |
| busy | vt_v1_m0.02_trigger | 0 | comp | dk0.5 | 1,164.00 | 35.65 | -0.3 [-5.4, +6.3] | -38 [-915, +740] | -294 [-803, +118] P<=0 0.90 | -133 [-1,450, +1,001] P<=0 0.58 |
| busy | vt_v1_m0.02_trigger | 0 | comp | dk1 | 1,206.00 | 38.71 | +0.5 [-4.6, +6.8] | +73 [-886, +937] | -182 [-653, +135] P<=0 0.79 | -22 [-1,369, +1,145] P<=0 0.51 |
| busy | vt_v1_m0.02_trigger | 0 | comp | dk2 | 1,206.00 | 41.33 | +0.7 [-4.3, +7.0] | +115 [-882, +1,023] | -141 [-550, +125] P<=0 0.72 | +20 [-1,326, +1,211] P<=0 0.49 |
| busy | vt_v1_m0.02_trigger | 0 | comp | rv1_30 | 1,212.00 | 29.86 | +2.9 [-3.4, +10.0] | +338 [-428, +1,108] | +83 [-344, +523] P<=0 0.35 | +244 [-1,029, +1,392] P<=0 0.36 |
| busy | vt_v1_m0.02_trigger | 0 | comp | rv1_0 | 276.00 | 47.61 | +6.2 [-9.1, +18.2] | +210 [-221, +730] | -45 [-943, +879] P<=0 0.54 | +116 [-1,248, +1,327] P<=0 0.42 |
| busy | vt_v1_m0.02_trigger | 0 | comp | rv3_30 | 1,206.00 | 36.43 | +1.9 [-4.8, +9.5] | +265 [-719, +1,209] | +9 [-289, +286] P<=0 0.46 | +170 [-1,183, +1,374] P<=0 0.39 |
| busy | vt_v1_m0.02_trigger | 0 | comp | rv3_0 | 690.00 | 45.26 | +1.3 [-10.6, +11.4] | +106 [-780, +1,022] | -149 [-868, +481] P<=0 0.65 | +12 [-1,392, +1,299] P<=0 0.49 |
| busy | vt_v1_m0.02_trigger | 0 | comp | dk1_rv1 | 1,206.00 | 27.70 | +2.0 [-3.7, +8.5] | +224 [-438, +907] | -31 [-607, +506] P<=0 0.53 | +129 [-1,152, +1,253] P<=0 0.41 |
| busy | vt_v1_m0.02_trigger | 0 | comp | sl0 | 540.00 | 40.45 | +5.0 [-4.6, +18.2] | +325 [-315, +1,070] | +69 [-483, +704] P<=0 0.42 | +230 [-1,025, +1,267] P<=0 0.34 |
| busy | vt_v1_m0.02_trigger | 0 | comp | sl1 | 894.00 | 41.35 | +2.3 [-4.8, +12.1] | +268 [-671, +1,229] | +13 [-266, +301] P<=0 0.46 | +174 [-1,158, +1,356] P<=0 0.40 |
| busy | vt_v1_m0.02_trigger | 0 | e+25 | 60 | 1,278.00 | 51.30 | +2.7 [-2.8, +9.6] | +604 [-716, +1,922] |  |  |
| busy | vt_v1_m0.02_trigger | 0 | e+25 | s20 | 1,284.00 | 19.09 | +3.8 [-1.5, +10.0] | +323 [-144, +787] | -281 [-1,137, +563] P<=0 0.74 | +27 [-1,353, +1,169] P<=0 0.47 |
| busy | vt_v1_m0.02_trigger | 0 | e+25 | s40 | 1,278.00 | 36.26 | +3.0 [-2.3, +9.5] | +480 [-429, +1,386] | -124 [-539, +280] P<=0 0.72 | +184 [-1,308, +1,473] P<=0 0.40 |
| busy | vt_v1_m0.02_trigger | 0 | e+25 | s100 | 1,272.00 | 77.26 | +1.9 [-3.8, +9.1] | +635 [-1,476, +2,617] | +31 [-727, +747] P<=0 0.47 | +339 [-1,801, +2,368] P<=0 0.38 |
| busy | vt_v1_m0.02_trigger | 0 | e+25 | dk0.5 | 1,224.00 | 39.71 | +0.9 [-4.4, +7.2] | +153 [-805, +1,045] | -451 [-1,013, +34] P<=0 0.96 | -143 [-1,674, +1,126] P<=0 0.57 |
| busy | vt_v1_m0.02_trigger | 0 | e+25 | dk1 | 1,278.00 | 44.09 | +1.7 [-3.4, +7.8] | +330 [-733, +1,342] | -274 [-744, +82] P<=0 0.92 | +34 [-1,520, +1,381] P<=0 0.49 |
| busy | vt_v1_m0.02_trigger | 0 | e+25 | dk2 | 1,278.00 | 48.06 | +1.9 [-3.0, +7.9] | +408 [-726, +1,495] | -195 [-617, +79] P<=0 0.86 | +112 [-1,448, +1,529] P<=0 0.45 |
| busy | vt_v1_m0.02_trigger | 0 | e+25 | rv1_30 | 1,278.00 | 33.60 | +3.4 [-2.5, +9.9] | +485 [-374, +1,343] | -119 [-629, +406] P<=0 0.66 | +189 [-1,310, +1,503] P<=0 0.40 |
| busy | vt_v1_m0.02_trigger | 0 | e+25 | rv1_0 | 288.00 | 54.14 | +4.4 [-8.9, +15.7] | +181 [-291, +726] | -423 [-1,435, +668] P<=0 0.78 | -115 [-1,615, +1,188] P<=0 0.56 |
| busy | vt_v1_m0.02_trigger | 0 | e+25 | rv3_30 | 1,278.00 | 41.31 | +2.5 [-3.8, +9.4] | +431 [-672, +1,502] | -173 [-601, +187] P<=0 0.80 | +135 [-1,429, +1,559] P<=0 0.44 |
| busy | vt_v1_m0.02_trigger | 0 | e+25 | rv3_0 | 720.00 | 51.64 | +0.8 [-9.4, +9.9] | +87 [-868, +1,091] | -517 [-1,364, +191] P<=0 0.90 | -209 [-1,767, +1,185] P<=0 0.61 |
| busy | vt_v1_m0.02_trigger | 0 | e+25 | dk1_rv1 | 1,278.00 | 30.94 | +2.6 [-3.0, +8.7] | +347 [-392, +1,102] | -257 [-967, +395] P<=0 0.76 | +51 [-1,433, +1,325] P<=0 0.47 |
| busy | vt_v1_m0.02_trigger | 0 | e+25 | sl0 | 576.00 | 45.04 | +7.0 [-2.6, +19.9] | +549 [-206, +1,416] | -55 [-692, +670] P<=0 0.56 | +253 [-1,250, +1,523] P<=0 0.36 |
| busy | vt_v1_m0.02_trigger | 0 | e+25 | sl1 | 948.00 | 48.88 | +3.3 [-3.1, +12.0] | +514 [-569, +1,658] | -90 [-426, +272] P<=0 0.72 | +218 [-1,387, +1,682] P<=0 0.39 |
| unseen | vt_v1_m0.02_trigger | 0 | base | 60 | 561.08 | 48.29 | +12.0 [+7.7, +16.4] | +1,288 [+862, +1,746] |  |  |
| unseen | vt_v1_m0.02_trigger | 0 | base | s20 | 564.53 | 18.68 | +14.4 [+9.8, +19.6] | +600 [+414, +811] | -688 [-960, -437] P<=0 1.00 | -400 [-828, -33] P<=0 0.98 |
| unseen | vt_v1_m0.02_trigger | 0 | base | s40 | 561.08 | 34.56 | +13.1 [+8.7, +17.8] | +1,011 [+687, +1,364] | -277 [-404, -162] P<=0 1.00 | +10 [-389, +360] P<=0 0.50 |
| unseen | vt_v1_m0.02_trigger | 0 | base | s100 | 558.79 | 71.99 | +10.8 [+6.6, +15.2] | +1,723 [+1,097, +2,378] | +435 [+217, +675] P<=0 0.00 | +722 [+218, +1,198] P<=0 0.00 |
| unseen | vt_v1_m0.02_trigger | 0 | base | dk0.5 | 531.25 | 38.25 | +12.5 [+7.9, +17.6] | +971 [+616, +1,345] | -317 [-474, -176] P<=0 1.00 | -30 [-455, +319] P<=0 0.58 |
| unseen | vt_v1_m0.02_trigger | 0 | base | dk1 | 558.79 | 42.02 | +12.4 [+7.9, +17.1] | +1,136 [+747, +1,558] | -152 [-264, -53] P<=0 1.00 | +135 [-289, +493] P<=0 0.26 |
| unseen | vt_v1_m0.02_trigger | 0 | base | dk2 | 558.79 | 45.37 | +12.3 [+8.0, +17.0] | +1,232 [+828, +1,674] | -56 [-145, +13] P<=0 0.92 | +232 [-190, +583] P<=0 0.13 |
| unseen | vt_v1_m0.02_trigger | 0 | base | rv1_30 | 562.23 | 33.55 | +14.4 [+9.7, +19.3] | +1,057 [+717, +1,415] | -230 [-358, -102] P<=0 1.00 | +57 [-357, +413] P<=0 0.40 |
| unseen | vt_v1_m0.02_trigger | 0 | base | rv1_0 | 149.16 | 53.90 | +18.8 [+11.3, +26.6] | +547 [+306, +822] | -741 [-1,071, -421] P<=0 1.00 | -454 [-910, -34] P<=0 0.98 |
| unseen | vt_v1_m0.02_trigger | 0 | base | rv3_30 | 561.08 | 40.58 | +13.5 [+9.0, +18.1] | +1,195 [+800, +1,610] | -92 [-177, -11] P<=0 0.98 | +195 [-226, +551] P<=0 0.17 |
| unseen | vt_v1_m0.02_trigger | 0 | base | rv3_0 | 347.67 | 49.33 | +16.0 [+10.9, +21.5] | +1,024 [+671, +1,408] | -264 [-452, -83] P<=0 1.00 | +23 [-396, +396] P<=0 0.47 |
| unseen | vt_v1_m0.02_trigger | 0 | base | dk1_rv1 | 559.94 | 30.78 | +14.3 [+9.7, +19.5] | +957 [+638, +1,308] | -331 [-500, -167] P<=0 1.00 | -44 [-451, +309] P<=0 0.60 |
| unseen | vt_v1_m0.02_trigger | 0 | base | sl0 | 309.80 | 44.01 | +17.1 [+11.5, +23.4] | +922 [+598, +1,261] | -366 [-555, -174] P<=0 1.00 | -78 [-498, +273] P<=0 0.67 |
| unseen | vt_v1_m0.02_trigger | 0 | base | sl1 | 429.13 | 47.30 | +14.6 [+9.6, +20.1] | +1,173 [+787, +1,579] | -115 [-229, -17] P<=0 0.99 | +172 [-265, +528] P<=0 0.21 |
| unseen | vt_v1_m0.02_trigger | 0 | comp | 60 | 447.49 | 43.31 | +10.0 [+5.0, +15.5] | +763 [+402, +1,136] |  |  |
| unseen | vt_v1_m0.02_trigger | 0 | comp | s20 | 453.23 | 17.53 | +12.4 [+7.3, +18.0] | +387 [+235, +543] | -376 [-610, -161] P<=0 1.00 | -153 [-486, +156] P<=0 0.84 |
| unseen | vt_v1_m0.02_trigger | 0 | comp | s40 | 452.08 | 31.52 | +10.7 [+5.9, +16.2] | +599 [+345, +864] | -164 [-282, -57] P<=0 1.00 | +60 [-244, +335] P<=0 0.36 |
| unseen | vt_v1_m0.02_trigger | 0 | comp | s100 | 444.05 | 61.80 | +8.5 [+3.5, +14.1] | +923 [+403, +1,456] | +160 [-11, +337] P<=0 0.04 | +384 [-30, +746] P<=0 0.03 |
| unseen | vt_v1_m0.02_trigger | 0 | comp | dk0.5 | 424.54 | 36.02 | +10.9 [+5.6, +17.3] | +636 [+337, +962] | -127 [-249, -27] P<=0 0.99 | +97 [-224, +384] P<=0 0.28 |
| unseen | vt_v1_m0.02_trigger | 0 | comp | dk1 | 445.20 | 38.31 | +10.8 [+5.7, +16.6] | +715 [+382, +1,066] | -48 [-147, +30] P<=0 0.84 | +176 [-140, +469] P<=0 0.14 |
| unseen | vt_v1_m0.02_trigger | 0 | comp | dk2 | 446.34 | 40.46 | +10.4 [+5.5, +16.1] | +736 [+401, +1,089] | -28 [-114, +38] P<=0 0.73 | +196 [-124, +488] P<=0 0.11 |
| unseen | vt_v1_m0.02_trigger | 0 | comp | rv1_30 | 453.23 | 30.61 | +12.6 [+7.3, +18.3] | +670 [+389, +968] | -94 [-210, +28] P<=0 0.94 | +130 [-185, +427] P<=0 0.21 |
| unseen | vt_v1_m0.02_trigger | 0 | comp | rv1_0 | 130.80 | 46.93 | +18.9 [+10.0, +28.3] | +399 [+188, +637] | -365 [-637, -97] P<=0 1.00 | -141 [-497, +205] P<=0 0.80 |
| unseen | vt_v1_m0.02_trigger | 0 | comp | rv3_30 | 449.78 | 36.71 | +11.8 [+6.6, +17.3] | +740 [+422, +1,076] | -23 [-109, +58] P<=0 0.70 | +200 [-120, +494] P<=0 0.10 |
| unseen | vt_v1_m0.02_trigger | 0 | comp | rv3_0 | 283.41 | 44.12 | +14.4 [+8.2, +20.8] | +645 [+350, +970] | -118 [-303, +56] P<=0 0.90 | +106 [-221, +429] P<=0 0.28 |
| unseen | vt_v1_m0.02_trigger | 0 | comp | dk1_rv1 | 448.64 | 28.41 | +13.2 [+7.7, +19.4] | +641 [+372, +928] | -122 [-270, +21] P<=0 0.96 | +102 [-215, +399] P<=0 0.28 |
| unseen | vt_v1_m0.02_trigger | 0 | comp | sl0 | 254.73 | 36.48 | +15.3 [+8.7, +23.1] | +560 [+314, +836] | -203 [-355, -46] P<=0 1.00 | +20 [-300, +305] P<=0 0.47 |
| unseen | vt_v1_m0.02_trigger | 0 | comp | sl1 | 353.40 | 40.32 | +12.8 [+6.5, +19.8] | +704 [+376, +1,045] | -59 [-132, +11] P<=0 0.94 | +165 [-164, +451] P<=0 0.16 |
| unseen | vt_v1_m0.02_trigger | 0 | e+25 | 60 | 492.24 | 49.43 | +11.7 [+7.1, +16.8] | +1,119 [+706, +1,553] |  |  |
| unseen | vt_v1_m0.02_trigger | 0 | e+25 | s20 | 495.68 | 18.87 | +14.0 [+9.0, +19.6] | +512 [+338, +708] | -608 [-881, -352] P<=0 1.00 | -288 [-690, +61] P<=0 0.95 |
| unseen | vt_v1_m0.02_trigger | 0 | e+25 | s40 | 492.24 | 35.17 | +12.6 [+7.8, +17.8] | +854 [+556, +1,186] | -265 [-393, -147] P<=0 1.00 | +55 [-334, +383] P<=0 0.40 |
| unseen | vt_v1_m0.02_trigger | 0 | e+25 | s100 | 489.94 | 74.21 | +10.6 [+5.9, +15.7] | +1,509 [+874, +2,166] | +390 [+162, +629] P<=0 0.00 | +710 [+196, +1,201] P<=0 0.00 |
| unseen | vt_v1_m0.02_trigger | 0 | e+25 | dk0.5 | 464.70 | 39.35 | +12.1 [+7.1, +17.8] | +844 [+510, +1,216] | -275 [-424, -138] P<=0 1.00 | +44 [-365, +406] P<=0 0.42 |
| unseen | vt_v1_m0.02_trigger | 0 | e+25 | dk1 | 489.94 | 42.84 | +12.2 [+7.4, +17.6] | +997 [+626, +1,405] | -122 [-233, -30] P<=0 1.00 | +197 [-217, +554] P<=0 0.16 |
| unseen | vt_v1_m0.02_trigger | 0 | e+25 | dk2 | 489.94 | 46.20 | +12.2 [+7.4, +17.3] | +1,075 [+689, +1,501] | -44 [-128, +21] P<=0 0.86 | +276 [-132, +628] P<=0 0.09 |
| unseen | vt_v1_m0.02_trigger | 0 | e+25 | rv1_30 | 493.39 | 34.18 | +14.0 [+8.9, +19.2] | +904 [+587, +1,245] | -215 [-349, -80] P<=0 1.00 | +104 [-278, +449] P<=0 0.29 |
| unseen | vt_v1_m0.02_trigger | 0 | e+25 | rv1_0 | 137.69 | 53.30 | +18.0 [+10.0, +26.3] | +460 [+230, +718] | -659 [-986, -337] P<=0 1.00 | -339 [-777, +60] P<=0 0.95 |
| unseen | vt_v1_m0.02_trigger | 0 | e+25 | rv3_30 | 492.24 | 41.39 | +13.1 [+8.3, +18.1] | +1,022 [+658, +1,418] | -97 [-201, -4] P<=0 0.98 | +222 [-178, +564] P<=0 0.13 |
| unseen | vt_v1_m0.02_trigger | 0 | e+25 | rv3_0 | 308.65 | 49.89 | +15.2 [+9.7, +21.2] | +851 [+514, +1,219] | -268 [-482, -80] P<=0 1.00 | +52 [-348, +414] P<=0 0.41 |
| unseen | vt_v1_m0.02_trigger | 0 | e+25 | dk1_rv1 | 491.09 | 31.25 | +14.1 [+8.9, +19.7] | +824 [+526, +1,148] | -295 [-464, -127] P<=0 1.00 | +25 [-376, +371] P<=0 0.46 |
| unseen | vt_v1_m0.02_trigger | 0 | e+25 | sl0 | 275.38 | 43.71 | +17.6 [+11.4, +24.5] | +845 [+528, +1,190] | -274 [-438, -103] P<=0 1.00 | +45 [-350, +386] P<=0 0.41 |
| unseen | vt_v1_m0.02_trigger | 0 | e+25 | sl1 | 380.94 | 47.38 | +14.4 [+8.8, +20.6] | +1,032 [+657, +1,447] | -87 [-183, +1] P<=0 0.97 | +232 [-190, +592] P<=0 0.12 |

## Size rules: vt_v1_m0.02_trigger, L = -40
| group | arm | L | fill model | size | fills/day | sh/fill | mk10 c/$ | mk10 $/day | vs 60 sh $/day | gain vs micf $/day |
|---|---|---|---|---|---|---|---|---|---|---|
| select | vt_v1_m0.02_trigger | -40 | base | 60 | 1,238.00 | 40.49 | +8.4 [+5.7, +11.4] | +2,115 [+1,335, +2,900] |  |  |
| select | vt_v1_m0.02_trigger | -40 | base | s20 | 1,244.00 | 16.74 | +9.0 [+6.6, +11.8] | +937 [+651, +1,227] | -1,178 [-1,700, -704] P<=0 1.00 | -496 [-1,232, +151] P<=0 0.93 |
| select | vt_v1_m0.02_trigger | -40 | base | s40 | 1,240.00 | 29.54 | +8.6 [+6.1, +11.5] | +1,572 [+1,043, +2,112] | -542 [-800, -315] P<=0 1.00 | +140 [-490, +752] P<=0 0.34 |
| select | vt_v1_m0.02_trigger | -40 | base | s100 | 1,232.00 | 58.88 | +8.2 [+5.2, +11.3] | +3,001 [+1,786, +4,218] | +887 [+473, +1,352] P<=0 0.00 | +1,569 [+715, +2,468] P<=0 0.00 |
| select | vt_v1_m0.02_trigger | -40 | base | dk0.5 | 1,162.00 | 33.07 | +9.8 [+6.6, +13.3] | +1,844 [+1,154, +2,534] | -271 [-535, -37] P<=0 0.99 | +411 [-223, +1,023] P<=0 0.10 |
| select | vt_v1_m0.02_trigger | -40 | base | dk1 | 1,222.00 | 35.85 | +9.4 [+6.5, +12.5] | +2,044 [+1,310, +2,777] | -71 [-276, +116] P<=0 0.76 | +611 [-31, +1,267] P<=0 0.03 |
| select | vt_v1_m0.02_trigger | -40 | base | dk2 | 1,230.00 | 38.38 | +8.9 [+6.1, +12.0] | +2,105 [+1,358, +2,855] | -9 [-139, +117] P<=0 0.56 | +673 [+45, +1,309] P<=0 0.02 |
| select | vt_v1_m0.02_trigger | -40 | base | rv1_30 | 1,240.00 | 27.62 | +10.0 [+6.9, +13.4] | +1,659 [+1,080, +2,268] | -455 [-734, -202] P<=0 1.00 | +227 [-383, +846] P<=0 0.25 |
| select | vt_v1_m0.02_trigger | -40 | base | rv1_0 | 286.00 | 41.72 | +18.4 [+9.5, +30.2] | +896 [+454, +1,424] | -1,218 [-1,833, -692] P<=0 1.00 | -536 [-1,253, +155] P<=0 0.94 |
| select | vt_v1_m0.02_trigger | -40 | base | rv3_30 | 1,238.00 | 32.97 | +9.7 [+6.8, +13.0] | +1,962 [+1,278, +2,713] | -153 [-401, +63] P<=0 0.92 | +529 [-90, +1,153] P<=0 0.05 |
| select | vt_v1_m0.02_trigger | -40 | base | rv3_0 | 702.00 | 39.80 | +12.3 [+7.9, +17.5] | +1,661 [+983, +2,464] | -453 [-962, -10] P<=0 0.98 | +229 [-458, +942] P<=0 0.28 |
| select | vt_v1_m0.02_trigger | -40 | base | dk1_rv1 | 1,224.00 | 25.89 | +10.6 [+7.3, +14.3] | +1,609 [+1,040, +2,216] | -505 [-825, -222] P<=0 1.00 | +177 [-432, +795] P<=0 0.29 |
| select | vt_v1_m0.02_trigger | -40 | base | sl0 | 738.00 | 38.20 | +12.3 [+8.0, +16.9] | +1,672 [+994, +2,341] | -442 [-732, -204] P<=0 1.00 | +240 [-398, +860] P<=0 0.24 |
| select | vt_v1_m0.02_trigger | -40 | base | sl1 | 1,024.00 | 38.04 | +9.8 [+6.7, +13.2] | +1,886 [+1,158, +2,613] | -229 [-440, -54] P<=0 1.00 | +453 [-184, +1,105] P<=0 0.09 |
| select | vt_v1_m0.02_trigger | -40 | comp | 60 | 800.00 | 39.46 | +6.5 [+3.2, +10.3] | +1,054 [+502, +1,645] |  |  |
| select | vt_v1_m0.02_trigger | -40 | comp | s20 | 808.00 | 16.27 | +7.4 [+4.3, +11.1] | +491 [+276, +720] | -562 [-952, -227] P<=0 1.00 | -119 [-741, +461] P<=0 0.66 |
| select | vt_v1_m0.02_trigger | -40 | comp | s40 | 804.00 | 28.76 | +6.9 [+3.7, +10.6] | +812 [+410, +1,236] | -242 [-425, -80] P<=0 1.00 | +202 [-351, +759] P<=0 0.24 |
| select | vt_v1_m0.02_trigger | -40 | comp | s100 | 794.00 | 57.63 | +5.5 [+2.2, +9.1] | +1,279 [+496, +2,115] | +225 [-30, +524] P<=0 0.04 | +669 [+27, +1,357] P<=0 0.02 |
| select | vt_v1_m0.02_trigger | -40 | comp | dk0.5 | 756.00 | 33.13 | +7.7 [+3.8, +12.0] | +950 [+451, +1,472] | -104 [-336, +78] P<=0 0.84 | +340 [-222, +916] P<=0 0.12 |
| select | vt_v1_m0.02_trigger | -40 | comp | dk1 | 786.00 | 35.83 | +7.2 [+3.8, +11.1] | +1,020 [+508, +1,564] | -33 [-212, +105] P<=0 0.65 | +410 [-149, +992] P<=0 0.08 |
| select | vt_v1_m0.02_trigger | -40 | comp | dk2 | 794.00 | 37.78 | +6.8 [+3.5, +10.5] | +1,042 [+519, +1,597] | -12 [-117, +73] P<=0 0.58 | +432 [-116, +996] P<=0 0.06 |
| select | vt_v1_m0.02_trigger | -40 | comp | rv1_30 | 806.00 | 27.40 | +8.1 [+4.3, +12.2] | +877 [+437, +1,347] | -176 [-392, +0] P<=0 0.97 | +267 [-303, +849] P<=0 0.19 |
| select | vt_v1_m0.02_trigger | -40 | comp | rv1_0 | 200.00 | 41.65 | +17.8 [+7.3, +31.0] | +599 [+235, +1,023] | -455 [-903, -71] P<=0 0.99 | -11 [-658, +625] P<=0 0.52 |
| select | vt_v1_m0.02_trigger | -40 | comp | rv3_30 | 804.00 | 32.16 | +8.0 [+4.4, +12.0] | +1,031 [+535, +1,593] | -22 [-214, +137] P<=0 0.60 | +421 [-136, +982] P<=0 0.07 |
| select | vt_v1_m0.02_trigger | -40 | comp | rv3_0 | 446.00 | 39.74 | +12.0 [+6.2, +19.0] | +1,026 [+503, +1,667] | -28 [-458, +349] P<=0 0.56 | +416 [-215, +1,051] P<=0 0.10 |
| select | vt_v1_m0.02_trigger | -40 | comp | dk1_rv1 | 792.00 | 26.00 | +8.8 [+4.8, +13.0] | +878 [+452, +1,331] | -175 [-429, +33] P<=0 0.94 | +268 [-310, +851] P<=0 0.18 |
| select | vt_v1_m0.02_trigger | -40 | comp | sl0 | 444.00 | 36.35 | +10.0 [+4.4, +16.6] | +775 [+321, +1,271] | -278 [-581, -29] P<=0 0.99 | +166 [-405, +677] P<=0 0.28 |
| select | vt_v1_m0.02_trigger | -40 | comp | sl1 | 612.00 | 37.16 | +8.1 [+4.0, +12.8] | +899 [+412, +1,426] | -155 [-392, +30] P<=0 0.94 | +289 [-258, +802] P<=0 0.15 |
| select | vt_v1_m0.02_trigger | -40 | e+25 | 60 | 940.00 | 44.00 | +7.2 [+4.0, +10.7] | +1,485 [+798, +2,211] |  |  |
| select | vt_v1_m0.02_trigger | -40 | e+25 | s20 | 946.00 | 17.30 | +7.6 [+4.7, +11.1] | +616 [+361, +895] | -869 [-1,347, -441] P<=0 1.00 | -430 [-1,143, +196] P<=0 0.90 |
| select | vt_v1_m0.02_trigger | -40 | e+25 | s40 | 942.00 | 31.53 | +7.3 [+4.3, +10.7] | +1,079 [+609, +1,583] | -407 [-651, -193] P<=0 1.00 | +33 [-591, +618] P<=0 0.46 |
| select | vt_v1_m0.02_trigger | -40 | e+25 | s100 | 934.00 | 65.45 | +6.8 [+3.6, +10.3] | +2,108 [+1,080, +3,174] | +622 [+275, +1,022] P<=0 0.00 | +1,061 [+301, +1,832] P<=0 0.00 |
| select | vt_v1_m0.02_trigger | -40 | e+25 | dk0.5 | 888.00 | 35.75 | +8.7 [+5.0, +12.8] | +1,344 [+748, +1,980] | -141 [-410, +84] P<=0 0.87 | +298 [-332, +885] P<=0 0.17 |
| select | vt_v1_m0.02_trigger | -40 | e+25 | dk1 | 928.00 | 38.82 | +8.3 [+4.9, +11.9] | +1,466 [+811, +2,143] | -19 [-225, +164] P<=0 0.57 | +420 [-197, +1,025] P<=0 0.10 |
| select | vt_v1_m0.02_trigger | -40 | e+25 | dk2 | 934.00 | 41.48 | +7.7 [+4.6, +11.3] | +1,491 [+835, +2,168] | +6 [-121, +130] P<=0 0.46 | +445 [-157, +1,037] P<=0 0.08 |
| select | vt_v1_m0.02_trigger | -40 | e+25 | rv1_30 | 942.00 | 29.43 | +9.1 [+5.4, +13.2] | +1,219 [+681, +1,818] | -266 [-529, -32] P<=0 0.99 | +173 [-424, +759] P<=0 0.30 |
| select | vt_v1_m0.02_trigger | -40 | e+25 | rv1_0 | 220.00 | 46.24 | +19.5 [+9.2, +32.6] | +808 [+370, +1,340] | -677 [-1,242, -209] P<=0 1.00 | -238 [-934, +406] P<=0 0.75 |
| select | vt_v1_m0.02_trigger | -40 | e+25 | rv3_30 | 940.00 | 35.29 | +8.9 [+5.5, +12.7] | +1,459 [+819, +2,159] | -26 [-290, +200] P<=0 0.58 | +413 [-172, +980] P<=0 0.08 |
| select | vt_v1_m0.02_trigger | -40 | e+25 | rv3_0 | 514.00 | 44.54 | +12.5 [+7.3, +18.7] | +1,384 [+747, +2,161] | -102 [-653, +363] P<=0 0.65 | +337 [-335, +969] P<=0 0.16 |
| select | vt_v1_m0.02_trigger | -40 | e+25 | dk1_rv1 | 930.00 | 27.48 | +9.9 [+5.9, +14.4] | +1,204 [+678, +1,788] | -281 [-595, -10] P<=0 0.98 | +158 [-439, +741] P<=0 0.32 |
| select | vt_v1_m0.02_trigger | -40 | e+25 | sl0 | 496.00 | 43.39 | +11.6 [+6.7, +17.3] | +1,195 [+645, +1,782] | -290 [-627, +9] P<=0 0.97 | +149 [-483, +732] P<=0 0.32 |
| select | vt_v1_m0.02_trigger | -40 | e+25 | sl1 | 720.00 | 42.78 | +9.1 [+5.5, +13.3] | +1,376 [+767, +2,015] | -109 [-338, +97] P<=0 0.84 | +330 [-277, +894] P<=0 0.14 |
| quiet | vt_v1_m0.02_trigger | -40 | base | 60 | 1,197.40 | 43.36 | +10.3 [+8.0, +12.7] | +2,720 [+2,057, +3,415] |  |  |
| quiet | vt_v1_m0.02_trigger | -40 | base | s20 | 1,208.75 | 17.78 | +12.4 [+9.7, +15.2] | +1,306 [+986, +1,642] | -1,414 [-1,819, -1,049] P<=0 1.00 | -407 [-767, -82] P<=0 0.99 |
| quiet | vt_v1_m0.02_trigger | -40 | base | s40 | 1,201.66 | 31.70 | +11.2 [+8.8, +13.8] | +2,138 [+1,620, +2,696] | -581 [-761, -418] P<=0 1.00 | +425 [+147, +688] P<=0 0.00 |
| quiet | vt_v1_m0.02_trigger | -40 | base | s100 | 1,193.14 | 63.34 | +9.2 [+7.0, +11.6] | +3,613 [+2,707, +4,572] | +893 [+605, +1,227] P<=0 0.00 | +1,900 [+1,370, +2,460] P<=0 0.00 |
| quiet | vt_v1_m0.02_trigger | -40 | base | dk0.5 | 1,144.91 | 35.09 | +11.6 [+9.1, +14.1] | +2,287 [+1,718, +2,872] | -433 [-695, -201] P<=0 1.00 | +573 [+225, +922] P<=0 0.00 |
| quiet | vt_v1_m0.02_trigger | -40 | base | dk1 | 1,188.89 | 38.38 | +11.2 [+8.8, +13.7] | +2,564 [+1,958, +3,189] | -155 [-309, +0] P<=0 0.97 | +851 [+509, +1,185] P<=0 0.00 |
| quiet | vt_v1_m0.02_trigger | -40 | base | dk2 | 1,193.14 | 40.89 | +10.8 [+8.5, +13.4] | +2,680 [+2,050, +3,358] | -40 [-134, +61] P<=0 0.80 | +967 [+629, +1,293] P<=0 0.00 |
| quiet | vt_v1_m0.02_trigger | -40 | base | rv1_30 | 1,207.33 | 30.03 | +12.6 [+9.8, +15.5] | +2,225 [+1,688, +2,788] | -495 [-703, -301] P<=0 1.00 | +512 [+214, +788] P<=0 0.00 |
| quiet | vt_v1_m0.02_trigger | -40 | base | rv1_0 | 310.70 | 45.49 | +18.5 [+12.9, +25.1] | +1,132 [+779, +1,511] | -1,588 [-2,117, -1,101] P<=0 1.00 | -581 [-1,062, -178] P<=0 1.00 |
| quiet | vt_v1_m0.02_trigger | -40 | base | rv3_30 | 1,200.24 | 36.51 | +12.0 [+9.5, +14.8] | +2,587 [+1,986, +3,226] | -133 [-271, +9] P<=0 0.97 | +873 [+547, +1,172] P<=0 0.00 |
| quiet | vt_v1_m0.02_trigger | -40 | base | rv3_0 | 744.83 | 43.84 | +14.8 [+11.4, +18.6] | +2,270 [+1,745, +2,825] | -450 [-755, -137] P<=0 1.00 | +557 [+175, +928] P<=0 0.00 |
| quiet | vt_v1_m0.02_trigger | -40 | base | dk1_rv1 | 1,195.98 | 27.93 | +12.9 [+10.1, +15.9] | +2,089 [+1,591, +2,611] | -631 [-890, -392] P<=0 1.00 | +376 [+59, +666] P<=0 0.01 |
| quiet | vt_v1_m0.02_trigger | -40 | base | sl0 | 797.32 | 35.39 | +14.0 [+10.7, +17.6] | +1,893 [+1,409, +2,403] | -827 [-1,179, -526] P<=0 1.00 | +180 [-196, +530] P<=0 0.17 |
| quiet | vt_v1_m0.02_trigger | -40 | base | sl1 | 1,025.73 | 40.46 | +11.4 [+8.8, +14.3] | +2,390 [+1,805, +2,992] | -329 [-549, -164] P<=0 1.00 | +677 [+366, +976] P<=0 0.00 |
| quiet | vt_v1_m0.02_trigger | -40 | comp | 60 | 732.06 | 42.75 | +8.0 [+5.5, +10.7] | +1,302 [+870, +1,780] |  |  |
| quiet | vt_v1_m0.02_trigger | -40 | comp | s20 | 741.99 | 17.46 | +10.2 [+7.2, +13.4] | +672 [+457, +906] | -630 [-915, -384] P<=0 1.00 | -131 [-397, +118] P<=0 0.85 |
| quiet | vt_v1_m0.02_trigger | -40 | comp | s40 | 736.32 | 31.21 | +8.5 [+6.0, +11.4] | +1,011 [+685, +1,361] | -291 [-432, -170] P<=0 1.00 | +208 [-3, +423] P<=0 0.03 |
| quiet | vt_v1_m0.02_trigger | -40 | comp | s100 | 727.80 | 60.89 | +7.3 [+4.8, +9.9] | +1,717 [+1,117, +2,377] | +415 [+219, +629] P<=0 0.00 | +914 [+551, +1,308] P<=0 0.00 |
| quiet | vt_v1_m0.02_trigger | -40 | comp | dk0.5 | 693.75 | 35.65 | +9.6 [+6.7, +12.6] | +1,204 [+811, +1,627] | -98 [-254, +41] P<=0 0.92 | +401 [+140, +668] P<=0 0.00 |
| quiet | vt_v1_m0.02_trigger | -40 | comp | dk1 | 723.55 | 38.54 | +9.0 [+6.4, +12.0] | +1,309 [+886, +1,747] | +7 [-80, +98] P<=0 0.45 | +506 [+263, +770] P<=0 0.00 |
| quiet | vt_v1_m0.02_trigger | -40 | comp | dk2 | 727.80 | 40.57 | +8.5 [+5.9, +11.4] | +1,308 [+875, +1,767] | +6 [-56, +73] P<=0 0.44 | +505 [+259, +761] P<=0 0.00 |
| quiet | vt_v1_m0.02_trigger | -40 | comp | rv1_30 | 736.32 | 30.00 | +9.7 [+6.8, +12.9] | +1,076 [+721, +1,457] | -227 [-374, -101] P<=0 1.00 | +273 [+50, +496] P<=0 0.01 |
| quiet | vt_v1_m0.02_trigger | -40 | comp | rv1_0 | 194.36 | 47.21 | +14.8 [+8.5, +22.2] | +608 [+338, +918] | -694 [-1,041, -392] P<=0 1.00 | -194 [-531, +114] P<=0 0.90 |
| quiet | vt_v1_m0.02_trigger | -40 | comp | rv3_30 | 733.48 | 36.02 | +9.4 [+6.6, +12.4] | +1,258 [+853, +1,690] | -44 [-136, +48] P<=0 0.82 | +456 [+217, +711] P<=0 0.00 |
| quiet | vt_v1_m0.02_trigger | -40 | comp | rv3_0 | 461.08 | 42.96 | +11.9 [+8.2, +16.1] | +1,141 [+777, +1,549] | -161 [-363, +44] P<=0 0.94 | +339 [+58, +651] P<=0 0.01 |
| quiet | vt_v1_m0.02_trigger | -40 | comp | dk1_rv1 | 727.80 | 28.16 | +10.4 [+7.4, +13.8] | +1,067 [+722, +1,439] | -235 [-403, -85] P<=0 1.00 | +264 [+31, +496] P<=0 0.02 |
| quiet | vt_v1_m0.02_trigger | -40 | comp | sl0 | 418.52 | 35.23 | +13.2 [+8.9, +17.6] | +939 [+610, +1,302] | -363 [-574, -183] P<=0 1.00 | +136 [-143, +405] P<=0 0.17 |
| quiet | vt_v1_m0.02_trigger | -40 | comp | sl1 | 573.16 | 40.36 | +9.9 [+6.7, +13.3] | +1,154 [+757, +1,586] | -149 [-271, -52] P<=0 1.00 | +351 [+115, +598] P<=0 0.00 |
| quiet | vt_v1_m0.02_trigger | -40 | e+25 | 60 | 851.23 | 47.75 | +9.5 [+6.9, +12.2] | +1,983 [+1,391, +2,601] |  |  |
| quiet | vt_v1_m0.02_trigger | -40 | e+25 | s20 | 862.58 | 18.57 | +11.8 [+8.7, +15.2] | +958 [+682, +1,270] | -1,025 [-1,375, -712] P<=0 1.00 | -324 [-655, -29] P<=0 0.98 |
| quiet | vt_v1_m0.02_trigger | -40 | e+25 | s40 | 856.91 | 34.00 | +10.6 [+7.7, +13.6] | +1,571 [+1,107, +2,064] | -412 [-570, -271] P<=0 1.00 | +289 [+36, +532] P<=0 0.01 |
| quiet | vt_v1_m0.02_trigger | -40 | e+25 | s100 | 848.39 | 71.76 | +8.3 [+5.8, +10.9] | +2,615 [+1,813, +3,460] | +632 [+370, +926] P<=0 0.00 | +1,333 [+867, +1,833] P<=0 0.00 |
| quiet | vt_v1_m0.02_trigger | -40 | e+25 | dk0.5 | 811.51 | 38.16 | +10.8 [+8.0, +13.8] | +1,661 [+1,183, +2,165] | -321 [-544, -123] P<=0 1.00 | +379 [+59, +686] P<=0 0.01 |
| quiet | vt_v1_m0.02_trigger | -40 | e+25 | dk1 | 842.72 | 41.96 | +10.4 [+7.8, +13.4] | +1,884 [+1,357, +2,435] | -99 [-224, +33] P<=0 0.94 | +602 [+309, +911] P<=0 0.00 |
| quiet | vt_v1_m0.02_trigger | -40 | e+25 | dk2 | 845.56 | 44.89 | +10.1 [+7.5, +13.0] | +1,976 [+1,420, +2,567] | -6 [-83, +74] P<=0 0.58 | +694 [+410, +991] P<=0 0.00 |
| quiet | vt_v1_m0.02_trigger | -40 | e+25 | rv1_30 | 859.74 | 32.49 | +11.8 [+8.6, +15.2] | +1,633 [+1,152, +2,154] | -350 [-523, -193] P<=0 1.00 | +350 [+99, +599] P<=0 0.01 |
| quiet | vt_v1_m0.02_trigger | -40 | e+25 | rv1_0 | 221.32 | 51.09 | +17.2 [+11.1, +24.4] | +857 [+533, +1,206] | -1,126 [-1,570, -730] P<=0 1.00 | -425 [-856, -48] P<=0 0.99 |
| quiet | vt_v1_m0.02_trigger | -40 | e+25 | rv3_30 | 852.65 | 40.06 | +11.1 [+8.2, +14.2] | +1,889 [+1,361, +2,448] | -94 [-206, +22] P<=0 0.94 | +607 [+326, +893] P<=0 0.00 |
| quiet | vt_v1_m0.02_trigger | -40 | e+25 | rv3_0 | 540.53 | 48.21 | +13.8 [+10.0, +18.0] | +1,722 [+1,244, +2,239] | -260 [-496, -19] P<=0 0.98 | +440 [+130, +761] P<=0 0.00 |
| quiet | vt_v1_m0.02_trigger | -40 | e+25 | dk1_rv1 | 849.81 | 30.11 | +12.2 [+9.0, +15.6] | +1,537 [+1,090, +2,005] | -446 [-653, -250] P<=0 1.00 | +254 [-31, +531] P<=0 0.04 |
| quiet | vt_v1_m0.02_trigger | -40 | e+25 | sl0 | 472.43 | 43.73 | +13.8 [+9.8, +18.0] | +1,369 [+919, +1,833] | -614 [-902, -364] P<=0 1.00 | +87 [-252, +409] P<=0 0.31 |
| quiet | vt_v1_m0.02_trigger | -40 | e+25 | sl1 | 678.15 | 46.41 | +10.6 [+7.5, +13.9] | +1,688 [+1,175, +2,226] | -295 [-497, -131] P<=0 1.00 | +406 [+119, +689] P<=0 0.00 |
| busy | vt_v1_m0.02_trigger | -40 | base | 60 | 5,154.00 | 47.79 | +1.0 [-0.7, +3.0] | +1,081 [-878, +2,999] |  |  |
| busy | vt_v1_m0.02_trigger | -40 | base | s20 | 5,166.00 | 18.39 | +2.1 [+0.3, +4.1] | +859 [+135, +1,597] | -222 [-1,449, +976] P<=0 0.64 | +100 [-1,474, +1,359] P<=0 0.43 |
| busy | vt_v1_m0.02_trigger | -40 | base | s40 | 5,154.00 | 34.08 | +1.4 [-0.3, +3.4] | +1,098 [-250, +2,456] | +18 [-613, +613] P<=0 0.48 | +339 [-1,303, +1,791] P<=0 0.33 |
| busy | vt_v1_m0.02_trigger | -40 | base | s100 | 5,118.00 | 71.48 | +0.3 [-1.5, +2.5] | +423 [-2,573, +3,560] | -658 [-1,841, +626] P<=0 0.85 | -337 [-3,142, +2,298] P<=0 0.60 |
| busy | vt_v1_m0.02_trigger | -40 | base | dk0.5 | 4,980.00 | 38.72 | +0.6 [-1.1, +2.8] | +464 [-995, +2,008] | -617 [-1,513, +191] P<=0 0.93 | -296 [-2,155, +1,315] P<=0 0.63 |
| busy | vt_v1_m0.02_trigger | -40 | base | dk1 | 5,118.00 | 42.63 | +0.8 [-0.7, +2.8] | +773 [-745, +2,312] | -308 [-942, +293] P<=0 0.84 | +14 [-1,835, +1,580] P<=0 0.48 |
| busy | vt_v1_m0.02_trigger | -40 | base | dk2 | 5,142.00 | 45.49 | +0.9 [-0.7, +2.7] | +864 [-787, +2,482] | -217 [-683, +220] P<=0 0.82 | +104 [-1,794, +1,722] P<=0 0.45 |
| busy | vt_v1_m0.02_trigger | -40 | base | rv1_30 | 5,154.00 | 31.02 | +1.9 [-0.1, +4.0] | +1,247 [-39, +2,525] | +166 [-688, +919] P<=0 0.33 | +487 [-1,246, +2,056] P<=0 0.29 |
| busy | vt_v1_m0.02_trigger | -40 | base | rv1_0 | 1,056.00 | 49.41 | +4.9 [+0.2, +9.7] | +850 [+41, +1,712] | -231 [-1,757, +1,182] P<=0 0.61 | +90 [-1,683, +1,708] P<=0 0.45 |
| busy | vt_v1_m0.02_trigger | -40 | base | rv3_30 | 5,154.00 | 38.53 | +1.3 [-0.7, +3.6] | +1,093 [-636, +2,766] | +12 [-456, +397] P<=0 0.47 | +334 [-1,586, +2,047] P<=0 0.36 |
| busy | vt_v1_m0.02_trigger | -40 | base | rv3_0 | 2,856.00 | 48.59 | +1.6 [-1.3, +4.9] | +844 [-681, +2,414] | -236 [-1,206, +598] P<=0 0.68 | +85 [-1,980, +1,961] P<=0 0.46 |
| busy | vt_v1_m0.02_trigger | -40 | base | dk1_rv1 | 5,118.00 | 29.00 | +1.8 [+0.1, +3.8] | +1,089 [+36, +2,125] | +9 [-1,122, +990] P<=0 0.48 | +330 [-1,409, +1,808] P<=0 0.35 |
| busy | vt_v1_m0.02_trigger | -40 | base | sl0 | 3,054.00 | 38.78 | +2.4 [-0.8, +6.7] | +1,097 [-388, +2,804] | +16 [-1,002, +1,011] P<=0 0.49 | +337 [-1,251, +1,832] P<=0 0.35 |
| busy | vt_v1_m0.02_trigger | -40 | base | sl1 | 4,398.00 | 44.33 | +1.1 [-0.8, +3.5] | +911 [-704, +2,638] | -170 [-720, +335] P<=0 0.73 | +151 [-1,605, +1,715] P<=0 0.43 |
| busy | vt_v1_m0.02_trigger | -40 | comp | 60 | 3,828.00 | 44.50 | -1.5 [-3.5, +0.7] | -1,107 [-2,719, +461] |  |  |
| busy | vt_v1_m0.02_trigger | -40 | comp | s20 | 3,864.00 | 17.85 | -0.4 [-2.3, +1.8] | -111 [-715, +474] | +996 [+58, +2,004] P<=0 0.02 | -326 [-1,688, +832] P<=0 0.70 |
| busy | vt_v1_m0.02_trigger | -40 | comp | s40 | 3,846.00 | 32.38 | -1.1 [-3.0, +1.1] | -559 [-1,690, +545] | +548 [+77, +1,052] P<=0 0.01 | -774 [-2,382, +595] P<=0 0.86 |
| busy | vt_v1_m0.02_trigger | -40 | comp | s100 | 3,810.00 | 64.58 | -2.1 [-4.1, +0.3] | -2,154 [-4,640, +253] | -1,047 [-1,950, -211] P<=0 0.99 | -2,369 [-4,926, -122] P<=0 0.98 |
| busy | vt_v1_m0.02_trigger | -40 | comp | dk0.5 | 3,708.00 | 37.47 | -2.3 [-4.2, -0.1] | -1,301 [-2,552, -64] | -194 [-828, +386] P<=0 0.72 | -1,516 [-3,243, -74] P<=0 0.98 |
| busy | vt_v1_m0.02_trigger | -40 | comp | dk1 | 3,816.00 | 40.68 | -1.8 [-3.7, +0.3] | -1,173 [-2,533, +168] | -66 [-547, +372] P<=0 0.59 | -1,388 [-3,148, +54] P<=0 0.97 |
| busy | vt_v1_m0.02_trigger | -40 | comp | dk2 | 3,822.00 | 42.87 | -1.7 [-3.5, +0.3] | -1,196 [-2,644, +211] | -89 [-493, +251] P<=0 0.65 | -1,411 [-3,211, +76] P<=0 0.96 |
| busy | vt_v1_m0.02_trigger | -40 | comp | rv1_30 | 3,852.00 | 29.73 | -0.6 [-3.1, +2.0] | -283 [-1,460, +892] | +824 [+282, +1,394] P<=0 0.00 | -498 [-2,169, +966] P<=0 0.73 |
| busy | vt_v1_m0.02_trigger | -40 | comp | rv1_0 | 798.00 | 47.04 | +2.4 [-4.5, +8.6] | +289 [-498, +1,104] | +1,396 [+280, +2,528] P<=0 0.01 | +74 [-1,500, +1,502] P<=0 0.46 |
| busy | vt_v1_m0.02_trigger | -40 | comp | rv3_30 | 3,840.00 | 36.80 | -1.3 [-3.6, +1.2] | -773 [-2,217, +608] | +334 [+7, +627] P<=0 0.02 | -988 [-2,875, +570] P<=0 0.88 |
| busy | vt_v1_m0.02_trigger | -40 | comp | rv3_0 | 2,160.00 | 46.09 | -1.6 [-4.9, +2.0] | -583 [-1,847, +697] | +524 [-181, +1,147] P<=0 0.07 | -798 [-2,671, +758] P<=0 0.82 |
| busy | vt_v1_m0.02_trigger | -40 | comp | dk1_rv1 | 3,834.00 | 28.13 | -0.8 [-3.2, +1.6] | -374 [-1,391, +660] | +734 [+54, +1,424] P<=0 0.02 | -588 [-2,240, +802] P<=0 0.77 |
| busy | vt_v1_m0.02_trigger | -40 | comp | sl0 | 1,890.00 | 35.92 | +0.3 [-2.9, +4.4] | +82 [-702, +949] | +1,189 [+240, +2,291] P<=0 0.01 | -133 [-1,494, +1,021] P<=0 0.58 |
| busy | vt_v1_m0.02_trigger | -40 | comp | sl1 | 2,940.00 | 41.01 | -1.0 [-3.5, +1.8] | -484 [-1,728, +795] | +623 [+50, +1,304] P<=0 0.02 | -698 [-2,385, +759] P<=0 0.81 |
| busy | vt_v1_m0.02_trigger | -40 | e+25 | 60 | 4,338.00 | 50.14 | -0.3 [-2.0, +1.5] | -325 [-2,014, +1,271] |  |  |
| busy | vt_v1_m0.02_trigger | -40 | e+25 | s20 | 4,356.00 | 18.84 | +0.6 [-1.0, +2.3] | +206 [-385, +757] | +531 [-510, +1,670] P<=0 0.17 | -162 [-1,709, +1,093] P<=0 0.58 |
| busy | vt_v1_m0.02_trigger | -40 | e+25 | s40 | 4,350.00 | 35.40 | +0.1 [-1.6, +1.9] | +52 [-1,116, +1,187] | +377 [-125, +915] P<=0 0.07 | -316 [-2,054, +1,154] P<=0 0.65 |
| busy | vt_v1_m0.02_trigger | -40 | e+25 | s100 | 4,314.00 | 75.62 | -1.0 [-2.6, +0.9] | -1,337 [-3,935, +1,219] | -1,012 [-1,993, -97] P<=0 0.99 | -1,705 [-4,467, +736] P<=0 0.91 |
| busy | vt_v1_m0.02_trigger | -40 | e+25 | dk0.5 | 4,206.00 | 40.74 | -0.9 [-2.5, +0.9] | -654 [-1,933, +581] | -330 [-1,120, +391] P<=0 0.79 | -1,022 [-3,001, +603] P<=0 0.87 |
| busy | vt_v1_m0.02_trigger | -40 | e+25 | dk1 | 4,314.00 | 44.87 | -0.5 [-2.0, +1.2] | -429 [-1,761, +897] | -104 [-683, +426] P<=0 0.63 | -797 [-2,733, +805] P<=0 0.81 |
| busy | vt_v1_m0.02_trigger | -40 | e+25 | dk2 | 4,326.00 | 47.75 | -0.5 [-2.0, +1.2] | -404 [-1,834, +988] | -79 [-552, +334] P<=0 0.62 | -772 [-2,715, +849] P<=0 0.80 |
| busy | vt_v1_m0.02_trigger | -40 | e+25 | rv1_30 | 4,350.00 | 32.19 | +0.6 [-1.4, +2.7] | +325 [-851, +1,482] | +649 [+70, +1,212] P<=0 0.01 | -43 [-1,825, +1,509] P<=0 0.52 |
| busy | vt_v1_m0.02_trigger | -40 | e+25 | rv1_0 | 900.00 | 51.09 | +3.7 [-1.9, +8.9] | +566 [-241, +1,436] | +891 [-256, +2,048] P<=0 0.06 | +198 [-1,532, +1,776] P<=0 0.41 |
| busy | vt_v1_m0.02_trigger | -40 | e+25 | rv3_30 | 4,344.00 | 40.27 | -0.1 [-2.0, +2.0] | -51 [-1,516, +1,378] | +273 [-121, +625] P<=0 0.08 | -419 [-2,407, +1,296] P<=0 0.67 |
| busy | vt_v1_m0.02_trigger | -40 | e+25 | rv3_0 | 2,394.00 | 51.21 | +0.1 [-3.0, +3.4] | +25 [-1,392, +1,496] | +350 [-521, +1,071] P<=0 0.18 | -343 [-2,421, +1,567] P<=0 0.63 |
| busy | vt_v1_m0.02_trigger | -40 | e+25 | dk1_rv1 | 4,326.00 | 30.22 | +0.5 [-1.3, +2.5] | +258 [-748, +1,263] | +583 [-193, +1,351] P<=0 0.07 | -110 [-1,896, +1,398] P<=0 0.54 |
| busy | vt_v1_m0.02_trigger | -40 | e+25 | sl0 | 2,142.00 | 43.62 | +1.3 [-1.7, +5.0] | +465 [-632, +1,626] | +790 [-194, +1,788] P<=0 0.07 | +97 [-1,552, +1,526] P<=0 0.46 |
| busy | vt_v1_m0.02_trigger | -40 | e+25 | sl1 | 3,372.00 | 48.28 | -0.2 [-2.1, +2.0] | -135 [-1,488, +1,235] | +190 [-565, +1,029] P<=0 0.33 | -503 [-2,470, +1,178] P<=0 0.70 |
| unseen | vt_v1_m0.02_trigger | -40 | base | 60 | 1,954.04 | 45.59 | +5.8 [+4.0, +7.9] | +2,406 [+1,755, +3,097] |  |  |
| unseen | vt_v1_m0.02_trigger | -40 | base | s20 | 1,965.51 | 18.08 | +7.5 [+5.5, +9.8] | +1,220 [+930, +1,527] | -1,186 [-1,571, -796] P<=0 1.00 | -310 [-722, +80] P<=0 0.95 |
| unseen | vt_v1_m0.02_trigger | -40 | base | s40 | 1,957.48 | 32.90 | +6.5 [+4.6, +8.7] | +1,939 [+1,453, +2,454] | -467 [-648, -272] P<=0 1.00 | +409 [+10, +771] P<=0 0.02 |
| unseen | vt_v1_m0.02_trigger | -40 | base | s100 | 1,943.71 | 67.44 | +4.9 [+3.2, +6.9] | +3,003 [+2,090, +4,024] | +597 [+240, +941] P<=0 0.00 | +1,472 [+760, +2,125] P<=0 0.00 |
| unseen | vt_v1_m0.02_trigger | -40 | base | dk0.5 | 1,878.31 | 36.93 | +6.2 [+4.2, +8.6] | +1,938 [+1,409, +2,527] | -468 [-724, -226] P<=0 1.00 | +407 [-88, +801] P<=0 0.04 |
| unseen | vt_v1_m0.02_trigger | -40 | base | dk1 | 1,940.27 | 40.53 | +6.1 [+4.3, +8.3] | +2,222 [+1,657, +2,842] | -184 [-354, -20] P<=0 0.99 | +691 [+215, +1,090] P<=0 0.00 |
| unseen | vt_v1_m0.02_trigger | -40 | base | dk2 | 1,948.30 | 43.21 | +5.9 [+4.2, +8.1] | +2,333 [+1,732, +2,989] | -74 [-196, +36] P<=0 0.92 | +802 [+332, +1,204] P<=0 0.00 |
| unseen | vt_v1_m0.02_trigger | -40 | base | rv1_30 | 1,962.07 | 30.53 | +7.5 [+5.5, +9.9] | +2,038 [+1,531, +2,551] | -369 [-603, -142] P<=0 1.00 | +507 [+110, +873] P<=0 0.01 |
| unseen | vt_v1_m0.02_trigger | -40 | base | rv1_0 | 453.23 | 47.24 | +13.1 [+9.3, +17.5] | +1,078 [+759, +1,433] | -1,328 [-1,852, -834] P<=0 1.00 | -453 [-949, +1] P<=0 0.97 |
| unseen | vt_v1_m0.02_trigger | -40 | base | rv3_30 | 1,956.33 | 37.53 | +6.9 [+5.0, +9.3] | +2,301 [+1,714, +2,895] | -105 [-243, +33] P<=0 0.93 | +770 [+304, +1,178] P<=0 0.00 |
| unseen | vt_v1_m0.02_trigger | -40 | base | rv3_0 | 1,148.56 | 46.10 | +8.9 [+6.4, +12.0] | +1,997 [+1,472, +2,535] | -409 [-708, -112] P<=0 1.00 | +467 [-23, +931] P<=0 0.03 |
| unseen | vt_v1_m0.02_trigger | -40 | base | dk1_rv1 | 1,946.01 | 28.47 | +7.6 [+5.6, +10.1] | +1,898 [+1,436, +2,380] | -508 [-793, -234] P<=0 1.00 | +367 [-50, +748] P<=0 0.04 |
| unseen | vt_v1_m0.02_trigger | -40 | base | sl0 | 1,228.88 | 37.00 | +8.9 [+6.2, +12.1] | +1,741 [+1,243, +2,254] | -666 [-1,002, -349] P<=0 1.00 | +210 [-216, +598] P<=0 0.16 |
| unseen | vt_v1_m0.02_trigger | -40 | base | sl1 | 1,670.63 | 42.41 | +6.4 [+4.5, +8.9] | +2,107 [+1,526, +2,709] | -299 [-492, -125] P<=0 1.00 | +577 [+158, +956] P<=0 0.00 |
| unseen | vt_v1_m0.02_trigger | -40 | comp | 60 | 1,324.11 | 43.72 | +3.1 [+1.3, +5.3] | +841 [+367, +1,314] |  |  |
| unseen | vt_v1_m0.02_trigger | -40 | comp | s20 | 1,339.03 | 17.68 | +4.7 [+2.7, +7.3] | +522 [+304, +735] | -319 [-625, -17] P<=0 0.98 | -168 [-517, +136] P<=0 0.86 |
| unseen | vt_v1_m0.02_trigger | -40 | comp | s40 | 1,331.00 | 31.86 | +3.6 [+1.7, +5.8] | +711 [+367, +1,053] | -131 [-284, +18] P<=0 0.95 | +21 [-343, +350] P<=0 0.45 |
| unseen | vt_v1_m0.02_trigger | -40 | comp | s100 | 1,317.23 | 62.94 | +2.5 [+0.7, +4.7] | +977 [+294, +1,669] | +135 [-107, +384] P<=0 0.15 | +287 [-352, +840] P<=0 0.19 |
| unseen | vt_v1_m0.02_trigger | -40 | comp | dk0.5 | 1,270.18 | 36.67 | +3.5 [+1.5, +6.0] | +725 [+322, +1,128] | -116 [-285, +42] P<=0 0.92 | +35 [-393, +395] P<=0 0.44 |
| unseen | vt_v1_m0.02_trigger | -40 | comp | dk1 | 1,314.93 | 39.72 | +3.5 [+1.6, +5.8] | +834 [+414, +1,273] | -7 [-123, +102] P<=0 0.54 | +144 [-275, +509] P<=0 0.25 |
| unseen | vt_v1_m0.02_trigger | -40 | comp | dk2 | 1,319.52 | 41.84 | +3.2 [+1.4, +5.4] | +829 [+385, +1,278] | -12 [-106, +72] P<=0 0.60 | +139 [-286, +514] P<=0 0.26 |
| unseen | vt_v1_m0.02_trigger | -40 | comp | rv1_30 | 1,332.14 | 29.85 | +4.5 [+2.4, +7.0] | +816 [+464, +1,194] | -26 [-183, +140] P<=0 0.63 | +125 [-259, +472] P<=0 0.27 |
| unseen | vt_v1_m0.02_trigger | -40 | comp | rv1_0 | 309.80 | 47.13 | +9.6 [+5.1, +14.6] | +547 [+279, +832] | -294 [-653, +71] P<=0 0.95 | -143 [-538, +234] P<=0 0.78 |
| unseen | vt_v1_m0.02_trigger | -40 | comp | rv3_30 | 1,327.55 | 36.45 | +4.0 [+1.9, +6.4] | +870 [+446, +1,310] | +28 [-68, +124] P<=0 0.28 | +180 [-246, +565] P<=0 0.21 |
| unseen | vt_v1_m0.02_trigger | -40 | comp | rv3_0 | 785.98 | 44.60 | +5.5 [+2.7, +8.8] | +812 [+432, +1,225] | -30 [-237, +183] P<=0 0.62 | +121 [-307, +531] P<=0 0.29 |
| unseen | vt_v1_m0.02_trigger | -40 | comp | dk1_rv1 | 1,321.82 | 28.14 | +4.7 [+2.6, +7.3] | +791 [+452, +1,144] | -50 [-240, +148] P<=0 0.71 | +101 [-277, +449] P<=0 0.30 |
| unseen | vt_v1_m0.02_trigger | -40 | comp | sl0 | 699.92 | 35.58 | +7.5 [+4.4, +11.3] | +775 [+463, +1,094] | -66 [-319, +203] P<=0 0.69 | +85 [-251, +403] P<=0 0.31 |
| unseen | vt_v1_m0.02_trigger | -40 | comp | sl1 | 1,025.78 | 40.71 | +4.5 [+2.2, +7.2] | +840 [+441, +1,242] | -1 [-151, +160] P<=0 0.52 | +150 [-248, +493] P<=0 0.22 |
| unseen | vt_v1_m0.02_trigger | -40 | e+25 | 60 | 1,518.02 | 49.06 | +4.4 [+2.6, +6.6] | +1,541 [+977, +2,112] |  |  |
| unseen | vt_v1_m0.02_trigger | -40 | e+25 | s20 | 1,530.65 | 18.72 | +6.1 [+4.0, +8.6] | +814 [+573, +1,076] | -727 [-1,082, -380] P<=0 1.00 | -293 [-690, +53] P<=0 0.95 |
| unseen | vt_v1_m0.02_trigger | -40 | e+25 | s40 | 1,524.91 | 34.76 | +5.2 [+3.3, +7.5] | +1,281 [+859, +1,723] | -261 [-424, -97] P<=0 1.00 | +173 [-232, +521] P<=0 0.19 |
| unseen | vt_v1_m0.02_trigger | -40 | e+25 | s100 | 1,511.14 | 73.87 | +3.5 [+1.8, +5.6] | +1,859 [+1,035, +2,676] | +318 [+2, +627] P<=0 0.02 | +752 [+57, +1,366] P<=0 0.02 |
| unseen | vt_v1_m0.02_trigger | -40 | e+25 | dk0.5 | 1,460.65 | 39.58 | +4.7 [+2.7, +7.1] | +1,219 [+764, +1,705] | -323 [-547, -110] P<=0 1.00 | +111 [-370, +514] P<=0 0.30 |
| unseen | vt_v1_m0.02_trigger | -40 | e+25 | dk1 | 1,506.55 | 43.56 | +4.8 [+2.9, +7.0] | +1,442 [+940, +1,959] | -100 [-247, +46] P<=0 0.91 | +334 [-129, +731] P<=0 0.08 |
| unseen | vt_v1_m0.02_trigger | -40 | e+25 | dk2 | 1,511.14 | 46.46 | +4.7 [+2.8, +6.8] | +1,521 [+994, +2,065] | -20 [-129, +85] P<=0 0.65 | +414 [-44, +803] P<=0 0.04 |
| unseen | vt_v1_m0.02_trigger | -40 | e+25 | rv1_30 | 1,527.20 | 32.32 | +6.2 [+4.1, +8.7] | +1,382 [+939, +1,831] | -159 [-346, +27] P<=0 0.96 | +275 [-140, +627] P<=0 0.10 |
| unseen | vt_v1_m0.02_trigger | -40 | e+25 | rv1_0 | 351.11 | 51.09 | +11.5 [+7.4, +16.3] | +801 [+498, +1,123] | -740 [-1,190, -313] P<=0 1.00 | -306 [-774, +117] P<=0 0.92 |
| unseen | vt_v1_m0.02_trigger | -40 | e+25 | rv3_30 | 1,520.32 | 40.17 | +5.5 [+3.5, +7.9] | +1,518 [+1,008, +2,047] | -24 [-136, +94] P<=0 0.67 | +410 [-57, +802] P<=0 0.04 |
| unseen | vt_v1_m0.02_trigger | -40 | e+25 | rv3_0 | 894.98 | 49.74 | +7.3 [+4.7, +10.5] | +1,398 [+921, +1,911] | -144 [-390, +106] P<=0 0.88 | +291 [-194, +740] P<=0 0.12 |
| unseen | vt_v1_m0.02_trigger | -40 | e+25 | dk1_rv1 | 1,514.58 | 30.17 | +6.3 [+4.2, +8.9] | +1,292 [+893, +1,715] | -249 [-480, -11] P<=0 0.98 | +185 [-234, +561] P<=0 0.18 |
| unseen | vt_v1_m0.02_trigger | -40 | e+25 | sl0 | 791.71 | 43.67 | +8.2 [+5.2, +11.6] | +1,196 [+792, +1,617] | -345 [-639, -60] P<=0 0.99 | +89 [-320, +479] P<=0 0.34 |
| unseen | vt_v1_m0.02_trigger | -40 | e+25 | sl1 | 1,193.31 | 47.42 | +5.2 [+3.1, +7.7] | +1,339 [+844, +1,843] | -202 [-416, +6] P<=0 0.97 | +232 [-219, +627] P<=0 0.14 |

## Size rules: micf, L = 0
| group | arm | L | fill model | size | fills/day | sh/fill | mk10 c/$ | mk10 $/day | vs 60 sh $/day | gain vs micf $/day |
|---|---|---|---|---|---|---|---|---|---|---|
| select | micf | 0 | base | 60 | 714.00 | 50.79 | +3.5 [+0.3, +7.0] | +816 [+77, +1,634] |  |  |
| select | micf | 0 | base | s20 | 722.00 | 18.54 | +4.3 [+1.2, +7.8] | +369 [+102, +661] | -448 [-1,026, +43] P<=0 0.96 | -448 [-1,026, +43] P<=0 0.96 |
| select | micf | 0 | base | s40 | 716.00 | 35.45 | +3.8 [+0.7, +7.3] | +628 [+120, +1,198] | -188 [-477, +54] P<=0 0.93 | -188 [-477, +54] P<=0 0.93 |
| select | micf | 0 | base | s100 | 704.00 | 79.08 | +2.7 [-0.5, +6.1] | +963 [-178, +2,190] | +147 [-297, +634] P<=0 0.26 | +147 [-297, +634] P<=0 0.26 |
| select | micf | 0 | base | dk0.5 | 670.00 | 39.47 | +6.3 [+2.7, +10.4] | +1,095 [+460, +1,819] | +279 [-48, +600] P<=0 0.04 | +279 [-48, +600] P<=0 0.04 |
| select | micf | 0 | base | dk1 | 708.00 | 42.68 | +5.1 [+1.7, +8.8] | +1,009 [+315, +1,770] | +193 [-33, +413] P<=0 0.05 | +193 [-33, +413] P<=0 0.05 |
| select | micf | 0 | base | dk2 | 712.00 | 46.34 | +4.4 [+1.0, +8.0] | +937 [+209, +1,727] | +120 [-17, +249] P<=0 0.05 | +120 [-17, +249] P<=0 0.05 |
| select | micf | 0 | base | rv1_30 | 718.00 | 30.13 | +5.6 [+2.0, +9.7] | +774 [+279, +1,333] | -43 [-387, +277] P<=0 0.60 | -43 [-387, +277] P<=0 0.60 |
| select | micf | 0 | base | rv1_0 | 92.00 | 49.83 | +22.1 [+10.0, +39.7] | +605 [+268, +1,054] | -211 [-940, +453] P<=0 0.72 | -211 [-940, +453] P<=0 0.72 |
| select | micf | 0 | base | rv3_30 | 716.00 | 34.58 | +6.0 [+2.4, +10.1] | +962 [+387, +1,624] | +146 [-149, +440] P<=0 0.17 | +146 [-149, +440] P<=0 0.17 |
| select | micf | 0 | base | rv3_0 | 230.00 | 49.85 | +14.3 [+7.6, +23.2] | +1,031 [+547, +1,658] | +214 [-401, +813] P<=0 0.26 | +214 [-401, +813] P<=0 0.26 |
| select | micf | 0 | base | dk1_rv1 | 712.00 | 27.35 | +6.5 [+2.7, +10.9] | +814 [+331, +1,374] | -2 [-391, +363] P<=0 0.50 | -2 [-391, +363] P<=0 0.50 |
| select | micf | 0 | base | sl0 | 472.00 | 50.18 | +5.5 [+1.3, +10.4] | +807 [+193, +1,521] | -9 [-409, +343] P<=0 0.54 | -9 [-409, +343] P<=0 0.54 |
| select | micf | 0 | base | sl1 | 596.00 | 49.11 | +5.1 [+1.5, +9.2] | +935 [+272, +1,692] | +119 [-156, +406] P<=0 0.21 | +119 [-156, +406] P<=0 0.21 |
| select | micf | 0 | comp | 60 | 592.00 | 48.16 | +1.2 [-2.2, +4.8] | +223 [-395, +883] |  |  |
| select | micf | 0 | comp | s20 | 608.00 | 18.30 | +2.4 [-1.2, +6.1] | +171 [-86, +443] | -51 [-493, +349] P<=0 0.58 | -51 [-493, +349] P<=0 0.58 |
| select | micf | 0 | comp | s40 | 600.00 | 34.04 | +1.5 [-2.0, +5.1] | +201 [-253, +674] | -22 [-229, +169] P<=0 0.58 | -22 [-229, +169] P<=0 0.58 |
| select | micf | 0 | comp | s100 | 586.00 | 71.93 | +0.6 [-2.6, +4.1] | +166 [-725, +1,141] | -56 [-376, +280] P<=0 0.64 | -56 [-376, +280] P<=0 0.64 |
| select | micf | 0 | comp | dk0.5 | 562.00 | 37.81 | +3.4 [-0.2, +7.4] | +483 [-29, +1,047] | +260 [-25, +521] P<=0 0.04 | +260 [-25, +521] P<=0 0.04 |
| select | micf | 0 | comp | dk1 | 594.00 | 40.80 | +2.5 [-1.0, +6.2] | +397 [-160, +1,001] | +175 [-37, +356] P<=0 0.05 | +175 [-37, +356] P<=0 0.05 |
| select | micf | 0 | comp | dk2 | 592.00 | 44.44 | +1.8 [-1.6, +5.5] | +317 [-278, +959] | +94 [-33, +213] P<=0 0.07 | +94 [-33, +213] P<=0 0.07 |
| select | micf | 0 | comp | rv1_30 | 606.00 | 28.49 | +2.4 [-1.2, +6.4] | +272 [-129, +708] | +49 [-230, +323] P<=0 0.36 | +49 [-230, +323] P<=0 0.36 |
| select | micf | 0 | comp | rv1_0 | 72.00 | 42.85 | +13.9 [+4.2, +28.8] | +276 [+75, +540] | +53 [-570, +643] P<=0 0.43 | +53 [-570, +643] P<=0 0.43 |
| select | micf | 0 | comp | rv3_30 | 606.00 | 32.10 | +3.0 [-0.7, +7.1] | +384 [-84, +903] | +162 [-84, +395] P<=0 0.10 | +162 [-84, +395] P<=0 0.10 |
| select | micf | 0 | comp | rv3_0 | 186.00 | 44.97 | +10.4 [+4.2, +18.9] | +573 [+222, +1,056] | +350 [-212, +879] P<=0 0.10 | +350 [-212, +879] P<=0 0.10 |
| select | micf | 0 | comp | dk1_rv1 | 600.00 | 26.27 | +3.2 [-0.5, +7.4] | +335 [-49, +766] | +112 [-214, +424] P<=0 0.24 | +112 [-214, +424] P<=0 0.24 |
| select | micf | 0 | comp | sl0 | 396.00 | 45.92 | +2.5 [-2.3, +7.7] | +282 [-251, +870] | +60 [-255, +356] P<=0 0.34 | +60 [-255, +356] P<=0 0.34 |
| select | micf | 0 | comp | sl1 | 496.00 | 46.41 | +2.2 [-1.5, +6.4] | +329 [-232, +929] | +106 [-152, +374] P<=0 0.22 | +106 [-152, +374] P<=0 0.22 |
| select | micf | 0 | e+25 | 60 | 644.00 | 52.04 | +2.4 [-0.8, +5.9] | +530 [-184, +1,286] |  |  |
| select | micf | 0 | e+25 | s20 | 650.00 | 18.75 | +3.4 [+0.1, +6.8] | +265 [+7, +540] | -265 [-816, +192] P<=0 0.85 | -265 [-816, +192] P<=0 0.85 |
| select | micf | 0 | e+25 | s40 | 646.00 | 36.13 | +3.0 [-0.3, +6.5] | +453 [-44, +984] | -77 [-331, +144] P<=0 0.74 | -77 [-331, +144] P<=0 0.74 |
| select | micf | 0 | e+25 | s100 | 636.00 | 81.78 | +1.6 [-1.6, +5.1] | +550 [-545, +1,706] | +20 [-400, +490] P<=0 0.48 | +20 [-400, +490] P<=0 0.48 |
| select | micf | 0 | e+25 | dk0.5 | 606.00 | 39.76 | +5.3 [+1.7, +9.3] | +846 [+261, +1,498] | +316 [-17, +652] P<=0 0.03 | +316 [-17, +652] P<=0 0.03 |
| select | micf | 0 | e+25 | dk1 | 640.00 | 43.20 | +4.2 [+0.6, +7.8] | +758 [+111, +1,458] | +228 [-5, +456] P<=0 0.03 | +228 [-5, +456] P<=0 0.03 |
| select | micf | 0 | e+25 | dk2 | 642.00 | 47.27 | +3.4 [-0.1, +7.0] | +673 [-13, +1,404] | +143 [+5, +280] P<=0 0.02 | +143 [+5, +280] P<=0 0.02 |
| select | micf | 0 | e+25 | rv1_30 | 648.00 | 30.37 | +4.4 [+0.8, +8.3] | +558 [+100, +1,053] | +28 [-307, +345] P<=0 0.43 | +28 [-307, +345] P<=0 0.43 |
| select | micf | 0 | e+25 | rv1_0 | 76.00 | 51.42 | +19.9 [+8.2, +37.7] | +470 [+181, +852] | -60 [-766, +578] P<=0 0.57 | -60 [-766, +578] P<=0 0.57 |
| select | micf | 0 | e+25 | rv3_30 | 646.00 | 34.89 | +4.9 [+1.4, +8.9] | +716 [+188, +1,320] | +186 [-111, +474] P<=0 0.10 | +186 [-111, +474] P<=0 0.10 |
| select | micf | 0 | e+25 | rv3_0 | 206.00 | 49.73 | +12.4 [+6.0, +21.2] | +813 [+378, +1,396] | +283 [-323, +872] P<=0 0.18 | +283 [-323, +872] P<=0 0.18 |
| select | micf | 0 | e+25 | dk1_rv1 | 644.00 | 27.57 | +5.3 [+1.4, +9.7] | +608 [+156, +1,122] | +78 [-307, +439] P<=0 0.34 | +78 [-307, +439] P<=0 0.34 |
| select | micf | 0 | e+25 | sl0 | 442.00 | 51.26 | +4.2 [+0.0, +9.1] | +598 [+0, +1,235] | +68 [-291, +416] P<=0 0.35 | +68 [-291, +416] P<=0 0.35 |
| select | micf | 0 | e+25 | sl1 | 540.00 | 50.78 | +3.9 [+0.3, +7.9] | +679 [+48, +1,353] | +149 [-112, +451] P<=0 0.15 | +149 [-112, +451] P<=0 0.15 |
| quiet | micf | 0 | base | 60 | 415.68 | 50.84 | +7.9 [+4.7, +11.3] | +1,148 [+675, +1,638] |  |  |
| quiet | micf | 0 | base | s20 | 428.45 | 19.18 | +10.8 [+6.7, +15.3] | +591 [+354, +855] | -557 [-848, -301] P<=0 1.00 | -557 [-848, -301] P<=0 1.00 |
| quiet | micf | 0 | base | s40 | 422.78 | 35.61 | +9.2 [+5.6, +13.0] | +935 [+548, +1,333] | -213 [-345, -101] P<=0 1.00 | -213 [-345, -101] P<=0 1.00 |
| quiet | micf | 0 | base | s100 | 412.85 | 77.40 | +6.7 [+3.7, +10.0] | +1,495 [+809, +2,217] | +347 [+121, +599] P<=0 0.00 | +347 [+121, +599] P<=0 0.00 |
| quiet | micf | 0 | base | dk0.5 | 381.64 | 36.90 | +10.6 [+6.8, +14.5] | +1,036 [+626, +1,462] | -112 [-314, +79] P<=0 0.88 | -112 [-314, +79] P<=0 0.88 |
| quiet | micf | 0 | base | dk1 | 402.92 | 41.62 | +9.6 [+6.2, +13.2] | +1,125 [+689, +1,578] | -23 [-171, +124] P<=0 0.63 | -23 [-171, +124] P<=0 0.63 |
| quiet | micf | 0 | base | dk2 | 408.59 | 45.29 | +9.1 [+5.7, +12.8] | +1,169 [+711, +1,646] | +21 [-84, +136] P<=0 0.36 | +21 [-84, +136] P<=0 0.36 |
| quiet | micf | 0 | base | rv1_30 | 425.62 | 31.89 | +11.0 [+6.9, +15.4] | +981 [+579, +1,407] | -167 [-306, -39] P<=0 0.99 | -167 [-306, -39] P<=0 0.99 |
| quiet | micf | 0 | base | rv1_0 | 85.12 | 49.88 | +22.9 [+12.6, +36.0] | +536 [+277, +823] | -612 [-988, -287] P<=0 1.00 | -612 [-988, -287] P<=0 1.00 |
| quiet | micf | 0 | base | rv3_30 | 417.10 | 37.32 | +10.8 [+6.9, +15.0] | +1,116 [+678, +1,595] | -33 [-137, +73] P<=0 0.72 | -33 [-137, +73] P<=0 0.72 |
| quiet | micf | 0 | base | rv3_0 | 183.01 | 49.78 | +18.5 [+11.7, +26.3] | +1,021 [+610, +1,470] | -127 [-341, +93] P<=0 0.87 | -127 [-341, +93] P<=0 0.87 |
| quiet | micf | 0 | base | dk1_rv1 | 410.01 | 28.33 | +11.9 [+7.7, +16.5] | +928 [+558, +1,319] | -220 [-420, -34] P<=0 0.99 | -220 [-420, -34] P<=0 0.99 |
| quiet | micf | 0 | base | sl0 | 251.11 | 44.82 | +12.1 [+7.2, +17.1] | +876 [+491, +1,291] | -273 [-505, -79] P<=0 1.00 | -273 [-505, -79] P<=0 1.00 |
| quiet | micf | 0 | base | sl1 | 326.31 | 48.67 | +9.9 [+6.1, +14.1] | +1,044 [+606, +1,510] | -104 [-234, +2] P<=0 0.97 | -104 [-234, +2] P<=0 0.97 |
| quiet | micf | 0 | comp | 60 | 350.42 | 45.06 | +5.9 [+2.5, +9.6] | +645 [+268, +1,048] |  |  |
| quiet | micf | 0 | comp | s20 | 360.35 | 17.76 | +8.1 [+4.1, +12.4] | +352 [+176, +542] | -293 [-543, -69] P<=0 1.00 | -293 [-543, -69] P<=0 1.00 |
| quiet | micf | 0 | comp | s40 | 351.84 | 32.56 | +6.4 [+3.0, +10.2] | +510 [+240, +796] | -135 [-259, -24] P<=0 0.99 | -135 [-259, -24] P<=0 0.99 |
| quiet | micf | 0 | comp | s100 | 347.59 | 65.27 | +4.6 [+1.3, +8.2] | +742 [+201, +1,291] | +97 [-69, +265] P<=0 0.13 | +97 [-69, +265] P<=0 0.13 |
| quiet | micf | 0 | comp | dk0.5 | 322.05 | 34.73 | +9.0 [+4.8, +13.6] | +713 [+376, +1,075] | +68 [-64, +206] P<=0 0.17 | +68 [-64, +206] P<=0 0.17 |
| quiet | micf | 0 | comp | dk1 | 337.66 | 38.39 | +8.1 [+4.3, +12.1] | +740 [+386, +1,123] | +96 [-6, +222] P<=0 0.04 | +96 [-6, +222] P<=0 0.04 |
| quiet | micf | 0 | comp | dk2 | 346.17 | 40.64 | +7.2 [+3.6, +11.1] | +710 [+352, +1,092] | +66 [-21, +177] P<=0 0.08 | +66 [-21, +177] P<=0 0.08 |
| quiet | micf | 0 | comp | rv1_30 | 353.26 | 29.11 | +8.5 [+4.4, +13.2] | +584 [+284, +896] | -61 [-184, +61] P<=0 0.84 | -61 [-184, +61] P<=0 0.84 |
| quiet | micf | 0 | comp | rv1_0 | 70.94 | 43.43 | +23.3 [+10.7, +39.4] | +382 [+162, +636] | -263 [-550, +3] P<=0 0.97 | -263 [-550, +3] P<=0 0.97 |
| quiet | micf | 0 | comp | rv3_30 | 350.42 | 33.65 | +8.7 [+4.6, +13.2] | +688 [+353, +1,050] | +43 [-51, +150] P<=0 0.20 | +43 [-51, +150] P<=0 0.20 |
| quiet | micf | 0 | comp | rv3_0 | 150.38 | 44.09 | +16.8 [+9.3, +25.0] | +682 [+354, +1,031] | +37 [-159, +254] P<=0 0.36 | +37 [-159, +254] P<=0 0.36 |
| quiet | micf | 0 | comp | dk1_rv1 | 340.49 | 26.48 | +10.1 [+5.6, +14.8] | +617 [+327, +932] | -28 [-178, +136] P<=0 0.64 | -28 [-178, +136] P<=0 0.64 |
| quiet | micf | 0 | comp | sl0 | 212.81 | 36.30 | +10.0 [+4.4, +16.1] | +511 [+216, +819] | -134 [-306, +14] P<=0 0.96 | -134 [-306, +14] P<=0 0.96 |
| quiet | micf | 0 | comp | sl1 | 282.33 | 41.49 | +8.0 [+3.8, +12.6] | +634 [+288, +994] | -11 [-91, +66] P<=0 0.63 | -11 [-91, +66] P<=0 0.63 |
| quiet | micf | 0 | e+25 | 60 | 380.22 | 50.40 | +7.0 [+3.7, +10.7] | +919 [+475, +1,400] |  |  |
| quiet | micf | 0 | e+25 | s20 | 392.99 | 18.82 | +9.6 [+5.3, +14.5] | +474 [+254, +728] | -444 [-713, -204] P<=0 1.00 | -444 [-713, -204] P<=0 1.00 |
| quiet | micf | 0 | e+25 | s40 | 387.31 | 34.99 | +8.0 [+4.3, +12.0] | +734 [+382, +1,105] | -185 [-312, -70] P<=0 1.00 | -185 [-312, -70] P<=0 1.00 |
| quiet | micf | 0 | e+25 | s100 | 378.80 | 77.29 | +6.2 [+3.0, +9.7] | +1,251 [+604, +1,951] | +333 [+107, +583] P<=0 0.00 | +333 [+107, +583] P<=0 0.00 |
| quiet | micf | 0 | e+25 | dk0.5 | 347.59 | 36.78 | +9.6 [+5.5, +14.0] | +863 [+477, +1,262] | -55 [-238, +119] P<=0 0.75 | -55 [-238, +119] P<=0 0.75 |
| quiet | micf | 0 | e+25 | dk1 | 368.87 | 41.25 | +8.7 [+5.0, +12.6] | +925 [+515, +1,363] | +7 [-134, +148] P<=0 0.46 | +7 [-134, +148] P<=0 0.46 |
| quiet | micf | 0 | e+25 | dk2 | 374.54 | 44.76 | +8.2 [+4.7, +12.0] | +953 [+519, +1,410] | +34 [-69, +153] P<=0 0.26 | +34 [-69, +153] P<=0 0.26 |
| quiet | micf | 0 | e+25 | rv1_30 | 388.73 | 31.35 | +9.9 [+5.5, +14.7] | +795 [+419, +1,188] | -123 [-255, +3] P<=0 0.97 | -123 [-255, +3] P<=0 0.97 |
| quiet | micf | 0 | e+25 | rv1_0 | 73.77 | 50.07 | +22.5 [+11.3, +36.7] | +445 [+205, +709] | -474 [-840, -154] P<=0 1.00 | -474 [-840, -154] P<=0 1.00 |
| quiet | micf | 0 | e+25 | rv3_30 | 381.64 | 36.66 | +9.9 [+5.7, +14.4] | +914 [+498, +1,357] | -4 [-105, +100] P<=0 0.53 | -4 [-105, +100] P<=0 0.53 |
| quiet | micf | 0 | e+25 | rv3_0 | 161.73 | 49.66 | +17.9 [+10.4, +26.4] | +868 [+473, +1,294] | -51 [-264, +164] P<=0 0.67 | -51 [-264, +164] P<=0 0.67 |
| quiet | micf | 0 | e+25 | dk1_rv1 | 375.96 | 27.69 | +11.1 [+6.4, +16.0] | +770 [+424, +1,143] | -148 [-336, +35] P<=0 0.95 | -148 [-336, +35] P<=0 0.95 |
| quiet | micf | 0 | e+25 | sl0 | 239.76 | 44.11 | +11.6 [+6.3, +17.3] | +782 [+402, +1,187] | -137 [-329, +29] P<=0 0.94 | -137 [-329, +29] P<=0 0.94 |
| quiet | micf | 0 | e+25 | sl1 | 306.44 | 47.17 | +9.2 [+5.3, +13.5] | +881 [+480, +1,319] | -38 [-136, +46] P<=0 0.80 | -38 [-136, +46] P<=0 0.80 |
| busy | micf | 0 | base | 60 | 936.00 | 52.62 | +1.3 [-3.5, +6.1] | +375 [-908, +1,983] |  |  |
| busy | micf | 0 | base | s20 | 942.00 | 18.90 | +1.5 [-2.9, +6.0] | +164 [-283, +713] | -211 [-1,224, +620] P<=0 0.68 | -211 [-1,224, +620] P<=0 0.68 |
| busy | micf | 0 | base | s40 | 942.00 | 36.05 | +1.5 [-3.1, +6.3] | +311 [-579, +1,439] | -64 [-543, +329] P<=0 0.62 | -64 [-543, +329] P<=0 0.62 |
| busy | micf | 0 | base | s100 | 936.00 | 81.86 | +0.8 [-4.0, +5.7] | +360 [-1,660, +2,731] | -15 [-723, +784] P<=0 0.52 | -15 [-723, +784] P<=0 0.52 |
| busy | micf | 0 | base | dk0.5 | 840.00 | 36.97 | -1.8 [-6.7, +3.2] | -321 [-1,124, +607] | -696 [-1,523, -32] P<=0 0.98 | -696 [-1,523, -32] P<=0 0.98 |
| busy | micf | 0 | base | dk1 | 912.00 | 42.15 | -0.9 [-6.0, +4.0] | -202 [-1,228, +945] | -578 [-1,234, -72] P<=0 0.99 | -578 [-1,234, -72] P<=0 0.99 |
| busy | micf | 0 | base | dk2 | 936.00 | 45.80 | +0.1 [-5.0, +5.0] | +38 [-1,126, +1,422] | -337 [-820, +9] P<=0 0.97 | -337 [-820, +9] P<=0 0.97 |
| busy | micf | 0 | base | rv1_30 | 942.00 | 29.36 | +2.0 [-2.6, +6.6] | +329 [-387, +1,224] | -46 [-761, +527] P<=0 0.54 | -46 [-761, +527] P<=0 0.54 |
| busy | micf | 0 | base | rv1_0 | 60.00 | 56.50 | +10.7 [-8.1, +28.2] | +173 [-72, +490] | -203 [-1,695, +977] P<=0 0.61 | -203 [-1,695, +977] P<=0 0.61 |
| busy | micf | 0 | base | rv3_30 | 942.00 | 32.38 | +3.0 [-2.1, +8.2] | +555 [-371, +1,755] | +180 [-309, +626] P<=0 0.22 | +180 [-309, +626] P<=0 0.22 |
| busy | micf | 0 | base | rv3_0 | 198.00 | 49.10 | +10.9 [-0.3, +20.0] | +641 [-11, +1,470] | +266 [-761, +1,163] P<=0 0.29 | +266 [-761, +1,163] P<=0 0.29 |
| busy | micf | 0 | base | dk1_rv1 | 912.00 | 25.92 | +0.9 [-4.2, +5.6] | +120 [-536, +865] | -255 [-1,168, +453] P<=0 0.74 | -255 [-1,168, +453] P<=0 0.74 |
| busy | micf | 0 | base | sl0 | 630.00 | 51.33 | +0.7 [-5.4, +6.3] | +117 [-859, +1,203] | -258 [-974, +268] P<=0 0.77 | -258 [-974, +268] P<=0 0.77 |
| busy | micf | 0 | base | sl1 | 786.00 | 52.93 | +1.4 [-3.7, +6.4] | +341 [-800, +1,680] | -35 [-342, +204] P<=0 0.57 | -35 [-342, +204] P<=0 0.57 |
| busy | micf | 0 | comp | 60 | 834.00 | 51.61 | +0.4 [-4.5, +5.3] | +95 [-1,038, +1,402] |  |  |
| busy | micf | 0 | comp | s20 | 858.00 | 18.79 | +1.2 [-3.3, +5.9] | +118 [-293, +605] | +23 [-785, +726] P<=0 0.48 | +23 [-785, +726] P<=0 0.48 |
| busy | micf | 0 | comp | s40 | 852.00 | 35.53 | +0.6 [-4.1, +5.3] | +113 [-655, +1,006] | +18 [-384, +384] P<=0 0.46 | +18 [-384, +384] P<=0 0.46 |
| busy | micf | 0 | comp | s100 | 822.00 | 79.06 | +0.1 [-4.9, +5.2] | +38 [-1,744, +2,092] | -56 [-731, +655] P<=0 0.56 | -56 [-731, +655] P<=0 0.56 |
| busy | micf | 0 | comp | dk0.5 | 750.00 | 38.48 | -2.3 [-7.4, +2.8] | -380 [-1,138, +462] | -474 [-1,177, +102] P<=0 0.94 | -474 [-1,177, +102] P<=0 0.94 |
| busy | micf | 0 | comp | dk1 | 816.00 | 42.75 | -1.6 [-6.4, +3.2] | -318 [-1,226, +657] | -413 [-978, +36] P<=0 0.96 | -413 [-978, +36] P<=0 0.96 |
| busy | micf | 0 | comp | dk2 | 834.00 | 45.89 | -0.8 [-5.6, +3.9] | -181 [-1,188, +915] | -275 [-750, +60] P<=0 0.93 | -275 [-750, +60] P<=0 0.93 |
| busy | micf | 0 | comp | rv1_30 | 852.00 | 28.96 | +1.6 [-3.2, +6.2] | +234 [-415, +980] | +139 [-421, +639] P<=0 0.30 | +139 [-421, +639] P<=0 0.30 |
| busy | micf | 0 | comp | rv1_0 | 54.00 | 51.62 | +17.9 [-5.6, +34.6] | +212 [-23, +515] | +118 [-1,103, +1,154] P<=0 0.40 | +118 [-1,103, +1,154] P<=0 0.40 |
| busy | micf | 0 | comp | rv3_30 | 846.00 | 31.51 | +2.1 [-2.9, +7.0] | +331 [-412, +1,210] | +236 [-255, +663] P<=0 0.17 | +236 [-255, +663] P<=0 0.17 |
| busy | micf | 0 | comp | rv3_0 | 162.00 | 47.04 | +11.9 [+0.1, +21.5] | +519 [+5, +1,146] | +424 [-500, +1,281] P<=0 0.18 | +424 [-500, +1,281] P<=0 0.18 |
| busy | micf | 0 | comp | dk1_rv1 | 822.00 | 26.19 | +0.5 [-4.8, +5.3] | +60 [-550, +732] | -34 [-760, +612] P<=0 0.53 | -34 [-760, +612] P<=0 0.53 |
| busy | micf | 0 | comp | sl0 | 600.00 | 44.86 | +0.3 [-6.5, +6.8] | +47 [-866, +1,049] | -47 [-516, +346] P<=0 0.56 | -47 [-516, +346] P<=0 0.56 |
| busy | micf | 0 | comp | sl1 | 714.00 | 50.01 | +0.8 [-5.0, +6.3] | +158 [-902, +1,390] | +64 [-74, +209] P<=0 0.18 | +64 [-74, +209] P<=0 0.18 |
| busy | micf | 0 | e+25 | 60 | 888.00 | 54.39 | +1.0 [-3.6, +5.6] | +296 [-913, +1,736] |  |  |
| busy | micf | 0 | e+25 | s20 | 894.00 | 19.38 | +1.0 [-3.3, +5.1] | +106 [-309, +596] | -190 [-1,133, +617] P<=0 0.68 | -190 [-1,133, +617] P<=0 0.68 |
| busy | micf | 0 | e+25 | s40 | 894.00 | 37.28 | +1.2 [-3.3, +5.6] | +239 [-595, +1,223] | -57 [-509, +328] P<=0 0.61 | -57 [-509, +328] P<=0 0.61 |
| busy | micf | 0 | e+25 | s100 | 888.00 | 84.96 | +0.6 [-4.1, +5.2] | +275 [-1,634, +2,454] | -21 [-721, +752] P<=0 0.52 | -21 [-721, +752] P<=0 0.52 |
| busy | micf | 0 | e+25 | dk0.5 | 786.00 | 38.66 | -1.9 [-6.8, +3.1] | -330 [-1,113, +570] | -626 [-1,388, +4] P<=0 0.97 | -626 [-1,388, +4] P<=0 0.97 |
| busy | micf | 0 | e+25 | dk1 | 858.00 | 43.59 | -1.1 [-6.1, +3.8] | -232 [-1,242, +869] | -528 [-1,123, -53] P<=0 0.98 | -528 [-1,123, -53] P<=0 0.98 |
| busy | micf | 0 | e+25 | dk2 | 882.00 | 47.19 | -0.1 [-5.3, +4.8] | -30 [-1,155, +1,265] | -326 [-801, +23] P<=0 0.96 | -326 [-801, +23] P<=0 0.96 |
| busy | micf | 0 | e+25 | rv1_30 | 894.00 | 30.26 | +1.7 [-2.9, +5.9] | +265 [-399, +1,056] | -31 [-697, +516] P<=0 0.52 | -31 [-697, +516] P<=0 0.52 |
| busy | micf | 0 | e+25 | rv1_0 | 60.00 | 55.45 | +11.3 [-8.0, +28.6] | +177 [-65, +495] | -119 [-1,464, +995] P<=0 0.57 | -119 [-1,464, +995] P<=0 0.57 |
| busy | micf | 0 | e+25 | rv3_30 | 894.00 | 33.17 | +2.6 [-2.5, +7.6] | +467 [-383, +1,504] | +171 [-307, +614] P<=0 0.22 | +171 [-307, +614] P<=0 0.22 |
| busy | micf | 0 | e+25 | rv3_0 | 186.00 | 49.65 | +11.2 [-0.3, +20.7] | +620 [-14, +1,427] | +324 [-636, +1,197] P<=0 0.24 | +324 [-636, +1,197] P<=0 0.24 |
| busy | micf | 0 | e+25 | dk1_rv1 | 858.00 | 26.73 | +0.7 [-4.4, +5.4] | +93 [-544, +797] | -203 [-1,042, +474] P<=0 0.71 | -203 [-1,042, +474] P<=0 0.71 |
| busy | micf | 0 | e+25 | sl0 | 612.00 | 51.40 | +0.5 [-5.6, +6.1] | +81 [-856, +1,121] | -215 [-853, +299] P<=0 0.77 | -215 [-853, +299] P<=0 0.77 |
| busy | micf | 0 | e+25 | sl1 | 750.00 | 54.03 | +1.2 [-4.1, +6.3] | +275 [-843, +1,562] | -21 [-260, +197] P<=0 0.56 | -21 [-260, +197] P<=0 0.56 |
| unseen | micf | 0 | base | 60 | 515.19 | 51.46 | +5.7 [+3.0, +8.5] | +1,000 [+509, +1,499] |  |  |
| unseen | micf | 0 | base | s20 | 526.66 | 19.09 | +7.9 [+4.6, +11.2] | +509 [+288, +755] | -491 [-804, -234] P<=0 1.00 | -491 [-804, -234] P<=0 1.00 |
| unseen | micf | 0 | base | s40 | 522.07 | 35.76 | +6.7 [+3.8, +9.6] | +816 [+441, +1,207] | -184 [-327, -63] P<=0 1.00 | -184 [-327, -63] P<=0 1.00 |
| unseen | micf | 0 | base | s100 | 512.89 | 78.96 | +4.8 [+2.1, +7.3] | +1,278 [+558, +1,996] | +278 [+43, +537] P<=0 0.01 | +278 [+43, +537] P<=0 0.01 |
| unseen | micf | 0 | base | dk0.5 | 469.29 | 36.92 | +6.8 [+3.6, +10.2] | +777 [+411, +1,167] | -224 [-445, -18] P<=0 0.98 | -224 [-445, -18] P<=0 0.98 |
| unseen | micf | 0 | base | dk1 | 500.27 | 41.81 | +6.3 [+3.4, +9.3] | +871 [+455, +1,293] | -129 [-300, +33] P<=0 0.94 | -129 [-300, +33] P<=0 0.94 |
| unseen | micf | 0 | base | dk2 | 509.45 | 45.47 | +6.2 [+3.3, +9.1] | +953 [+500, +1,401] | -48 [-173, +69] P<=0 0.79 | -48 [-173, +69] P<=0 0.79 |
| unseen | micf | 0 | base | rv1_30 | 524.37 | 31.02 | +8.3 [+5.0, +11.6] | +856 [+497, +1,225] | -144 [-330, +11] P<=0 0.97 | -144 [-330, +11] P<=0 0.97 |
| unseen | micf | 0 | base | rv1_0 | 80.32 | 50.83 | +21.2 [+12.4, +32.9] | +466 [+256, +707] | -534 [-953, -168] P<=0 1.00 | -534 [-953, -168] P<=0 1.00 |
| unseen | micf | 0 | base | rv3_30 | 517.48 | 35.60 | +8.5 [+5.3, +11.7] | +1,008 [+599, +1,438] | +8 [-122, +128] P<=0 0.46 | +8 [-122, +128] P<=0 0.46 |
| unseen | micf | 0 | base | rv3_0 | 185.88 | 49.64 | +17.0 [+11.3, +23.2] | +948 [+601, +1,330] | -52 [-318, +199] P<=0 0.67 | -52 [-318, +199] P<=0 0.67 |
| unseen | micf | 0 | base | dk1_rv1 | 506.01 | 27.50 | +8.6 [+5.2, +12.2] | +773 [+459, +1,112] | -227 [-461, -13] P<=0 0.98 | -227 [-461, -13] P<=0 0.98 |
| unseen | micf | 0 | base | sl0 | 323.57 | 47.24 | +7.9 [+3.8, +11.8] | +731 [+340, +1,107] | -270 [-483, -74] P<=0 1.00 | -270 [-483, -74] P<=0 1.00 |
| unseen | micf | 0 | base | sl1 | 414.22 | 50.22 | +6.9 [+3.7, +10.0] | +909 [+467, +1,348] | -91 [-199, +5] P<=0 0.97 | -91 [-199, +5] P<=0 0.97 |
| unseen | micf | 0 | comp | 60 | 442.90 | 47.42 | +3.9 [+1.0, +6.8] | +540 [+139, +934] |  |  |
| unseen | micf | 0 | comp | s20 | 455.52 | 18.13 | +5.7 [+2.5, +8.9] | +307 [+136, +483] | -232 [-489, +3] P<=0 0.97 | -232 [-489, +3] P<=0 0.97 |
| unseen | micf | 0 | comp | s40 | 447.49 | 33.64 | +4.4 [+1.5, +7.2] | +434 [+149, +710] | -106 [-236, +12] P<=0 0.96 | -106 [-236, +12] P<=0 0.96 |
| unseen | micf | 0 | comp | s100 | 438.31 | 70.22 | +3.0 [+0.1, +5.8] | +607 [+31, +1,157] | +68 [-130, +263] P<=0 0.22 | +68 [-130, +263] P<=0 0.22 |
| unseen | micf | 0 | comp | dk0.5 | 403.89 | 36.06 | +5.3 [+1.9, +8.9] | +504 [+182, +851] | -35 [-206, +137] P<=0 0.68 | -35 [-206, +137] P<=0 0.68 |
| unseen | micf | 0 | comp | dk1 | 429.13 | 39.98 | +4.8 [+1.6, +7.9] | +538 [+187, +895] | -2 [-139, +138] P<=0 0.52 | -2 [-139, +138] P<=0 0.52 |
| unseen | micf | 0 | comp | dk2 | 439.46 | 42.54 | +4.4 [+1.4, +7.3] | +540 [+179, +905] | +0 [-113, +113] P<=0 0.51 | +0 [-113, +113] P<=0 0.51 |
| unseen | micf | 0 | comp | rv1_30 | 448.64 | 29.06 | +6.2 [+2.9, +9.6] | +517 [+238, +803] | -23 [-176, +123] P<=0 0.65 | -23 [-176, +123] P<=0 0.65 |
| unseen | micf | 0 | comp | rv1_0 | 67.70 | 44.68 | +22.5 [+11.9, +36.4] | +350 [+166, +563] | -190 [-527, +121] P<=0 0.89 | -190 [-527, +121] P<=0 0.89 |
| unseen | micf | 0 | comp | rv3_30 | 445.20 | 32.87 | +6.6 [+3.2, +9.9] | +619 [+299, +951] | +80 [-44, +206] P<=0 0.10 | +80 [-44, +206] P<=0 0.10 |
| unseen | micf | 0 | comp | rv3_0 | 152.61 | 44.69 | +15.8 [+9.5, +22.7] | +651 [+380, +956] | +111 [-134, +358] P<=0 0.18 | +111 [-134, +358] P<=0 0.18 |
| unseen | micf | 0 | comp | dk1_rv1 | 432.57 | 26.37 | +7.0 [+3.5, +10.5] | +510 [+241, +788] | -29 [-217, +162] P<=0 0.64 | -29 [-217, +162] P<=0 0.64 |
| unseen | micf | 0 | comp | sl0 | 286.85 | 39.72 | +6.1 [+1.7, +10.5] | +422 [+113, +711] | -117 [-282, +36] P<=0 0.94 | -117 [-282, +36] P<=0 0.94 |
| unseen | micf | 0 | comp | sl1 | 364.88 | 44.68 | +5.3 [+1.7, +8.7] | +543 [+173, +909] | +4 [-64, +71] P<=0 0.47 | +4 [-64, +71] P<=0 0.47 |
| unseen | micf | 0 | e+25 | 60 | 477.32 | 51.82 | +5.0 [+2.2, +7.7] | +800 [+350, +1,257] |  |  |
| unseen | micf | 0 | e+25 | s20 | 488.80 | 19.02 | +6.8 [+3.4, +10.3] | +404 [+195, +631] | -396 [-689, -148] P<=0 1.00 | -396 [-689, -148] P<=0 1.00 |
| unseen | micf | 0 | e+25 | s40 | 484.21 | 35.80 | +5.7 [+2.7, +8.6] | +639 [+303, +991] | -160 [-299, -41] P<=0 1.00 | -160 [-299, -41] P<=0 1.00 |
| unseen | micf | 0 | e+25 | s100 | 476.18 | 80.03 | +4.3 [+1.6, +6.9] | +1,065 [+389, +1,732] | +265 [+29, +521] P<=0 0.01 | +265 [+29, +521] P<=0 0.01 |
| unseen | micf | 0 | e+25 | dk0.5 | 431.43 | 37.43 | +6.0 [+2.7, +9.4] | +635 [+286, +1,013] | -165 [-366, +27] P<=0 0.95 | -165 [-366, +27] P<=0 0.95 |
| unseen | micf | 0 | e+25 | dk1 | 462.41 | 42.08 | +5.5 [+2.4, +8.5] | +704 [+304, +1,105] | -96 [-255, +60] P<=0 0.90 | -96 [-255, +60] P<=0 0.90 |
| unseen | micf | 0 | e+25 | dk2 | 471.59 | 45.63 | +5.4 [+2.4, +8.3] | +765 [+337, +1,190] | -34 [-160, +81] P<=0 0.72 | -34 [-160, +81] P<=0 0.72 |
| unseen | micf | 0 | e+25 | rv1_30 | 485.35 | 30.97 | +7.3 [+3.9, +10.7] | +694 [+364, +1,049] | -106 [-277, +43] P<=0 0.92 | -106 [-277, +43] P<=0 0.92 |
| unseen | micf | 0 | e+25 | rv1_0 | 71.14 | 50.94 | +20.8 [+11.4, +33.1] | +394 [+196, +620] | -406 [-791, -66] P<=0 0.99 | -406 [-791, -66] P<=0 0.99 |
| unseen | micf | 0 | e+25 | rv3_30 | 479.62 | 35.41 | +7.6 [+4.3, +11.0] | +829 [+455, +1,228] | +29 [-95, +151] P<=0 0.33 | +29 [-95, +151] P<=0 0.33 |
| unseen | micf | 0 | e+25 | rv3_0 | 166.37 | 49.66 | +16.5 [+10.3, +23.4] | +820 [+486, +1,184] | +21 [-235, +268] P<=0 0.46 | +21 [-235, +268] P<=0 0.46 |
| unseen | micf | 0 | e+25 | dk1_rv1 | 468.14 | 27.35 | +7.8 [+4.2, +11.5] | +641 [+336, +968] | -159 [-370, +45] P<=0 0.94 | -159 [-370, +45] P<=0 0.94 |
| unseen | micf | 0 | e+25 | sl0 | 310.95 | 46.85 | +7.4 [+3.2, +11.5] | +648 [+276, +1,017] | -152 [-342, +21] P<=0 0.96 | -152 [-342, +21] P<=0 0.96 |
| unseen | micf | 0 | e+25 | sl1 | 391.27 | 49.69 | +6.3 [+2.9, +9.6] | +765 [+352, +1,180] | -35 [-121, +44] P<=0 0.80 | -35 [-121, +44] P<=0 0.80 |

## Size rules: vt_v3p_m0.02_any, L = 0
| group | arm | L | fill model | size | fills/day | sh/fill | mk10 c/$ | mk10 $/day | vs 60 sh $/day | gain vs micf $/day |
|---|---|---|---|---|---|---|---|---|---|---|
| select | vt_v3p_m0.02_any | 0 | base | 60 | 2,642.00 | 50.03 | +4.3 [+1.8, +8.7] | +3,435 [+1,393, +5,579] |  |  |
| select | vt_v3p_m0.02_any | 0 | base | s20 | 2,810.00 | 18.86 | +5.2 [+2.4, +10.3] | +1,669 [+836, +2,572] | -1,766 [-3,077, -554] P<=0 1.00 | +853 [-271, +2,077] P<=0 0.07 |
| select | vt_v3p_m0.02_any | 0 | base | s40 | 2,710.00 | 35.40 | +4.7 [+2.1, +9.5] | +2,728 [+1,238, +4,298] | -707 [-1,314, -134] P<=0 0.99 | +1,912 [+269, +3,724] P<=0 0.01 |
| select | vt_v3p_m0.02_any | 0 | base | s100 | 2,566.00 | 76.34 | +3.8 [+1.2, +8.1] | +4,518 [+1,372, +7,736] | +1,083 [-23, +2,244] P<=0 0.03 | +3,702 [+586, +7,014] P<=0 0.01 |
| select | vt_v3p_m0.02_any | 0 | base | dk0.5 | 2,472.00 | 36.50 | +4.2 [+1.7, +9.1] | +2,274 [+1,010, +3,611] | -1,161 [-2,196, -232] P<=0 0.99 | +1,458 [+147, +2,897] P<=0 0.01 |
| select | vt_v3p_m0.02_any | 0 | base | dk1 | 2,642.00 | 40.09 | +4.3 [+1.7, +9.0] | +2,750 [+1,146, +4,392] | -684 [-1,432, -13] P<=0 0.98 | +1,934 [+297, +3,701] P<=0 0.01 |
| select | vt_v3p_m0.02_any | 0 | base | dk2 | 2,648.00 | 44.03 | +4.6 [+1.9, +9.3] | +3,212 [+1,371, +5,181] | -223 [-702, +246] P<=0 0.83 | +2,395 [+531, +4,462] P<=0 0.01 |
| select | vt_v3p_m0.02_any | 0 | base | rv1_30 | 2,742.00 | 30.21 | +5.3 [+2.6, +10.6] | +2,645 [+1,362, +4,033] | -790 [-1,654, +35] P<=0 0.97 | +1,829 [+406, +3,408] P<=0 0.00 |
| select | vt_v3p_m0.02_any | 0 | base | rv1_0 | 350.00 | 52.27 | +7.8 [+3.4, +29.6] | +855 [+410, +1,353] | -2,580 [-4,620, -648] P<=0 0.99 | +38 [-778, +838] P<=0 0.48 |
| select | vt_v3p_m0.02_any | 0 | base | rv3_30 | 2,706.00 | 35.94 | +4.7 [+2.1, +10.1] | +2,794 [+1,405, +4,237] | -640 [-1,507, +144] P<=0 0.95 | +1,978 [+487, +3,674] P<=0 0.00 |
| select | vt_v3p_m0.02_any | 0 | base | rv3_0 | 1,058.00 | 49.75 | +4.2 [+1.3, +14.5] | +1,366 [+581, +2,325] | -2,069 [-3,972, -312] P<=0 0.99 | +550 [-410, +1,595] P<=0 0.14 |
| select | vt_v3p_m0.02_any | 0 | base | dk1_rv1 | 2,710.00 | 26.54 | +5.5 [+2.6, +11.2] | +2,382 [+1,271, +3,573] | -1,053 [-2,144, -35] P<=0 0.98 | +1,566 [+310, +2,947] P<=0 0.01 |
| select | vt_v3p_m0.02_any | 0 | base | sl0 | 1,958.00 | 50.77 | +4.4 [+1.4, +9.4] | +2,576 [+684, +4,466] | -859 [-1,455, -281] P<=0 1.00 | +1,760 [-234, +3,809] P<=0 0.04 |
| select | vt_v3p_m0.02_any | 0 | base | sl1 | 2,340.00 | 50.11 | +4.4 [+1.6, +9.0] | +3,073 [+1,090, +5,043] | -362 [-797, +32] P<=0 0.97 | +2,257 [+190, +4,410] P<=0 0.01 |
| select | vt_v3p_m0.02_any | 0 | comp | 60 | 2,334.00 | 43.30 | +1.8 [-0.6, +5.1] | +1,103 [-384, +2,504] |  |  |
| select | vt_v3p_m0.02_any | 0 | comp | s20 | 2,490.00 | 17.62 | +3.4 [+1.0, +7.5] | +901 [+262, +1,547] | -203 [-1,046, +667] P<=0 0.68 | +678 [-235, +1,606] P<=0 0.07 |
| select | vt_v3p_m0.02_any | 0 | comp | s40 | 2,382.00 | 31.54 | +2.5 [+0.1, +6.1] | +1,140 [+57, +2,206] | +37 [-361, +443] P<=0 0.44 | +917 [-330, +2,165] P<=0 0.07 |
| select | vt_v3p_m0.02_any | 0 | comp | s100 | 2,248.00 | 63.29 | +0.6 [-2.1, +3.5] | +534 [-1,527, +2,413] | -569 [-1,311, +118] P<=0 0.95 | +311 [-1,744, +2,389] P<=0 0.39 |
| select | vt_v3p_m0.02_any | 0 | comp | dk0.5 | 2,182.00 | 33.91 | +2.0 [-0.2, +5.7] | +913 [-101, +1,854] | -190 [-864, +471] P<=0 0.72 | +690 [-340, +1,750] P<=0 0.09 |
| select | vt_v3p_m0.02_any | 0 | comp | dk1 | 2,326.00 | 36.18 | +2.1 [-0.2, +5.4] | +1,048 [-103, +2,154] | -55 [-547, +412] P<=0 0.59 | +825 [-365, +2,060] P<=0 0.09 |
| select | vt_v3p_m0.02_any | 0 | comp | dk2 | 2,344.00 | 38.88 | +2.1 [-0.1, +5.4] | +1,157 [-71, +2,343] | +53 [-303, +415] P<=0 0.40 | +934 [-349, +2,243] P<=0 0.09 |
| select | vt_v3p_m0.02_any | 0 | comp | rv1_30 | 2,418.00 | 27.36 | +3.0 [+0.7, +6.9] | +1,183 [+263, +2,111] | +80 [-495, +665] P<=0 0.41 | +961 [-150, +2,076] P<=0 0.04 |
| select | vt_v3p_m0.02_any | 0 | comp | rv1_0 | 306.00 | 48.25 | +4.6 [+1.5, +19.8] | +409 [+112, +751] | -694 [-2,030, +685] P<=0 0.85 | +187 [-523, +887] P<=0 0.31 |
| select | vt_v3p_m0.02_any | 0 | comp | rv3_30 | 2,378.00 | 32.07 | +2.4 [+0.2, +6.4] | +1,131 [+72, +2,157] | +28 [-543, +604] P<=0 0.47 | +908 [-269, +2,086] P<=0 0.06 |
| select | vt_v3p_m0.02_any | 0 | comp | rv3_0 | 928.00 | 44.64 | +2.0 [-0.6, +10.1] | +512 [-190, +1,276] | -592 [-1,919, +689] P<=0 0.83 | +289 [-590, +1,156] P<=0 0.26 |
| select | vt_v3p_m0.02_any | 0 | comp | dk1_rv1 | 2,392.00 | 24.58 | +3.1 [+0.9, +7.3] | +1,106 [+290, +1,919] | +3 [-737, +742] P<=0 0.52 | +883 [-98, +1,887] P<=0 0.04 |
| select | vt_v3p_m0.02_any | 0 | comp | sl0 | 1,724.00 | 43.65 | +1.5 [-2.1, +5.3] | +683 [-730, +2,005] | -420 [-838, +18] P<=0 0.97 | +460 [-1,032, +1,984] P<=0 0.28 |
| select | vt_v3p_m0.02_any | 0 | comp | sl1 | 2,054.00 | 43.01 | +1.9 [-1.1, +5.3] | +981 [-478, +2,375] | -123 [-388, +179] P<=0 0.81 | +758 [-799, +2,328] P<=0 0.17 |
| select | vt_v3p_m0.02_any | 0 | e+25 | 60 | 2,528.00 | 50.66 | +4.3 [+1.6, +8.9] | +3,336 [+1,263, +5,588] |  |  |
| select | vt_v3p_m0.02_any | 0 | e+25 | s20 | 2,684.00 | 19.04 | +5.1 [+2.3, +10.3] | +1,589 [+763, +2,512] | -1,747 [-3,092, -484] P<=0 1.00 | +1,059 [-26, +2,264] P<=0 0.03 |
| select | vt_v3p_m0.02_any | 0 | e+25 | s40 | 2,592.00 | 35.78 | +4.7 [+1.9, +9.6] | +2,628 [+1,135, +4,284] | -708 [-1,313, -123] P<=0 0.99 | +2,098 [+441, +3,915] P<=0 0.01 |
| select | vt_v3p_m0.02_any | 0 | e+25 | s100 | 2,450.00 | 77.57 | +3.8 [+1.0, +8.0] | +4,311 [+1,234, +7,540] | +975 [-59, +2,051] P<=0 0.03 | +3,781 [+737, +7,093] P<=0 0.01 |
| select | vt_v3p_m0.02_any | 0 | e+25 | dk0.5 | 2,360.00 | 36.75 | +3.7 [+1.3, +8.7] | +1,952 [+694, +3,286] | -1,384 [-2,495, -375] P<=0 1.00 | +1,422 [+125, +2,846] P<=0 0.02 |
| select | vt_v3p_m0.02_any | 0 | e+25 | dk1 | 2,532.00 | 40.32 | +3.8 [+1.3, +8.6] | +2,365 [+826, +4,023] | -971 [-1,813, -240] P<=0 0.99 | +1,835 [+228, +3,574] P<=0 0.01 |
| select | vt_v3p_m0.02_any | 0 | e+25 | dk2 | 2,536.00 | 44.42 | +4.1 [+1.5, +8.8] | +2,817 [+1,067, +4,699] | -519 [-1,091, +5] P<=0 0.97 | +2,287 [+440, +4,327] P<=0 0.01 |
| select | vt_v3p_m0.02_any | 0 | e+25 | rv1_30 | 2,626.00 | 30.47 | +5.1 [+2.3, +10.5] | +2,477 [+1,209, +3,858] | -859 [-1,771, -8] P<=0 0.98 | +1,947 [+519, +3,518] P<=0 0.00 |
| select | vt_v3p_m0.02_any | 0 | e+25 | rv1_0 | 330.00 | 53.31 | +6.8 [+2.8, +27.5] | +722 [+315, +1,166] | -2,614 [-4,682, -738] P<=0 0.99 | +192 [-614, +978] P<=0 0.34 |
| select | vt_v3p_m0.02_any | 0 | e+25 | rv3_30 | 2,594.00 | 36.28 | +4.6 [+1.9, +10.0] | +2,621 [+1,233, +4,099] | -715 [-1,589, +105] P<=0 0.95 | +2,091 [+591, +3,784] P<=0 0.00 |
| select | vt_v3p_m0.02_any | 0 | e+25 | rv3_0 | 1,000.00 | 51.06 | +4.0 [+1.1, +14.1] | +1,254 [+488, +2,164] | -2,082 [-4,058, -281] P<=0 0.99 | +724 [-238, +1,741] P<=0 0.07 |
| select | vt_v3p_m0.02_any | 0 | e+25 | dk1_rv1 | 2,596.00 | 26.73 | +5.0 [+2.2, +10.7] | +2,093 [+1,009, +3,291] | -1,243 [-2,441, -165] P<=0 0.99 | +1,563 [+339, +2,937] P<=0 0.01 |
| select | vt_v3p_m0.02_any | 0 | e+25 | sl0 | 1,886.00 | 51.48 | +4.4 [+1.3, +9.8] | +2,559 [+680, +4,464] | -778 [-1,438, -147] P<=0 0.99 | +2,029 [+10, +4,168] P<=0 0.02 |
| select | vt_v3p_m0.02_any | 0 | e+25 | sl1 | 2,228.00 | 50.65 | +4.3 [+1.5, +9.3] | +2,946 [+976, +4,992] | -391 [-836, +30] P<=0 0.97 | +2,416 [+312, +4,651] P<=0 0.01 |
| quiet | vt_v3p_m0.02_any | 0 | base | 60 | 1,576.20 | 51.64 | +8.9 [+0.1, +18.6] | +3,824 [+39, +8,060] |  |  |
| quiet | vt_v3p_m0.02_any | 0 | base | s20 | 1,634.36 | 19.04 | +9.7 [+0.8, +19.1] | +1,582 [+131, +3,099] | -2,242 [-5,005, +158] P<=0 0.97 | +434 [-1,141, +2,077] P<=0 0.29 |
| quiet | vt_v3p_m0.02_any | 0 | base | s40 | 1,601.73 | 36.22 | +9.2 [+0.6, +18.8] | +2,835 [+157, +5,763] | -989 [-2,332, +173] P<=0 0.95 | +1,687 [-1,068, +4,698] P<=0 0.12 |
| quiet | vt_v3p_m0.02_any | 0 | base | s100 | 1,550.66 | 78.31 | +8.3 [-0.8, +18.5] | +5,336 [-499, +12,199] | +1,512 [-592, +4,060] P<=0 0.09 | +4,188 [-1,720, +10,950] P<=0 0.09 |
| quiet | vt_v3p_m0.02_any | 0 | base | dk0.5 | 1,481.14 | 37.32 | +11.6 [+1.6, +23.6] | +3,258 [+417, +6,807] | -566 [-1,817, +691] P<=0 0.82 | +2,109 [-811, +5,729] P<=0 0.09 |
| quiet | vt_v3p_m0.02_any | 0 | base | dk1 | 1,553.50 | 42.62 | +10.8 [+1.4, +21.6] | +3,695 [+464, +7,622] | -129 [-900, +674] P<=0 0.64 | +2,547 [-836, +6,356] P<=0 0.07 |
| quiet | vt_v3p_m0.02_any | 0 | base | dk2 | 1,566.27 | 46.54 | +10.1 [+1.0, +20.4] | +3,863 [+366, +7,925] | +39 [-424, +544] P<=0 0.46 | +2,715 [-869, +6,680] P<=0 0.07 |
| quiet | vt_v3p_m0.02_any | 0 | base | rv1_30 | 1,617.34 | 31.19 | +11.0 [+2.0, +21.3] | +2,898 [+484, +5,713] | -925 [-2,474, +515] P<=0 0.89 | +1,750 [-762, +4,604] P<=0 0.09 |
| quiet | vt_v3p_m0.02_any | 0 | base | rv1_0 | 211.39 | 55.05 | +24.3 [+8.2, +42.9] | +1,321 [+387, +2,904] | -2,503 [-5,998, +717] P<=0 0.93 | +173 [-962, +1,788] P<=0 0.46 |
| quiet | vt_v3p_m0.02_any | 0 | base | rv3_30 | 1,608.83 | 36.14 | +11.0 [+2.2, +21.5] | +3,312 [+647, +6,677] | -512 [-1,931, +808] P<=0 0.77 | +2,163 [-628, +5,550] P<=0 0.07 |
| quiet | vt_v3p_m0.02_any | 0 | base | rv3_0 | 551.88 | 52.78 | +17.8 [+6.7, +32.1] | +2,491 [+825, +5,253] | -1,333 [-4,456, +1,642] P<=0 0.80 | +1,343 [-349, +4,091] P<=0 0.11 |
| quiet | vt_v3p_m0.02_any | 0 | base | dk1_rv1 | 1,583.29 | 27.85 | +12.4 [+2.7, +23.4] | +2,799 [+597, +5,537] | -1,024 [-2,798, +618] P<=0 0.88 | +1,651 [-669, +4,412] P<=0 0.09 |
| quiet | vt_v3p_m0.02_any | 0 | base | sl0 | 1,195.98 | 50.13 | +10.9 [+0.5, +22.6] | +3,342 [+138, +7,201] | -482 [-1,260, +293] P<=0 0.89 | +2,194 [-1,089, +6,003] P<=0 0.10 |
| quiet | vt_v3p_m0.02_any | 0 | base | sl1 | 1,414.46 | 50.80 | +9.8 [+0.4, +20.1] | +3,683 [+177, +7,720] | -140 [-542, +241] P<=0 0.76 | +2,535 [-1,034, +6,626] P<=0 0.09 |
| quiet | vt_v3p_m0.02_any | 0 | comp | 60 | 1,383.25 | 44.91 | +7.6 [-1.5, +18.3] | +2,504 [-495, +6,054] |  |  |
| quiet | vt_v3p_m0.02_any | 0 | comp | s20 | 1,452.77 | 18.01 | +8.7 [+0.1, +18.2] | +1,214 [+8, +2,605] | -1,290 [-3,552, +538] P<=0 0.91 | +569 [-718, +2,036] P<=0 0.20 |
| quiet | vt_v3p_m0.02_any | 0 | comp | s40 | 1,415.88 | 32.38 | +7.9 [-1.1, +18.2] | +1,927 [-270, +4,485] | -577 [-1,604, +220] P<=0 0.91 | +1,282 [-940, +3,811] P<=0 0.14 |
| quiet | vt_v3p_m0.02_any | 0 | comp | s100 | 1,349.20 | 64.71 | +6.6 [-1.9, +17.0] | +3,074 [-866, +7,862] | +570 [-457, +1,824] P<=0 0.15 | +2,429 [-1,654, +7,275] P<=0 0.13 |
| quiet | vt_v3p_m0.02_any | 0 | comp | dk0.5 | 1,292.45 | 34.93 | +10.9 [+0.6, +23.7] | +2,544 [+141, +5,811] | +40 [-767, +830] P<=0 0.48 | +1,899 [-600, +5,067] P<=0 0.08 |
| quiet | vt_v3p_m0.02_any | 0 | comp | dk1 | 1,353.46 | 38.61 | +9.8 [+0.1, +21.4] | +2,671 [+32, +5,983] | +167 [-336, +679] P<=0 0.27 | +2,026 [-679, +5,361] P<=0 0.08 |
| quiet | vt_v3p_m0.02_any | 0 | comp | dk2 | 1,373.32 | 41.18 | +9.0 [-0.5, +20.1] | +2,673 [-139, +6,107] | +169 [-143, +501] P<=0 0.16 | +2,028 [-858, +5,455] P<=0 0.09 |
| quiet | vt_v3p_m0.02_any | 0 | comp | rv1_30 | 1,427.23 | 28.67 | +10.0 [+0.4, +21.3] | +2,145 [+97, +4,786] | -359 [-1,445, +594] P<=0 0.77 | +1,500 [-623, +4,146] P<=0 0.10 |
| quiet | vt_v3p_m0.02_any | 0 | comp | rv1_0 | 192.95 | 49.60 | +24.9 [+5.6, +45.9] | +1,108 [+199, +2,669] | -1,396 [-3,919, +945] P<=0 0.87 | +463 [-556, +2,057] P<=0 0.32 |
| quiet | vt_v3p_m0.02_any | 0 | comp | rv3_30 | 1,418.72 | 32.83 | +9.9 [+0.4, +21.2] | +2,408 [+101, +5,484] | -96 [-1,028, +741] P<=0 0.59 | +1,763 [-595, +4,780] P<=0 0.08 |
| quiet | vt_v3p_m0.02_any | 0 | comp | rv3_0 | 480.95 | 48.74 | +16.6 [+3.9, +33.1] | +1,894 [+373, +4,468] | -610 [-2,845, +1,447] P<=0 0.72 | +1,249 [-287, +3,850] P<=0 0.12 |
| quiet | vt_v3p_m0.02_any | 0 | comp | dk1_rv1 | 1,393.18 | 26.02 | +11.8 [+1.5, +23.8] | +2,226 [+265, +4,840] | -278 [-1,490, +833] P<=0 0.68 | +1,581 [-445, +4,095] P<=0 0.07 |
| quiet | vt_v3p_m0.02_any | 0 | comp | sl0 | 1,066.88 | 41.78 | +9.4 [-1.9, +22.8] | +2,129 [-378, +5,316] | -375 [-999, +214] P<=0 0.90 | +1,484 [-1,135, +4,628] P<=0 0.15 |
| quiet | vt_v3p_m0.02_any | 0 | comp | sl1 | 1,248.47 | 43.22 | +8.9 [-1.0, +20.5] | +2,480 [-274, +5,914] | -24 [-418, +334] P<=0 0.55 | +1,835 [-983, +5,187] P<=0 0.12 |
| quiet | vt_v3p_m0.02_any | 0 | e+25 | 60 | 1,493.91 | 52.29 | +8.8 [+0.1, +18.4] | +3,646 [+46, +7,730] |  |  |
| quiet | vt_v3p_m0.02_any | 0 | e+25 | s20 | 1,553.50 | 19.02 | +9.7 [+0.9, +18.9] | +1,501 [+136, +2,991] | -2,145 [-4,767, +149] P<=0 0.97 | +583 [-868, +2,150] P<=0 0.22 |
| quiet | vt_v3p_m0.02_any | 0 | e+25 | s40 | 1,520.87 | 36.43 | +9.1 [+0.4, +18.5] | +2,659 [+124, +5,482] | -987 [-2,288, +129] P<=0 0.96 | +1,741 [-818, +4,617] P<=0 0.10 |
| quiet | vt_v3p_m0.02_any | 0 | e+25 | s100 | 1,465.54 | 79.78 | +8.2 [-0.9, +18.2] | +5,037 [-560, +11,567] | +1,391 [-633, +3,833] P<=0 0.10 | +4,118 [-1,468, +10,448] P<=0 0.08 |
| quiet | vt_v3p_m0.02_any | 0 | e+25 | dk0.5 | 1,405.95 | 37.53 | +11.4 [+1.4, +23.6] | +3,077 [+384, +6,555] | -569 [-1,825, +681] P<=0 0.82 | +2,158 [-623, +5,662] P<=0 0.07 |
| quiet | vt_v3p_m0.02_any | 0 | e+25 | dk1 | 1,472.63 | 42.79 | +10.6 [+1.2, +21.5] | +3,471 [+403, +7,224] | -175 [-984, +666] P<=0 0.67 | +2,552 [-584, +6,192] P<=0 0.06 |
| quiet | vt_v3p_m0.02_any | 0 | e+25 | dk2 | 1,491.07 | 46.59 | +10.1 [+1.0, +20.1] | +3,672 [+404, +7,500] | +26 [-504, +588] P<=0 0.49 | +2,753 [-560, +6,556] P<=0 0.06 |
| quiet | vt_v3p_m0.02_any | 0 | e+25 | rv1_30 | 1,533.64 | 31.30 | +10.8 [+1.8, +21.3] | +2,709 [+413, +5,467] | -937 [-2,428, +437] P<=0 0.90 | +1,790 [-557, +4,580] P<=0 0.07 |
| quiet | vt_v3p_m0.02_any | 0 | e+25 | rv1_0 | 207.13 | 53.82 | +23.6 [+6.6, +42.9] | +1,208 [+279, +2,800] | -2,438 [-5,723, +652] P<=0 0.94 | +289 [-801, +1,909] P<=0 0.39 |
| quiet | vt_v3p_m0.02_any | 0 | e+25 | rv3_30 | 1,525.12 | 36.35 | +10.9 [+2.0, +21.5] | +3,118 [+505, +6,479] | -528 [-1,829, +738] P<=0 0.79 | +2,199 [-431, +5,565] P<=0 0.06 |
| quiet | vt_v3p_m0.02_any | 0 | e+25 | rv3_0 | 522.09 | 53.38 | +17.4 [+5.6, +32.5] | +2,332 [+675, +5,113] | -1,314 [-4,233, +1,466] P<=0 0.82 | +1,413 [-244, +4,188] P<=0 0.09 |
| quiet | vt_v3p_m0.02_any | 0 | e+25 | dk1_rv1 | 1,498.17 | 27.93 | +12.2 [+2.4, +23.4] | +2,626 [+504, +5,305] | -1,020 [-2,700, +586] P<=0 0.89 | +1,707 [-473, +4,363] P<=0 0.07 |
| quiet | vt_v3p_m0.02_any | 0 | e+25 | sl0 | 1,156.26 | 50.34 | +10.7 [+0.0, +22.5] | +3,215 [+2, +7,058] | -432 [-1,130, +246] P<=0 0.89 | +2,296 [-897, +6,112] P<=0 0.09 |
| quiet | vt_v3p_m0.02_any | 0 | e+25 | sl1 | 1,352.04 | 51.29 | +9.6 [-0.0, +19.9] | +3,466 [-9, +7,475] | -180 [-525, +103] P<=0 0.88 | +2,547 [-961, +6,603] P<=0 0.09 |
| busy | vt_v3p_m0.02_any | 0 | base | 60 | 3,186.00 | 51.16 | -1.6 [-6.5, +3.5] | -1,269 [-5,677, +2,835] |  |  |
| busy | vt_v3p_m0.02_any | 0 | base | s20 | 3,222.00 | 18.88 | -0.2 [-4.9, +4.8] | -56 [-1,584, +1,443] | +1,213 [-1,284, +4,035] P<=0 0.20 | -431 [-2,369, +1,431] P<=0 0.66 |
| busy | vt_v3p_m0.02_any | 0 | base | s40 | 3,198.00 | 35.88 | -1.0 [-5.7, +4.0] | -558 [-3,555, +2,266] | +711 [-528, +2,105] P<=0 0.15 | -933 [-4,007, +1,942] P<=0 0.71 |
| busy | vt_v3p_m0.02_any | 0 | base | s100 | 3,126.00 | 78.24 | -2.4 [-7.4, +2.7] | -2,957 [-9,434, +3,099] | -1,688 [-3,770, +313] P<=0 0.95 | -3,332 [-9,556, +2,419] P<=0 0.85 |
| busy | vt_v3p_m0.02_any | 0 | base | dk0.5 | 2,976.00 | 38.23 | -2.4 [-7.9, +3.3] | -1,285 [-4,719, +1,683] | -16 [-1,386, +1,281] P<=0 0.52 | -1,660 [-5,189, +1,356] P<=0 0.83 |
| busy | vt_v3p_m0.02_any | 0 | base | dk1 | 3,174.00 | 42.48 | -2.2 [-8.1, +3.8] | -1,434 [-5,917, +2,357] | -165 [-1,029, +702] P<=0 0.66 | -1,809 [-6,332, +1,876] P<=0 0.80 |
| busy | vt_v3p_m0.02_any | 0 | base | dk2 | 3,156.00 | 46.64 | -1.9 [-7.5, +3.8] | -1,400 [-6,017, +2,620] | -131 [-826, +475] P<=0 0.64 | -1,775 [-6,329, +2,064] P<=0 0.79 |
| busy | vt_v3p_m0.02_any | 0 | base | rv1_30 | 3,210.00 | 31.14 | -0.4 [-5.1, +4.4] | -191 [-2,615, +2,147] | +1,078 [-692, +3,097] P<=0 0.13 | -566 [-3,210, +1,918] P<=0 0.65 |
| busy | vt_v3p_m0.02_any | 0 | base | rv1_0 | 456.00 | 53.80 | +2.5 [-6.7, +11.5] | +215 [-544, +964] | +1,484 [-2,268, +5,654] P<=0 0.25 | -160 [-1,921, +1,374] P<=0 0.57 |
| busy | vt_v3p_m0.02_any | 0 | base | rv3_30 | 3,210.00 | 37.81 | -0.5 [-4.8, +3.9] | -308 [-3,005, +2,213] | +961 [-609, +2,886] P<=0 0.14 | -683 [-3,390, +1,931] P<=0 0.68 |
| busy | vt_v3p_m0.02_any | 0 | base | rv3_0 | 1,350.00 | 52.58 | +0.6 [-3.7, +5.0] | +169 [-1,113, +1,423] | +1,437 [-1,942, +5,333] P<=0 0.25 | -207 [-1,998, +1,432] P<=0 0.59 |
| busy | vt_v3p_m0.02_any | 0 | base | dk1_rv1 | 3,180.00 | 28.09 | -0.6 [-5.9, +4.7] | -263 [-2,701, +1,942] | +1,006 [-919, +3,048] P<=0 0.16 | -638 [-3,330, +1,771] P<=0 0.67 |
| busy | vt_v3p_m0.02_any | 0 | base | sl0 | 1,734.00 | 47.05 | -0.8 [-7.8, +5.8] | -319 [-2,974, +2,517] | +950 [-924, +3,693] P<=0 0.25 | -694 [-3,680, +2,177] P<=0 0.67 |
| busy | vt_v3p_m0.02_any | 0 | base | sl1 | 2,550.00 | 49.17 | -1.0 [-6.4, +4.6] | -629 [-4,255, +2,944] | +640 [-393, +1,991] P<=0 0.16 | -1,004 [-4,632, +2,405] P<=0 0.70 |
| busy | vt_v3p_m0.02_any | 0 | comp | 60 | 2,772.00 | 45.50 | -3.6 [-8.5, +1.4] | -2,285 [-5,657, +870] |  |  |
| busy | vt_v3p_m0.02_any | 0 | comp | s20 | 2,862.00 | 17.97 | -2.2 [-7.1, +2.9] | -577 [-1,961, +727] | +1,708 [-104, +3,712] P<=0 0.03 | -672 [-2,486, +1,040] P<=0 0.77 |
| busy | vt_v3p_m0.02_any | 0 | comp | s40 | 2,802.00 | 32.94 | -2.9 [-7.9, +2.3] | -1,341 [-3,835, +1,071] | +944 [+148, +1,841] P<=0 0.01 | -1,436 [-4,098, +979] P<=0 0.87 |
| busy | vt_v3p_m0.02_any | 0 | comp | s100 | 2,754.00 | 65.19 | -4.1 [-8.4, +0.3] | -3,681 [-7,923, +256] | -1,395 [-2,535, -391] P<=0 1.00 | -3,775 [-8,222, +93] P<=0 0.97 |
| busy | vt_v3p_m0.02_any | 0 | comp | dk0.5 | 2,634.00 | 34.99 | -4.6 [-10.1, +1.2] | -2,041 [-4,922, +484] | +245 [-620, +1,117] P<=0 0.30 | -2,135 [-5,193, +476] P<=0 0.93 |
| busy | vt_v3p_m0.02_any | 0 | comp | dk1 | 2,760.00 | 38.65 | -4.2 [-9.7, +1.6] | -2,175 [-5,547, +784] | +110 [-499, +736] P<=0 0.37 | -2,269 [-5,807, +697] P<=0 0.92 |
| busy | vt_v3p_m0.02_any | 0 | comp | dk2 | 2,754.00 | 41.86 | -3.8 [-9.3, +1.8] | -2,186 [-5,693, +981] | +99 [-410, +602] P<=0 0.33 | -2,280 [-5,916, +817] P<=0 0.91 |
| busy | vt_v3p_m0.02_any | 0 | comp | rv1_30 | 2,838.00 | 28.86 | -2.3 [-7.1, +2.8] | -900 [-2,982, +1,096] | +1,386 [+196, +2,752] P<=0 0.01 | -994 [-3,358, +1,238] P<=0 0.81 |
| busy | vt_v3p_m0.02_any | 0 | comp | rv1_0 | 408.00 | 49.41 | +1.9 [-8.9, +12.0] | +134 [-588, +828] | +2,419 [-442, +5,607] P<=0 0.05 | +40 [-1,449, +1,373] P<=0 0.48 |
| busy | vt_v3p_m0.02_any | 0 | comp | rv3_30 | 2,832.00 | 34.44 | -2.7 [-7.0, +1.9] | -1,290 [-3,525, +852] | +996 [-61, +2,282] P<=0 0.04 | -1,384 [-3,820, +912] P<=0 0.88 |
| busy | vt_v3p_m0.02_any | 0 | comp | rv3_0 | 1,182.00 | 47.45 | -2.1 [-6.8, +2.6] | -499 [-1,703, +562] | +1,787 [-775, +4,815] P<=0 0.10 | -593 [-2,139, +879] P<=0 0.79 |
| busy | vt_v3p_m0.02_any | 0 | comp | dk1_rv1 | 2,814.00 | 26.05 | -2.5 [-7.8, +2.9] | -881 [-2,965, +1,003] | +1,404 [+76, +2,790] P<=0 0.02 | -975 [-3,366, +1,118] P<=0 0.80 |
| busy | vt_v3p_m0.02_any | 0 | comp | sl0 | 1,422.00 | 41.37 | -3.4 [-11.2, +3.9] | -971 [-3,195, +1,225] | +1,315 [-6, +3,093] P<=0 0.03 | -1,065 [-3,608, +1,263] P<=0 0.80 |
| busy | vt_v3p_m0.02_any | 0 | comp | sl1 | 2,166.00 | 42.27 | -3.3 [-9.5, +2.7] | -1,504 [-4,387, +1,174] | +781 [+94, +1,552] P<=0 0.01 | -1,598 [-4,785, +1,183] P<=0 0.85 |
| busy | vt_v3p_m0.02_any | 0 | e+25 | 60 | 2,934.00 | 52.25 | -2.1 [-7.1, +3.2] | -1,603 [-5,928, +2,415] |  |  |
| busy | vt_v3p_m0.02_any | 0 | e+25 | s20 | 2,988.00 | 19.17 | -0.8 [-5.6, +4.2] | -231 [-1,736, +1,231] | +1,372 [-1,050, +4,035] P<=0 0.15 | -527 [-2,377, +1,210] P<=0 0.71 |
| busy | vt_v3p_m0.02_any | 0 | e+25 | s40 | 2,964.00 | 36.34 | -1.7 [-6.6, +3.5] | -924 [-3,936, +1,859] | +679 [-490, +1,962] P<=0 0.14 | -1,220 [-4,256, +1,524] P<=0 0.79 |
| busy | vt_v3p_m0.02_any | 0 | e+25 | s100 | 2,898.00 | 80.27 | -2.4 [-7.2, +2.7] | -2,841 [-8,853, +3,019] | -1,238 [-3,119, +580] P<=0 0.91 | -3,137 [-8,787, +2,265] P<=0 0.86 |
| busy | vt_v3p_m0.02_any | 0 | e+25 | dk0.5 | 2,730.00 | 38.91 | -3.3 [-9.0, +2.6] | -1,664 [-5,003, +1,242] | -61 [-1,422, +1,182] P<=0 0.54 | -1,960 [-5,375, +939] P<=0 0.89 |
| busy | vt_v3p_m0.02_any | 0 | e+25 | dk1 | 2,922.00 | 43.16 | -2.9 [-9.0, +3.2] | -1,809 [-6,150, +1,836] | -206 [-1,127, +696] P<=0 0.68 | -2,105 [-6,514, +1,415] P<=0 0.85 |
| busy | vt_v3p_m0.02_any | 0 | e+25 | dk2 | 2,910.00 | 47.49 | -2.6 [-8.1, +3.3] | -1,761 [-6,283, +2,172] | -158 [-924, +474] P<=0 0.66 | -2,057 [-6,476, +1,605] P<=0 0.84 |
| busy | vt_v3p_m0.02_any | 0 | e+25 | rv1_30 | 2,976.00 | 31.53 | -1.0 [-5.8, +4.0] | -442 [-2,829, +1,849] | +1,161 [-550, +3,075] P<=0 0.11 | -738 [-3,219, +1,614] P<=0 0.73 |
| busy | vt_v3p_m0.02_any | 0 | e+25 | rv1_0 | 432.00 | 53.86 | +3.2 [-5.5, +12.2] | +260 [-434, +977] | +1,863 [-1,741, +5,875] P<=0 0.18 | -36 [-1,618, +1,401] P<=0 0.52 |
| busy | vt_v3p_m0.02_any | 0 | e+25 | rv3_30 | 2,976.00 | 38.03 | -1.4 [-5.8, +3.2] | -775 [-3,376, +1,695] | +828 [-728, +2,628] P<=0 0.17 | -1,071 [-3,685, +1,386] P<=0 0.80 |
| busy | vt_v3p_m0.02_any | 0 | e+25 | rv3_0 | 1,224.00 | 52.96 | -1.0 [-5.4, +3.3] | -273 [-1,544, +845] | +1,330 [-2,047, +5,065] P<=0 0.26 | -569 [-2,251, +975] P<=0 0.77 |
| busy | vt_v3p_m0.02_any | 0 | e+25 | dk1_rv1 | 2,928.00 | 28.50 | -1.3 [-6.6, +4.2] | -516 [-2,884, +1,607] | +1,087 [-809, +3,025] P<=0 0.14 | -812 [-3,343, +1,448] P<=0 0.74 |
| busy | vt_v3p_m0.02_any | 0 | e+25 | sl0 | 1,542.00 | 49.13 | -1.4 [-8.6, +5.6] | -545 [-3,172, +2,259] | +1,058 [-513, +3,146] P<=0 0.13 | -841 [-3,710, +1,905] P<=0 0.71 |
| busy | vt_v3p_m0.02_any | 0 | e+25 | sl1 | 2,310.00 | 50.39 | -1.5 [-7.2, +4.3] | -879 [-4,232, +2,599] | +724 [-232, +1,964] P<=0 0.09 | -1,175 [-4,649, +2,105] P<=0 0.74 |
| unseen | vt_v3p_m0.02_any | 0 | base | 60 | 1,884.05 | 51.49 | +5.7 [-0.8, +12.9] | +2,850 [-438, +6,461] |  |  |
| unseen | vt_v3p_m0.02_any | 0 | base | s20 | 1,937.98 | 18.99 | +6.7 [+0.2, +13.8] | +1,269 [+42, +2,627] | -1,581 [-3,783, +373] P<=0 0.94 | +268 [-1,004, +1,640] P<=0 0.35 |
| unseen | vt_v3p_m0.02_any | 0 | base | s40 | 1,907.00 | 36.11 | +6.1 [-0.4, +13.2] | +2,186 [-147, +4,728] | -664 [-1,736, +271] P<=0 0.91 | +1,186 [-1,064, +3,632] P<=0 0.17 |
| unseen | vt_v3p_m0.02_any | 0 | base | s100 | 1,851.92 | 78.29 | +5.0 [-1.7, +12.5] | +3,750 [-1,363, +9,539] | +900 [-784, +2,917] P<=0 0.19 | +2,750 [-1,960, +8,210] P<=0 0.15 |
| unseen | vt_v3p_m0.02_any | 0 | base | dk0.5 | 1,767.01 | 37.61 | +7.2 [-0.3, +16.0] | +2,389 [-93, +5,551] | -461 [-1,507, +542] P<=0 0.82 | +1,389 [-1,008, +4,323] P<=0 0.17 |
| unseen | vt_v3p_m0.02_any | 0 | base | dk1 | 1,863.39 | 42.58 | +6.7 [-0.4, +14.8] | +2,714 [-158, +6,148] | -136 [-760, +498] P<=0 0.68 | +1,714 [-962, +4,857] P<=0 0.13 |
| unseen | vt_v3p_m0.02_any | 0 | base | dk2 | 1,870.28 | 46.57 | +6.4 [-0.6, +14.3] | +2,857 [-260, +6,450] | +7 [-379, +447] P<=0 0.50 | +1,856 [-1,028, +5,143] P<=0 0.12 |
| unseen | vt_v3p_m0.02_any | 0 | base | rv1_30 | 1,921.91 | 31.17 | +7.6 [+0.8, +15.1] | +2,308 [+247, +4,681] | -542 [-1,892, +671] P<=0 0.80 | +1,307 [-723, +3,676] P<=0 0.12 |
| unseen | vt_v3p_m0.02_any | 0 | base | rv1_0 | 258.17 | 54.63 | +18.4 [+6.0, +34.0] | +1,110 [+340, +2,573] | -1,740 [-4,682, +931] P<=0 0.89 | +109 [-859, +1,548] P<=0 0.48 |
| unseen | vt_v3p_m0.02_any | 0 | base | rv3_30 | 1,915.03 | 36.68 | +7.4 [+0.8, +14.9] | +2,619 [+305, +5,420] | -230 [-1,423, +825] P<=0 0.64 | +1,619 [-655, +4,369] P<=0 0.09 |
| unseen | vt_v3p_m0.02_any | 0 | base | rv3_0 | 704.51 | 52.71 | +12.0 [+4.3, +23.3] | +2,047 [+672, +4,621] | -803 [-3,444, +1,547] P<=0 0.73 | +1,046 [-401, +3,421] P<=0 0.16 |
| unseen | vt_v3p_m0.02_any | 0 | base | dk1_rv1 | 1,888.64 | 27.93 | +8.4 [+1.2, +16.7] | +2,214 [+307, +4,543] | -636 [-2,141, +752] P<=0 0.81 | +1,213 [-668, +3,463] P<=0 0.12 |
| unseen | vt_v3p_m0.02_any | 0 | base | sl0 | 1,298.87 | 49.34 | +8.1 [-0.2, +17.5] | +2,642 [-45, +5,898] | -208 [-978, +580] P<=0 0.70 | +1,642 [-967, +4,783] P<=0 0.13 |
| unseen | vt_v3p_m0.02_any | 0 | base | sl1 | 1,631.62 | 50.32 | +6.7 [-0.4, +14.6] | +2,859 [-161, +6,307] | +9 [-395, +406] P<=0 0.49 | +1,858 [-1,028, +5,247] P<=0 0.12 |
| unseen | vt_v3p_m0.02_any | 0 | comp | 60 | 1,648.83 | 45.10 | +4.1 [-2.6, +11.7] | +1,588 [-1,042, +4,682] |  |  |
| unseen | vt_v3p_m0.02_any | 0 | comp | s20 | 1,722.26 | 17.99 | +5.4 [-1.1, +12.5] | +872 [-184, +2,091] | -717 [-2,504, +752] P<=0 0.79 | +332 [-755, +1,556] P<=0 0.30 |
| unseen | vt_v3p_m0.02_any | 0 | comp | s40 | 1,680.96 | 32.56 | +4.6 [-2.1, +11.9] | +1,302 [-614, +3,482] | -286 [-1,120, +371] P<=0 0.75 | +762 [-1,123, +2,908] P<=0 0.25 |
| unseen | vt_v3p_m0.02_any | 0 | comp | s100 | 1,617.85 | 64.87 | +3.3 [-3.1, +10.6] | +1,782 [-1,671, +6,056] | +194 [-662, +1,225] P<=0 0.38 | +1,243 [-1,994, +5,171] P<=0 0.27 |
| unseen | vt_v3p_m0.02_any | 0 | comp | dk0.5 | 1,549.00 | 34.95 | +6.1 [-1.8, +15.9] | +1,667 [-491, +4,546] | +79 [-549, +747] P<=0 0.41 | +1,128 [-930, +3,828] P<=0 0.19 |
| unseen | vt_v3p_m0.02_any | 0 | comp | dk1 | 1,622.44 | 38.62 | +5.4 [-2.0, +14.1] | +1,744 [-631, +4,639] | +156 [-251, +579] P<=0 0.23 | +1,205 [-1,000, +3,958] P<=0 0.19 |
| unseen | vt_v3p_m0.02_any | 0 | comp | dk2 | 1,637.35 | 41.40 | +5.0 [-2.2, +13.1] | +1,744 [-756, +4,760] | +156 [-102, +439] P<=0 0.13 | +1,204 [-1,114, +4,085] P<=0 0.20 |
| unseen | vt_v3p_m0.02_any | 0 | comp | rv1_30 | 1,697.02 | 28.73 | +6.3 [-1.0, +14.9] | +1,563 [-235, +3,814] | -25 [-935, +773] P<=0 0.52 | +1,023 [-750, +3,220] P<=0 0.16 |
| unseen | vt_v3p_m0.02_any | 0 | comp | rv1_0 | 234.07 | 49.54 | +18.7 [+3.8, +36.9] | +922 [+162, +2,392] | -666 [-2,805, +1,279] P<=0 0.73 | +382 [-538, +1,783] P<=0 0.31 |
| unseen | vt_v3p_m0.02_any | 0 | comp | rv3_30 | 1,688.99 | 33.35 | +5.9 [-1.1, +14.5] | +1,701 [-315, +4,322] | +113 [-663, +805] P<=0 0.35 | +1,161 [-778, +3,633] P<=0 0.16 |
| unseen | vt_v3p_m0.02_any | 0 | comp | rv3_0 | 615.01 | 48.26 | +10.4 [+1.5, +23.5] | +1,436 [+178, +3,830] | -152 [-1,998, +1,557] P<=0 0.56 | +897 [-427, +3,076] P<=0 0.21 |
| unseen | vt_v3p_m0.02_any | 0 | comp | dk1_rv1 | 1,664.89 | 26.03 | +7.4 [-0.3, +16.7] | +1,632 [-63, +3,876] | +44 [-984, +983] P<=0 0.47 | +1,092 [-560, +3,211] P<=0 0.13 |
| unseen | vt_v3p_m0.02_any | 0 | comp | sl0 | 1,134.79 | 41.68 | +6.5 [-2.7, +17.1] | +1,536 [-620, +4,266] | -52 [-620, +501] P<=0 0.58 | +996 [-1,090, +3,688] P<=0 0.23 |
| unseen | vt_v3p_m0.02_any | 0 | comp | sl1 | 1,423.94 | 42.94 | +5.5 [-2.2, +14.2] | +1,718 [-701, +4,619] | +130 [-219, +445] P<=0 0.21 | +1,178 [-1,110, +4,002] P<=0 0.20 |
| unseen | vt_v3p_m0.02_any | 0 | e+25 | 60 | 1,769.31 | 52.28 | +5.5 [-0.9, +12.6] | +2,642 [-456, +6,218] |  |  |
| unseen | vt_v3p_m0.02_any | 0 | e+25 | s20 | 1,827.82 | 19.06 | +6.5 [+0.1, +13.5] | +1,170 [+14, +2,478] | -1,472 [-3,647, +393] P<=0 0.93 | +370 [-822, +1,670] P<=0 0.29 |
| unseen | vt_v3p_m0.02_any | 0 | e+25 | s40 | 1,796.84 | 36.40 | +5.8 [-0.6, +12.9] | +1,974 [-184, +4,493] | -668 [-1,721, +225] P<=0 0.92 | +1,175 [-967, +3,531] P<=0 0.16 |
| unseen | vt_v3p_m0.02_any | 0 | e+25 | s100 | 1,739.47 | 79.94 | +4.9 [-1.8, +12.4] | +3,530 [-1,319, +9,088] | +888 [-773, +2,876] P<=0 0.17 | +2,731 [-1,754, +8,038] P<=0 0.14 |
| unseen | vt_v3p_m0.02_any | 0 | e+25 | dk0.5 | 1,659.16 | 37.97 | +6.9 [-0.8, +15.9] | +2,170 [-229, +5,256] | -472 [-1,502, +509] P<=0 0.83 | +1,371 [-902, +4,269] P<=0 0.16 |
| unseen | vt_v3p_m0.02_any | 0 | e+25 | dk1 | 1,749.80 | 42.91 | +6.4 [-0.7, +14.4] | +2,461 [-248, +5,678] | -181 [-841, +476] P<=0 0.72 | +1,662 [-867, +4,727] P<=0 0.12 |
| unseen | vt_v3p_m0.02_any | 0 | e+25 | dk2 | 1,762.42 | 46.87 | +6.2 [-0.6, +13.8] | +2,633 [-245, +6,054] | -9 [-439, +477] P<=0 0.53 | +1,833 [-869, +5,052] P<=0 0.11 |
| unseen | vt_v3p_m0.02_any | 0 | e+25 | rv1_30 | 1,809.47 | 31.37 | +7.3 [+0.4, +15.0] | +2,106 [+134, +4,429] | -536 [-1,812, +616] P<=0 0.81 | +1,307 [-648, +3,627] P<=0 0.11 |
| unseen | vt_v3p_m0.02_any | 0 | e+25 | rv1_0 | 250.14 | 53.83 | +18.1 [+5.0, +34.7] | +1,027 [+257, +2,522] | -1,616 [-4,374, +960] P<=0 0.88 | +227 [-729, +1,647] P<=0 0.40 |
| unseen | vt_v3p_m0.02_any | 0 | e+25 | rv3_30 | 1,802.58 | 36.88 | +7.0 [+0.5, +14.8] | +2,373 [+165, +5,180] | -269 [-1,381, +761] P<=0 0.69 | +1,574 [-611, +4,283] P<=0 0.09 |
| unseen | vt_v3p_m0.02_any | 0 | e+25 | rv3_0 | 656.32 | 53.23 | +11.5 [+3.2, +23.5] | +1,834 [+479, +4,412] | -808 [-3,293, +1,466] P<=0 0.75 | +1,034 [-392, +3,398] P<=0 0.17 |
| unseen | vt_v3p_m0.02_any | 0 | e+25 | dk1_rv1 | 1,771.60 | 28.11 | +8.1 [+0.8, +16.5] | +2,025 [+195, +4,312] | -618 [-2,062, +745] P<=0 0.81 | +1,225 [-581, +3,483] P<=0 0.11 |
| unseen | vt_v3p_m0.02_any | 0 | e+25 | sl0 | 1,230.02 | 50.05 | +7.9 [-0.6, +17.4] | +2,496 [-195, +5,689] | -147 [-826, +512] P<=0 0.68 | +1,696 [-925, +4,799] P<=0 0.12 |
| unseen | vt_v3p_m0.02_any | 0 | e+25 | sl1 | 1,535.24 | 51.03 | +6.5 [-0.9, +14.6] | +2,635 [-353, +5,951] | -7 [-374, +336] P<=0 0.52 | +1,835 [-1,060, +5,166] P<=0 0.12 |
