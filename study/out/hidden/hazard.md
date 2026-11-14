# When do they fire? 50 ms bins: 1,568,800 (test 567,100)

| features | AUC A | A fills in top-decile bins | AUC B | B fills in top decile |
|---|---|---|---|---|
| state | 0.807 | 0.44 | 0.798 | 0.40 |
| state + forensic spot | 0.810 | 0.44 | 0.805 | 0.43 |
| state + perp book | 0.936 | 0.83 | 0.915 | 0.73 |
| state + spot book | 0.913 | 0.74 | 0.890 | 0.64 |
| state + Binance book trigger | 0.940 | 0.84 | 0.922 | 0.74 |
| state + Polymarket flow | 0.852 | 0.53 | 0.828 | 0.48 |
| state + forensic + Binance book + Polymarket | 0.947 | 0.86 | 0.928 | 0.78 |
| Binance book trigger alone | 0.839 | 0.65 | 0.810 | 0.57 |

base rate A: 0.0019 per 50 ms bin

base rate B: 0.0037 per 50 ms bin
