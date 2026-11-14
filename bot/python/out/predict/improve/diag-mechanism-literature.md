# Diagnostic: what the Polymarket 5m book does when Binance gets busy (phenomenon + literature)

Date 2026-10-12 (first pass 12:07, second pass 15:30 UTC). Code
`research/predict/improve/diag/mechanism-literature/` (runs as a directory; second pass in `race/`),
tables `data/out/predict/improve/diag-mechanism-literature/*.csv`, work files
`data/cache/predict/improve/mechanism-literature/`. Read only: no arm, model or pre-registration
changed; frozen `v1_L0` (570a9c1015c555c5) hash-checked and only read.

**Data:** allowed windows only (select, dev3, test3 run 1, ext). Market lists come from the frozen
runs' `markets-<tag>.csv`; every script asserts `max(start) < 1791744900`; hour files are opened by
explicit path only when they end at or before 18:55 UTC, so ext stops at the 17:50 market (36 of 48).
363 markets, 2,706 clean Binance events, 2,432 matched quiet placebos, 23,193 + 9,550 frozen-model
rows (unseen + select), 8,949 simulated fills of the deployed arms and micf.

**Unit:** an *event* is a Binance perp mid move that shifts Polymarket fair P(Up) by >= 1 c within
100 ms of our receipt (>= 1 s apart, >= 20 s left, venue mid 0.10-0.90). Clocks are venue clocks
(Binance T vs Polymarket ts). Our L = 0 order matches at T + feed lag + 150 ms (median ~270 ms).

## Answer

**No: Polymarket makers do not reprice faster when Binance is busy.** At a fixed stale-level size the
busy-minus-calm requote change is -12, -3 and +8 ms (small, mid, large levels), and stale quotes are
*more* likely to still rest at our match when busy (+7 pp). What collapses is the information in the
move, and the frozen model does not see it.

| perp msgs/s decile | events | level sh | requote ms [CI] | P(< 150 ms) | **alive at our L0 match** [CI] | ends: cancel / eaten | rival excess hazard /s | rival excess wave /s | value at seen price c | **our L0 value 1 s c** [CI] |
|---|---|---|---|---|---|---|---|---|---|---|
| D1 0-42 | 271 | 121 | 233 [216, 239] | 0.25 | 0.22 [0.17, 0.27] | 0.75 / 0.03 | +0.46 | +30.0 | +10.5 | **+4.6 [+3.0, +6.3]** |
| D2 42-60 | 272 | 142 | 232 [218, 241] | 0.24 | 0.18 [0.13, 0.22] | 0.80 / 0.03 | +0.68 | +29.0 | +8.3 | +2.6 [+1.6, +3.8] |
| D3 60-84 | 269 | 120 | 208 [191, 229] | 0.31 | 0.13 [0.09, 0.17] | 0.84 / 0.03 | +0.61 | +24.3 | +6.3 | +2.3 [+1.1, +3.5] |
| D4 84-112 | 271 | 115 | 227 [208, 237] | 0.27 | 0.21 [0.16, 0.26] | 0.79 / 0.01 | +0.28 | +21.4 | +5.1 | +1.5 [+0.2, +2.9] |
| D5 112-150 | 270 | 120 | 213 [195, 236] | 0.30 | 0.19 [0.14, 0.24] | 0.79 / 0.02 | +0.41 | +20.8 | +3.4 | -0.2 [-1.2, +0.7] |
| D6 150-200 | 271 | 115 | 233 [215, 242] | 0.27 | 0.23 [0.18, 0.27] | 0.76 / 0.01 | +0.52 | +21.8 | +2.4 | -0.5 [-1.2, +0.4] |
| D7 200-264 | 270 | 123 | 216 [201, 239] | 0.26 | 0.25 [0.20, 0.30] | 0.71 / 0.04 | +0.63 | +17.6 | +2.7 | -0.1 [-1.1, +1.0] |
| D8 264-355 | 271 | 114 | 217 [195, 235] | 0.27 | 0.24 [0.19, 0.30] | 0.70 / 0.06 | +0.81 | +17.4 | +2.2 | +0.0 [-0.9, +1.1] |
| D9 355-517 | 270 | 115 | 209 [182, 232] | 0.34 | 0.22 [0.17, 0.29] | 0.72 / 0.06 | +0.98 | +16.8 | +1.6 | -0.4 [-0.9, +0.3] |
| D10 517-2,100 | 271 | 87 | 197 [178, 244] | 0.35 | 0.27 [0.21, 0.32] | 0.68 / 0.06 | +0.98 | **+13.6** | +1.1 | **-0.9 [-1.6, -0.2]** |

