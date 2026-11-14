# Why the veto arm fails under the hold

## Bridge: paper to live-like

| step | $ traded/day | mk10 c/$ | $/day |
|---|---|---|---|
| paper bot log | 52,258.41 | 9.58 | 5,006.37 |
| replay at 150 ms (venue clock) | 35,090.87 | 3.44 | 1,208.38 |
| hold p10 | 28,055.02 | 1.76 | 493.81 |
| hold p50 | 26,854.22 | 0.84 | 226.79 |
| hold drawn (live distribution) | 26,830.31 | 0.30 | 81.04 |


## (a)-(c) by arm, 150 ms replay vs real hold

| set | orders | fill | dep_t med | dep_m med | survive % | >=60 sh survive % | pulled % of removed | inst mk filled c/$ | inst mk missed c/$ | ask drift p50 c | ask drift mean c | stale at t % |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| vt_v1_m0.02_trigger (paper) | 9890 | 0.4 | 215.0 | 0.0 | 44.9 | 31.1 | 96.3 | 6.9 | 16.8 | 3.0 | 4.3 | 33.8 |
| vt_v1_m0.02_trigger (real) | 9890 | 0.3 | 215.0 | 0.0 | 41.5 | 32.7 | 91.1 | 3.1 | 16.4 | 4.2 | 5.5 | 33.8 |
| vt_v1_m0.03_any (paper) | 5903 | 0.4 | 119.0 | 0.0 | 46.9 | 25.5 | 96.0 | 8.5 | 22.8 | 4.0 | 5.5 | 42.7 |
| vt_v1_m0.03_any (real) | 5903 | 0.2 | 119.0 | 0.0 | 41.2 | 26.6 | 90.6 | 2.6 | 22.1 | 5.7 | 6.9 | 42.7 |
| micf (paper) | 5267 | 0.2 | 0.0 | 0.0 | 65.1 | 18.2 | 91.7 | 5.1 | 21.5 | 7.0 | 8.0 | 72.3 |
| micf (real) | 5267 | 0.2 | 0.0 | 0.0 | 57.8 | 20.6 | 86.2 | 2.3 | 21.4 | 7.4 | 8.8 | 72.3 |


## Feed staleness at decision (veto)

| veto orders | n | paper $/day | paper c/$ | real-hold $/day | real-hold c/$ |
|---|---|---|---|---|---|
| venue ask = seen at t | 6543 | 3,172.9 | 8.2 | 181.2 | 0.8 |
| venue ask != seen at t (stale feed) | 3347 | 1,833.4 | 13.7 | -100.1 | -2.2 |


## (d) veto by model edge quintile

| bin | orders | fill | dep_t med | dep_m med | survive % | >=60 sh survive % | pulled % of removed | inst mk filled c/$ | inst mk missed c/$ | ask drift p50 c | ask drift mean c | stale at t % |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| (0.019, 0.0215] | 1978 | 0.4 | 222.0 | 0.0 | 46.2 | 39.3 | 91.0 | -0.9 | 11.9 | 3.7 | 4.5 | 35.7 |
| (0.0215, 0.0236] | 1978 | 0.4 | 235.0 | 0.0 | 45.3 | 38.7 | 90.5 | 3.8 | 12.2 | 3.7 | 4.7 | 35.2 |
| (0.0236, 0.0266] | 1978 | 0.3 | 232.7 | 0.0 | 43.6 | 34.5 | 91.0 | 1.7 | 14.4 | 4.0 | 5.0 | 32.5 |
| (0.0266, 0.0327] | 1978 | 0.3 | 220.0 | 0.0 | 37.5 | 29.2 | 91.4 | 3.6 | 16.4 | 4.6 | 5.6 | 31.1 |
| (0.0327, 0.204] | 1978 | 0.2 | 145.9 | 0.0 | 32.9 | 21.7 | 91.5 | 12.1 | 26.3 | 6.6 | 8.0 | 34.7 |


## (d) veto by perp 250 ms move quintile (signed)

| bin | orders | fill | dep_t med | dep_m med | survive % | >=60 sh survive % | pulled % of removed | inst mk filled c/$ | inst mk missed c/$ | ask drift p50 c | ask drift mean c | stale at t % |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 1978 | 0.4 | 349.5 | 0.0 | 44.5 | 38.6 | 91.1 | -0.5 | 12.4 | 3.5 | 4.3 | 18.1 |
| 1 | 1978 | 0.4 | 532.0 | 4.0 | 33.9 | 40.4 | 93.2 | 3.3 | 14.3 | 3.2 | 4.0 | 10.1 |
| 2 | 1978 | 0.3 | 257.0 | 0.0 | 38.3 | 30.5 | 90.3 | 4.7 | 15.5 | 4.5 | 5.6 | 25.3 |
| 3 | 1978 | 0.3 | 65.8 | 0.0 | 46.8 | 30.3 | 88.6 | 2.6 | 16.6 | 4.9 | 6.2 | 50.1 |
| 4 | 1978 | 0.2 | 0.0 | 0.0 | 54.2 | 23.6 | 88.2 | 7.5 | 21.7 | 6.1 | 7.7 | 65.6 |

