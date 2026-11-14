# Other venues vs the Binance books (3.5 h of side-recorder data, 887 leader fills)

Side accuracy / coverage, trigger window (0.21-0.33 s before the print):

| feed | A all | A Binance-miss | B all | B Binance-miss |
|---|---|---|---|---|
| perp_micro | 0.774 / 0.89 | 0.344 / 0.80 | 0.722 / 0.87 | 0.296 / 0.77 |
| spot_micro | 0.725 / 0.72 | 0.237 / 0.68 | 0.711 / 0.71 | 0.284 / 0.65 |
| perp_flow | 0.809 / 0.30 | 0.773 / 0.20 | 0.765 / 0.27 | 0.585 / 0.20 |
| spot_flow | 0.767 / 0.25 | 0.607 / 0.25 | 0.701 / 0.26 | 0.483 / 0.23 |
| okx_micro | 0.687 / 0.85 | 0.483 / 0.79 | 0.715 / 0.83 | 0.587 / 0.77 |
| okx_flow | 0.657 / 0.24 | 0.480 / 0.22 | 0.608 / 0.22 | 0.438 / 0.18 |
| bybit_micro | 0.802 / 0.69 | 0.682 / 0.59 | 0.786 / 0.69 | 0.685 / 0.62 |
| bybit_flow | 0.780 / 0.20 | 0.529 / 0.15 | 0.688 / 0.18 | 0.600 / 0.17 |
| coinbase_micro | 0.671 / 0.24 | 0.692 / 0.23 | 0.654 / 0.22 | 0.603 / 0.26 |
| coinbase_flow | 0.629 / 0.24 | 0.615 / 0.23 | 0.602 / 0.22 | 0.574 / 0.26 |
- rule 'Binance only': A 0.797 / 0.77, B 0.738 / 0.76 (accuracy / coverage)
- rule 'Binance, else Bybit': A 0.789 / 0.90, B 0.726 / 0.92 (accuracy / coverage)
- rule 'Binance, else Bybit, else OKX': A 0.778 / 0.97, B 0.716 / 0.97 (accuracy / coverage)

Binance-miss fills (perp + spot book silent, split or opposite): A 0.382, B 0.441

Side AUC, out-of-fold by half hour:

| features | A | B |
|---|---|---|
| Binance books | 0.830 | 0.852 |
| other venues + perp trades | 0.831 | 0.830 |
| Binance + OKX | 0.829 | 0.866 |
| Binance + Bybit | 0.836 | 0.860 |
| Binance + Coinbase | 0.843 | 0.858 |
| Binance + perp trades | 0.847 | 0.854 |
| Bybit alone | 0.790 | 0.794 |
| Binance + other venues | 0.851 | 0.873 |

Impulse response to each venue's mid ticks (venue clocks):

| venue | who | ticks | peak lag ms | lift at peak |
|---|---|---|---|---|
| perp | A | 683 | 270 | 100x |
| perp | B | 683 | 260 | 68x |
| okx | A | 663 | 270 | 39x |
| okx | B | 663 | 260 | 32x |
| bybit | A | 1597 | 230 | 37x |
| bybit | B | 1597 | 210 | 21x |
| coinbase | A | 7659 | 250 | 7x |
| coinbase | B | 7659 | 200 | 4x |

Lead over the Binance perp (perp tick time minus venue tick time, same direction, |gap| < 0.5 s; positive = venue first):

- perp: matched 683, median 0 ms, p25 0, p75 0, venue first 0.00
- okx: matched 291, median 0 ms, p25 -20, p75 0, venue first 0.13
- bybit: matched 687, median -20 ms, p25 -60, p75 0, venue first 0.15
- coinbase: matched 338, median -50 ms, p25 -120, p75 0, venue first 0.17