Best level, no competition window, market-bootstrap CIs (`dec_requote_pmsg10.csv`,
`dec_race_pmsg10.csv`, `dec_value_pmsg10.csv`). *Eaten* = rival prints at or through the stale price
summed to >= 80% of the level. *Rival excess* = event minus matched placebo in the same decile: hazard
of the first stale-price print, and prints toward the move per second at 200-500 ms after T.

- **At fixed level size** (busy D8-10 minus calm D1-3, `calm_busy_by_size.csv`): requote -12 [-39, +10],
  -3 [-36, +21], +8 [+2, +20] ms; alive at our match +0.06 [0.00, +0.12], +0.08 [+0.01, +0.16],
  +0.09 [+0.01, +0.18]. Linear probability of alive: **+3.4 pp per log unit of msgs/s [+1.3, +5.7]**
  holding size, surprise and the previous event fixed (`memory_ols.csv`).
- **Busy response is bimodal:** ends < 150 ms rise 0.26 to 0.32 and quotes left > 1 s rise 0.05 to 0.12
  (`selection_alive_gone.csv`). Some makers get faster, more stop reacting.
- **The follower's own load is a different state:** in the top decile of Polymarket book messages
  requote falls to 178 ms [160, 200], 11% of levels are eaten and the rival excess hazard is +1.5/s
  (`dec_requote_pmupd10.csv`, `dec_race_pmupd10.csv`). Busy Binance is not a busy race; busy
  Polymarket is.
- **Rivals scale with surprise, makers do not:** prints toward the move at 200-500 ms go 18 to 34/s
  from the lowest to the highest surprise decile (move / 30 s fair churn; background 3-6/s), while
  requote time stays 197-235 ms with no trend (`dec_race_surprise.csv`, `dec_requote_surprise.csv`).

## Why a quiet-hours value model fails when busy: calibration by surprise

The frozen 1 s model on its own firing rows (pred >= 2 c), realized 1 s value over predicted, by perp
msgs/s and *surprise* = side-signed staleness in cents (perp microprice move since our book view last
changed) over the 30 s fair churn. Fixed round bin edges (`calib_busy_x_surprise.csv`,
`calib_select_busy_x_surprise.csv`):

| msgs/s | surprise | select rows | select real/pred | unseen rows | unseen real/pred | unseen real 1 s c [CI] |
|---|---|---|---|---|---|---|
| <= 100 | < 0.05 | 2,348 | 0.62 | 1,904 | 0.59 | +2.5 [-0.3, +5.2] |
| <= 100 | >= 0.5 | 1,690 | 1.76 | 5,429 | 1.34 | +9.6 [+6.9, +12.4] |
| 100-300 | < 0.05 | 1,031 | 0.69 | 3,048 | 0.39 | +1.5 [-0.1, +3.2] |
| 100-300 | >= 0.5 | 969 | 2.16 | 2,064 | 1.15 | +6.1 [+3.5, +9.3] |
| > 300 | < 0.05 | 544 | 0.58 | 2,811 | **0.05** | +0.2 [-0.8, +1.2] |
| > 300 | 0.05-0.5 | 915 | 2.86 | 1,990 | **0.22** | +0.9 [-0.6, +2.6] |
| > 300 | >= 0.5 | 57 | 3.71 | 52 | 3.28 | +20.9 [+6.9, +33.6] |

- **Low-surprise rows are over-predicted everywhere** (0.58-0.69 on select, 0.05-0.59 unseen). This
  part was visible on the selection window.
- **The busy collapse is a low- and mid-surprise collapse.** Busy rows with a real unpriced move still
  pay (52 rows, 3.3x), but busy hours rarely produce one: surprise and msgs/s correlate -0.43, and 34%
  of unseen rows have surprise < 0.05.
- **Select did not show the busy collapse** (busy mid-surprise 2.86x on Saturday vs 0.22x unseen), so a
  busy-specific rule cannot be selected on select. The 1 s taker's median fill has surprise ~0: it
  mostly trades the fair-value gap and the book's own repricing, the signals that fail when busy.

## Mechanisms that break a quiet-hours value model in busy hours

| # | mechanism | evidence here | feature or rule it implies | status |
|---|---|---|---|---|
| M1 | **Information dilution:** a 1 c move is a jump in a calm book and noise in a busy one | value at seen price +10.5 to +1.1 c across deciles; frozen model 0.05-0.22x on busy low/mid-surprise rows, 3.3x on busy high-surprise rows | surprise ratio; `dmic`/OFI over 30 s path length; event-time decays | measured; fix never tested (H1) |
| M2 | **Out-of-support regime:** train rarely saw busy Binance | `sigma` above the train p99 on 35% of ext rows; realized/pred 1.22 to 0.16 by msgs/s quintile (`calib_sigma.csv`, `calib_pmsg10.csv`) | busy hours in training; activity-conditional margin | measured (H6) |
| M3 | **The race is against the maker's cancel, not rival takers** (replaces the first pass's "rivals win more when busy") | ends: cancel 68-84%, eaten 1-6%; rival excess wave falls +30 to +13.6/s with activity; excess first-print hazard only +0.5 to +1.0/s | model the maker-cancel hazard against our match clock, not a rival race | measured |
| M4 | **Maker speed is a level (and weakly a maker) trait** | requote OLS: log level size +93 ms per SD; previous event alive in the same market raises alive now by 6 pp [+1.5, +10] at fixed size (`ols_lag_q.csv`, `memory_*.csv`) | touch size, level age, last event's survival in this market | measured (H2) |
| M5 | **Our feed goes stale (replay side)** | perp messages > 0.5 s late in 18-41% of some hours; compressed-backlog fills: 1 s taker L = 0 -0.4 (28 fills) vs +17.1 c/$ (`fills_compressed.csv`) | feed-health gate; Dublin's own lag in the paper logs | open, mixed (H7) |
| M6 | **The hold as a venue-wide last look, regime-dependent** | value at the seen price, alive minus gone: calm +1.8 c [-0.7, +4.5], busy -0.5 [-1.8, +0.7]; OLS alive x busy -2.1 c [-4.8, +0.3] (`selection_*.csv`) | survival-conditional target; alive-probability x regime | weak, CI crosses 0 (H8) |
| M7 | **Leader-busy is not follower-busy** | busy Binance: rival wave halves; busy Polymarket book: requote 178 ms, 11% eaten, rival hazard +1.5/s | Polymarket book message rate as a race-intensity input | measured (H5) |

**The deployed arms' fills on unseen windows** (dev3 + test3 run 1 + ext, 10 s markout c/$, market
bootstrap, split at a post hoc 313 msgs/s; `fills_busy.csv`): 1 s taker L = 0 **+18.8 [+9.2, +28.8]**
calm vs **+1.8 [-4.2, +8.0]** busy; veto L = 0 +15.8 vs +2.7; veto L = -40 +8.4 vs -0.3; micf L = 0 +8.0
vs -0.7. Busy fills are zero-edge, not losing. On select busy fills were not worse.

**Post hoc gates on the same fills** (`gates_posthoc_unseen.csv`, `gate_surprise.csv`; micf ungated
unless stated):

| gate | window | arm, L | fills | 10 s mk c/$ [CI] | $/day | gain vs micf $/day [CI] |
|---|---|---|---|---|---|---|
| none (frozen) | select | taker 1 s, 0 | 287 | +14.3 [+8.1, +23.8] | 2,082 | +1,266 [+303, +2,406] |
| surprise >= 0.05 | select | taker 1 s, 0 | 60 | +52.8 [+30.9, +84.9] | 979 | +163 [-505, +812] |
| none (frozen) | unseen | taker 1 s, 0 | 451 | +15.9 [+7.7, +24.6] | 1,861 | +835 [-130, +1,993] |
| surprise >= 0.05 | unseen | taker 1 s, 0 | 128 | +28.0 [+20.3, +36.7] | 882 | -144 [-512, +230] |
| msgs/s <= 313 | unseen | taker 1 s, 0 | 353 | +18.8 | 1,824 | +798 [-114, +1,947] |
| feed ok, micf gated too | unseen | veto, -40 | 1,432 | +6.7 | 2,496 | +1,028 [+619, +1,473] |
| none (frozen) | unseen | veto, -40 | 1,578 | +5.8 [+4.0, +8.1] | 2,424 | +854 [+395, +1,306] |
| surprise >= 0.05 | unseen | veto, -40 | 652 | +10.5 [+7.9, +13.4] | 2,001 | +431 [+69, +809] |

**No gate closes the L = 0 CI or raises $/day.** A surprise gate doubles to quadruples c/$ but drops
70-80% of fills, and low-surprise fills still earn on select. The signal belongs in sizing or in the
model, not in a filter.

## Literature and fidelity audit

**Where this venue diverges from the incumbents** (the divergence is the mechanism):

| venue feature | incumbent model | what we measure | mechanism it opens |
|---|---|---|---|
| **150 ms taker hold, cancels undelayed** | a taker-only delay protects makers and ends sniping (Baldauf-Mollner 2020; Brolley-Cimon 2020; Aldrich-Friedman 2023; Khapko-Zoican 2021) | only 24-35% of stale levels go within 150 ms; 13-27% still rest at our match; makers end 68-84% of stale levels, rivals eat 1-6% | the bump protects only the fastest third of makers; the race is taker vs maker cancel, so model the cancel hazard (M3, M4) |
| **The hold is a last look on every resting quote** | last look is a dealer's option (Cartea-Jaimungal-Walton 2019, MAFE, 10.1007/s11579-018-0218-3) | survivors richer than cancelled quotes in calm hours, poorer in busy hours (weak) | fill-conditional value whose sign flips with regime (M6) |
| **1 c tick, information per tick set by delta** | large-tick books: implicit spread, spread ~ volatility per trade (Dayri-Rosenbaum 2015; Wyart et al. 2008) | the same 1 c move carries +10.5 c of value in a calm book and +1.1 c in a busy one; levels shrink 121 to 87 sh | value per unit of surprise, not per cent (M1) |
| **Binary settlement (cents = delta x BTC bp)** | quotes and news in the same units | the arms earn in high *cents* churn (+33.8 c/$ top `cvol30` quintile) and nothing in high BTC message rate | condition on cents-space churn, not BTC activity |
| **Leader and follower load differ** | one market, one activity clock (Menkveld-Zoican 2017; Foucault-Kozhan-Tham 2017) | Binance-busy halves the rival wave; Polymarket-busy heats the race | separate leader and follower activity inputs (M7) |

**Verified sources** (DOI or arXiv id resolved this session through Crossref or arXiv):

| source | claim used | fit here |
|---|---|---|
| Budish, Cramton, Shim 2015, QJE 130(4), 10.1093/qje/qjv027; Aquilina, Budish, O'Neill 2022, QJE 137(1), 10.1093/qje/qjab032 (first pass) | symmetric races of 5-10 us worth ~half a tick | races here run 200-500 ms and the snipers' target is mostly cancelled first |
| Foucault, Kozhan, Tham 2017, RFS, 10.1093/rfs/hhw103 | toxic arbitrage on stale quotes after news | arbitrageurs here scale with surprise (18 to 34 prints/s), as their model implies |
| Menkveld, Zoican 2017, RFS, 10.1093/rfs/hhx006 | net effect of speed depends on the news-to-liquidity ratio | busy BTC raises the noise share of every move: M1 |
| Shkilko, Sokolov 2020, JF, 10.1111/jofi.12969 | removing fast traders' speed edge lowers adverse selection | the hold removes it only for makers slower than ~150 ms |
| Hasbrouck, Saar 2013, JFM, 10.1016/j.finmar.2013.05.003; Brogaard, Hagstromer, Norden, Riordan 2015, RFS, 10.1093/rfs/hhv045 | fast makers use speed to avoid adverse selection | only 25-35% of makers here are faster than the hold |
| Weller 2013, SSRN 10.2139/ssrn.2355825 | fast vs slow liquidity: speed specialises by role | large levels are slow (+93 ms per SD of log size): slow liquidity is the prey |
| Corwin, Coughenour 2008, JF, 10.1111/j.1540-6261.2008.01420.x | limited attention degrades liquidity in busy periods | no slower median requote; partial support at the margin (+7 pp alive when busy) |
| Easley, Lopez de Prado, O'Hara 2012, RFS, 10.1093/rfs/hhs053; Andersen, Bondarenko 2014, JFM, 10.1016/j.finmar.2013.05.005 | VPIN toxicity; critique: it tracks trade intensity | raw "ended by a trade" (0.36 to 0.54) was mostly background; use excess over placebo |
| Ane, Geman 2000, JF, 10.1111/0022-1082.00286 | returns are near normal in transaction time | event-time decays for M1 |
| Moallemi, Saglam 2013, OR, 10.1287/opre.2013.1165; Cartea, Sanchez-Betancourt 2021, SIFIN, 10.1137/19m1258888 | latency cost grows with volatility; latency-optimal taker limit | fixed +2 c limit and 3 c margin ignore state |
| Rothschild, Sethi 2016, J. Prediction Markets, 10.5750/jpm.v10i1.1179 | prediction-market trader ecology (Intrade) | human-scale; no ms maker behaviour, no source venue |
| Dubach 2026, arXiv 2604.24366 | Polymarket stylized facts; feed-inferred trade direction matches on-chain ~59% | our `last_trade_price` side matches a book-price test on **90%** of prints, 78% by size (`trade_side_check.csv`): usable, attenuates direction counts ~20% |
| Chen, Long, Su 2026, arXiv 2609.17902 | "ghost fills": off-chain matches invalidated on-chain after price moves | realized fill rate may fall with move size; paper/live fills only |

**Shared omission.** Every incumbent values a stale quote as a function of the source move and of the
speed gap. None conditions on the move's surprise relative to the follower's own recent churn, and none
models the maker's cancel hazard against a fixed taker delay. Here the rival takers already price
surprise, the makers do not (their speed is set by level size), and the frozen model does neither. The
gap: **predict value per unit of surprise, against a maker-cancel clock, under a fixed taker hold.**

## Testable hypotheses

| id | hypothesis | test (clean protocol) | predicted effect |
|---|---|---|---|
| H1 | Surprise and event-time inputs fix the low-surprise over-prediction | retrain v1 on train with surprise (staleness c / 30 s churn), `dmic`/OFI over path length, per-N-message decays; check select calibration by msgs/s x surprise, then pre-register on post-run-3 data | low-surprise real/pred from ~0.6 toward 1; busy post-match AUC +0.02 |
| H2 | Maker-race inputs predict survival to the match | add touch size, level age, last event's survival and requote lag in this market; AUC of alive-at-match and post-match AUC | alive AUC above size-only; post-match AUC +0.01 |
| H3 | Surprise-scaled size beats a surprise gate | 60 sh base, 120-150 sh at surprise >= 0.25, chosen on select (+53 c/$ there), re-simulated with depth | $/day up at flat or higher c/$ |
| H4 | Low-surprise margin, selectable on select | margin 3 c / 0.6 = 5 c when surprise < 0.05 (0.58-0.69 shrink on select) | c/$ up, $/day about flat; busy low-surprise fills (unseen +1 c) mostly dropped |
| H5 | Polymarket's own message rate measures race intensity | add `pmupd10` (and prints in the last 0.3 s minus background) | markout of the top-tercile fills below half of the bottom tercile |
| H6 | Busy training data beats any rule | add busy weekday hours after the prereg2 segment; compare to frozen v1 on the next unseen block | busy slope from 0.5 toward 1 |
| H7 | Feed-health gate | receipt - T > 0.5 s or compression > 1.5, all arms incl. micf; read Dublin's own lag | veto L = -40 gain +854 to ~+1,028 (post hoc) |
| H8 | The last-look sign flip is real | re-measure alive minus gone value at the seen price by regime on new hours | alive x busy CI below 0 |

## Ideas and their status

| idea | status | premises / evidence |
|---|---|---|
| makers reprice faster when Binance is busy | **lost a comparison** (measured, no effect) | at fixed size -12 / -3 / +8 ms; survival to our match rises |
| rival takers win more of the race when busy (first pass M3) | **lost a comparison** (revised) | rival wave falls by half; 1-6% of levels eaten; the first pass counted partial and background prints |
| limited-attention makers (Corwin-Coughenour) | **open** | no median slowdown; +3.4 pp alive per log msgs/s at fixed size |
| msgs/s gate, side-signed staleness gate, surprise gate on the deployed arms | **lost a comparison** (post hoc) | c/$ up, $/day and gain down; surprise gate lost on select too |
| feed-health gate | **open, mixed** | post hoc; needs Dublin's own lag |
| surprise / event-time features, maker-race features, surprise-scaled size | **never tested** (H1-H3) | mechanism evidence only |
| sibling-market maker consensus (did the 15m book reprice on this move?) | **never tested** | the recorder subscribes to 5m books only |
| ghost-fill risk | **never tested** | needs paper or live fills |

## Caveats

- **Best level and post hoc.** Event values and calibration rows use the best level with no
  competition window; arm results come from the frozen simulator. dev3, test3 and ext were already
  test windows, so every split on them is a labelled look, not a claim. Select is the only window
  where a rule could legitimately be chosen.
- **Direction labels** are right on 90% of prints (78% by size); toward/against counts are attenuated.
  *Eaten* uses the level size at T and ignores refills, so it is a lower bound on trade consumption.
- **Recorder feed lag:** the Binance futures feed lagged > 0.5 s in parts of test3 13-14 UTC and ext
  15-16 UTC; part of the replayed busy-hour damage may be our recording.
- **Sample:** ext truncated to 36 of 48 markets; busy evidence is mostly one Sunday afternoon; busy
  high-surprise rows are 52 (unseen) and 57 (select).

## Reproduce

```
D=research/predict/improve/diag/mechanism-literature
OMP_NUM_THREADS=2 nice -n 10 python3 $D build        # events + placebos (~12 min)
OMP_NUM_THREADS=2 nice -n 10 python3 $D calib        # frozen v1_L0 rows, dev3 / test3r1 / ext (~7 min)
OMP_NUM_THREADS=2 nice -n 10 python3 $D calib --windows select --tag calib_select   # (~4 min)
OMP_NUM_THREADS=2 nice -n 10 python3 $D fills        # deployed arms' frozen fills + state (~3 min)
python3 $D analyze && python3 $D posthoc             # first-pass tables
OMP_NUM_THREADS=2 nice -n 10 python3 $D sidecheck    # trade-direction labels (48 markets)
python3 $D deciles && python3 $D surprise && python3 $D gate
```
