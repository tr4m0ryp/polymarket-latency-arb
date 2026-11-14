# How the BTC up/down latency bots execute

Source: `python3 research/execution.py` (stats in `research/exec_stats.py`).
Rows: the 80 wallet x family rows of the latency list (all 49 `latency_arb`, 18 `latency_arb_partial`
with |PnL| >= $100, 13 `momentum_taker` with PnL >= $2k or <= -$500). Full numbers per row:
`data/out/latency/execution.csv`; one tx-level example market per row: `data/out/latency/execution_cycles.csv`.
Window: the ~2 days of collected fills. All PnL in the YES frame, `q*(R - pi)`.

## TL;DR

**They are not arbitrageurs and they are not round-trippers. They are pure buyers that hold to resolution.**
38 of 49 `latency_arb` rows have zero SELL fills. They buy Up *and* Down in the same market (median
90% of markets), switching side every time the spot-implied fair value crosses the book, in fixed
share clips (60 shares for the four big 5m bots), one fill per transaction, mostly as taker. The
Up+Down pairs they accumulate cost **$1.00 at the median** (so no lock-in arbitrage), and the
round-trip leg loses money in aggregate: **-$24.6k round-trip vs +$270.2k held-to-resolution** across
the 49 `latency_arb` rows (+$245.6k total). The profit is the small net tilt (median 19% of gross
shares) that is left at the close, which ends up on the winning side more often than not.

## Method notes

- **PnL split (exact, average cost, per market).** With B YES-shares bought at average pb and S sold at
  average ps (buying Down at p = selling YES at 1-p), `pnl = min(B,S)*(ps-pb) + net*(R - entry)`.
  The first term is the round-trip / pair term (it is positive exactly when Up+Down pairs were bought
  for < $1), the second is what the residual position earned at resolution.
- **Up+Down cost** = VWAP of Up buys + VWAP of Down buys in a market where both were bought.
- **net/gross exposure** = |B - S| / (B + S) at the end of the market: 0 = fully hedged, 1 = one-sided.
- **net side right** = share of residual net shares that sat on the winning outcome.
- **edge** = sign(q) * (fair - pi) on taker fills, fair = spot-implied P(Up) under the real settlement rule.
- **rho(size, edge)** = Spearman correlation of taker-tx USD with that edge (does size scale with edge?).
- Merges/redemptions are not in the fill feed. A hedged pair pays $1 whether merged or held, so the split is unaffected.
- Fill `ts` is the Polygon block time, a few seconds after the off-chain match.

## Class-level facts

| | latency_arb (49) | latency_arb_partial (18) | momentum_taker (13) |
|---|---|---|---|
| PnL | +$245.6k | +$1.2k | +$57.6k |
| round-trip / pair PnL | -$24.6k | +$2.1k | -$41.5k |
| held-to-resolution PnL | +$270.2k | -$0.9k | +$99.1k |
| taker / maker PnL | +$193.8k / +$51.7k | +$1.3k / -$0.1k | +$29.2k / +$28.3k |
| rows with zero SELLs | 38 | 14 | 13 |
| fills per tx (median) | 1.001 | 1.000 | 1.000 |
| taker USD share (median) | 77% | 100% | 76% |
| markets with Up and Down bought (median) | 90% | 87% | 51% |
| Up+Down cost (median of medians) | 1.000 | 0.966 | 1.135 |
| end net/gross exposure (median) | 0.19 | 0.26 | 1.00 |
| taker USD with positive spot edge (median) | 62% | 58% | 76% |
| rho(size, edge) / rho(size, 3 s BTC move) | +0.14 / -0.01 | +0.15 / +0.03 | +0.02 / -0.03 |
| UTC hours with > 1% of USD (median) | 24 | 23 | 23 |

`latency_arb` by family (PnL / round-trip / held): 5m +$64.0k / +$19.8k / +$44.1k; 15m +$47.6k / -$10.9k / +$58.5k;
hourly +$31.5k / -$13.2k / +$44.7k; 4h +$20.8k / -$16.0k / +$36.9k; daily +$81.7k / -$4.3k / +$85.9k.
5m is the only family where the pair term is positive, and that is driven by two wallets
(0x3048d65321be3497164cdfc2996f94f98a2e7537 +$9.4k, 0x576b0696fd5a9225d66fd9500fd98f5be10b0cab +$10.7k).

**Order size: fixed clips, weak edge scaling.** Size is uncorrelated with the size of the BTC move
(median rho -0.01) and only weakly with model edge (+0.14). Each bot has a signature clip:
60 shares (0xc53375ff94e96100f2b30a4b5775db35218d69a9 26% of fills, 0x3048d65321be3497164cdfc2996f94f98a2e7537 24%,
0x0ca4e9d27ff826a109ecbf74754fb66b93f277a6 21%, 0xd84403efd50b49a1d8a7181627e00307e6ea5908 22%, all 5m);
30 shares (0x41e2e1ccf1e4940029af02259a31c6b89b9fa354, 20% in 5m, 55% in 15m); 20 shares (0xb55fa1296e6ec55d0ce53d93b9237389f11764d4);
50 shares (0x576b0696fd5a9225d66fd9500fd98f5be10b0cab and 0xeebde7a0e019a63e6b476eb425505b7b3e6eba30 hourly, 37% each);
250 shares (0x32ed2e546b187ca15e2841edc82b22c713cf8ec3, 0x3725d52f3c252e8374999cc8617292ea2608ad88, 0xc2ad03f79ca3f3c17d8c7de2612ce0c89b7d40ed, 15m).
Partial clips (e.g. 54.1 of 60) appear when the top level is thinner than the clip. One fill per transaction
means each order takes a single resting level; they never sweep the book.

**Timing.** The 5m bots start ~5-14 s after the window opens (median first-fill t_rel 0.017-0.047),
spread USD evenly over the window, put 7-15% of USD in the last 60 s (the closing TWAP window), and
stop 25-34 s before close (p1 of secs_to_end). 15m bots start later (t_rel ~0.2 for the 250-share trio).
Hourly/4h/daily bots trade the whole window in dozens of bursts. Time of day: every large bot is active
in all 24 UTC hours; the top 3 hours carry 15-30% of USD (uniform = 12.5%), daily-market bots up to 45%.
Two days is too short to call that a schedule.

**Prices paid.** The 5m two-sided bots buy almost only in 0.30-0.70 (62-66% of buy USD) and
almost never above 0.90 (< 1%). The 0x576b0696fd5a9225d66fd9500fd98f5be10b0cab / 0xeebde7a0e019a63e6b476eb425505b7b3e6eba30 /
0x2ed94d1a460379292d2e3b46f2cf7d94b033f271 trio buys low (median buy price 0.18 and 0.29 for 0x576b0696fd5a9225d66fd9500fd98f5be10b0cab in 15m and 5m, ~0.40 in 4h) and spends 40-68% of 5m/15m USD above 0.90,
i.e. it buys both the cheap tail and the near-certain side.

## What one cycle looks like, per archetype

**A. 5m two-sided spot chaser** (0xc53375ff94e96100f2b30a4b5775db35218d69a9, 0x3048d65321be3497164cdfc2996f94f98a2e7537,
0x0ca4e9d27ff826a109ecbf74754fb66b93f277a6, 0xd84403efd50b49a1d8a7181627e00307e6ea5908; 0x41e2e1ccf1e4940029af02259a31c6b89b9fa354 is the same with 30-share
clips and half its 5m flow as maker). Every 300 s, in 569-575 of 576 markets: first order ~6 s after open; then
14-85 single-fill buys (median tx $8-13, p90 ~$40), 7-13 bursts, and 5-27 switches between Up and Down per market.
Each buy is the side whose ask sits below the spot-implied fair value (54-64% of taker USD has positive edge, median edge
+0.07 to +1.0 c). Nothing is sold. By the close the position is mostly hedged pairs bought at ~$1.00 plus a net tilt of 5-25% of gross shares (median per market).
That tilt is on the winner for 56-66% of shares and carries all the profit: 0xc53375ff94e96100f2b30a4b5775db35218d69a9 = -$0.2k pairs + $21.1k held.
Example (`execution_cycles.csv`, 0xc53375ff94e96100f2b30a4b5775db35218d69a9, Down won): buys 60 Up at 0.64, 100 Down at 0.38,
60 Up at 0.63 in the first 10 s; follows fair from 0.59 to 0.86 buying Up; at t_rel 0.55 BTC drops 2.6 bp in 3 s, fair falls
to 0.27 and it buys Down in 60- and 100-share clips; flips back to Up on a +1.5 bp tick, then finishes on Down at 0.75-0.77.

**B. 15m slow both-sider** (0x32ed2e546b187ca15e2841edc82b22c713cf8ec3, 0x3725d52f3c252e8374999cc8617292ea2608ad88, 0xc2ad03f79ca3f3c17d8c7de2612ce0c89b7d40ed).
Three near-identical fingerprints: 8-9 fills per market, first fill at t_rel 0.20-0.22, 4-5 bursts, 1-2 side flips,
40% taker / 60% maker, 250-share clips alongside 5-share probes, Up+Down cost 0.975-1.011. PnL is half maker, half taker,
and half pairs, half held. They look like one operator running one configuration on three wallets
(identical parameters only, no on-chain link checked here).

**C. Long-horizon accumulator** (0x06dc51826bc524d9a83770e7de9dd7e005b04524 daily, 0xb55fa1296e6ec55d0ce53d93b9237389f11764d4 4h/hourly/15m,
0x9d57c42e847173d06841703825d3fe2299e456ea hourly, 0xdc3f46236700a2c7e89e2b952a123cd757ad4fa0 hourly). 60-130 fills per market across the whole window,
35-80 bursts, still pure buyers of both sides. The tilt grows as the window ages: 0x06dc51826bc524d9a83770e7de9dd7e005b04524 puts 36% of USD in the last
10% of the daily window, buys 62% of USD at >= 0.70, and its net position is right on 85% of shares; -$2.1k pairs, +$79.3k held.
0xb55fa1296e6ec55d0ce53d93b9237389f11764d4 is right on 76-87% of net shares and loses $44.6k on pairs across 4h/hourly/15m, which its tilt more than repays.
0x9d57c42e847173d06841703825d3fe2299e456ea hourly is the exception: its profit is pairs bought under $1 (median 0.950, 63% of markets < $1) and maker fills (+$9.1k),
with the tilt flat (-$0.1k).

**D. Cheap-tail pair builder** (0x576b0696fd5a9225d66fd9500fd98f5be10b0cab, 0xeebde7a0e019a63e6b476eb425505b7b3e6eba30, 0x2ed94d1a460379292d2e3b46f2cf7d94b033f271).
Buys the cheap side heavily, often from a resting order, and later the near-certain side, so pairs come in under $1
(median 0.85-0.89 in 5m and 4h, 76-79% of markets < $1). This is the one group where round-trip/pair PnL is the engine:
0x576b0696fd5a9225d66fd9500fd98f5be10b0cab 5m +$10.7k pairs vs -$8.9k held. Tilt hit rate is poor (34-43% in 4h and 5m).

**E. Pre-open strike sniper** (0x3089fcf3fe5b67ec287654b4d627bcd1d51135e4, 5m). 11 taker fills per market, 91% of USD in the 60 s strike-TWAP window
before the 5m market opens, at 0.50-0.70 (77%). Stops at the open and holds. Example: buys Up at 0.51 on a +1-2 bp tick, Down at 0.48-0.49
when it fades, Up at 0.54-0.59 on a +2.6 bp tick 1 s before open.

**F. Late certainty buyers (not latency).** 0xb1d30490fa2ec8dc55591e8c71d3d64b6e0fc279 buys only at >= 0.90 (100% of USD) after t_rel 0.25,
one side per market, 98-99% of markets won, $49 median tx. 0x44832d0d2ec11187c1e77d786feb15f6a50254c6 trades only the last 60 s of 15m markets at 0.70-0.99, 91% won.
Both pass the spot gate because the side they pick agrees with the latest move, but the cycle is "wait until settled, buy the
favourite", not latency.

**G. True round-trippers (minority).** Only 11 `latency_arb` rows sell at all. Those with > 10% SELL USD:
0x726fd4fd2d3f3a48fcbd54d1cecdd933d207d8e7 daily (13%, +$5.8k of its +$6.8k from round-trips), 0xa42f127d7e8df9f16881ffcc9ed0bc0326875f5a daily (45%),
0xe349bbbc5c179ed7f8f13ab5502381980f532147 and 0xc6accd5b5f647aacb751b8f3e9d640e723733778 15m (37-40%, 80-share clips), 0x5078f57065a338bd58065e76f02a9f9f5dd28082 hourly (47%),
0xfac01d79eb5d273ab0cbd3f8fd46a5da204584c8 15m (54%), 0x8b066217c8c3294a989ca9330e94d9c0810e8d91 hourly (46%, +$4.6k round-trip, -$4.0k held),
0x8320b90db15e5b777e5a023b5ba3cfa214d4904e daily (29%, -$4.2k total). All are small next to the hold-to-resolution bots.

## Answer: where the profit comes from

Holding. The bots pay roughly a full spread to build hedged Up+Down inventory as fair value oscillates, and that leg is
break-even to negative (-$24.6k across `latency_arb`). What pays is the last direction they leaned before the window
closed, because their last fills react to the newest spot move while the book is still stale. That residual is what a
copy trader would need to replicate, and it is set in the final third of the window (5m bots: last fill 25-34 s before close),
which is also why copying with a 2 s delay keeps so little.

## Tables (top 30 rows by PnL; full set in execution.csv)

### PnL split
| wallet | fam | class | mkts | PnL $ | round-trip $ | held-to-resolution $ | taker PnL $ | maker PnL $ | mkts won |
|---|---|---|---|---|---|---|---|---|---|
| `0x06dc51826bc524d9a83770e7de9dd7e005b04524` | daily | arb | 44 | 77,147 | -2,140 | 79,287 | 64,546 | 12,601 | 70% |
| `0x55be7aa03ecfbe37aa5460db791205f7ac9ddca3` | daily | mom | 21 | 25,977 | -14,243 | 40,220 | 18,078 | 7,899 | 62% |
| `0xc53375ff94e96100f2b30a4b5775db35218d69a9` | 5m | arb | 571 | 20,857 | -204 | 21,060 | 17,479 | 3,377 | 61% |
| `0x3048d65321be3497164cdfc2996f94f98a2e7537` | 5m | arb | 571 | 20,746 | 9,396 | 11,350 | 16,634 | 4,113 | 58% |
| `0xb55fa1296e6ec55d0ce53d93b9237389f11764d4` | 4h | arb | 116 | 15,755 | -24,868 | 40,623 | 12,159 | 3,596 | 66% |
| `0xcc500cbcc8b7cf5bd21975ebbea34f21b5644c82` | 4h | mom | 88 | 11,941 | -14,196 | 26,137 | 6,613 | 5,328 | 67% |
| `0x32ed2e546b187ca15e2841edc82b22c713cf8ec3` | 15m | arb | 349 | 9,805 | 5,117 | 4,688 | 5,946 | 3,859 | 52% |
| `0x3725d52f3c252e8374999cc8617292ea2608ad88` | 15m | arb | 332 | 9,687 | 473 | 9,214 | 4,869 | 4,818 | 51% |
| `0xb55fa1296e6ec55d0ce53d93b9237389f11764d4` | hourly | arb | 216 | 9,067 | -12,556 | 21,623 | 7,328 | 1,739 | 62% |
| `0xb55fa1296e6ec55d0ce53d93b9237389f11764d4` | 15m | arb | 251 | 8,944 | -7,174 | 16,117 | 8,379 | 565 | 62% |
| `0xc2ad03f79ca3f3c17d8c7de2612ce0c89b7d40ed` | 15m | arb | 339 | 8,584 | 4,679 | 3,905 | 5,086 | 3,497 | 50% |
| `0x9d57c42e847173d06841703825d3fe2299e456ea` | hourly | arb | 202 | 8,527 | 8,594 | -67 | -534 | 9,061 | 56% |
| `0x41e2e1ccf1e4940029af02259a31c6b89b9fa354` | 5m | arb | 575 | 7,906 | 1,698 | 6,209 | 5,474 | 2,433 | 59% |
| `0x0ca4e9d27ff826a109ecbf74754fb66b93f277a6` | 5m | arb | 569 | 7,777 | -1,288 | 9,065 | 6,514 | 1,264 | 52% |
| `0xb1d30490fa2ec8dc55591e8c71d3d64b6e0fc279` | 5m | mom | 322 | 7,198 | -7 | 7,205 | 4,015 | 3,183 | 98% |
| `0x726fd4fd2d3f3a48fcbd54d1cecdd933d207d8e7` | daily | arb | 45 | 6,793 | 5,776 | 1,017 | 5,965 | 828 | 78% |
| `0xdc3f46236700a2c7e89e2b952a123cd757ad4fa0` | hourly | arb | 240 | 5,106 | -4,430 | 9,537 | 4,707 | 400 | 67% |
| `0xeebde7a0e019a63e6b476eb425505b7b3e6eba30` | 5m | mom | 562 | 3,986 | -648 | 4,634 | 2,465 | 1,521 | 54% |
| `0xd84403efd50b49a1d8a7181627e00307e6ea5908` | 5m | arb | 561 | 3,894 | -1,928 | 5,822 | 2,312 | 1,581 | 56% |
| `0x21f4c1a1be34a39a7bc20985df4b7e5a39fb691d` | 15m | arb | 347 | 3,806 | -16,677 | 20,483 | 3,089 | 717 | 61% |
| `0xb1d30490fa2ec8dc55591e8c71d3d64b6e0fc279` | 15m | mom | 263 | 3,781 | -627 | 4,408 | 2,128 | 1,652 | 99% |
| `0x576b0696fd5a9225d66fd9500fd98f5be10b0cab` | hourly | arb | 238 | 3,762 | -2,176 | 5,938 | 1,994 | 1,769 | 58% |
| `0x2ed94d1a460379292d2e3b46f2cf7d94b033f271` | 15m | mom | 373 | 3,438 | 87 | 3,351 | 3,102 | 336 | 54% |
| `0x576b0696fd5a9225d66fd9500fd98f5be10b0cab` | 15m | mom | 383 | 2,595 | 3,774 | -1,180 | 1,390 | 1,204 | 49% |
| `0x41e2e1ccf1e4940029af02259a31c6b89b9fa354` | 15m | arb | 381 | 2,326 | 2,224 | 102 | 2,326 | 0 | 64% |
| `0x3089fcf3fe5b67ec287654b4d627bcd1d51135e4` | 5m | mom | 493 | 2,291 | -1,001 | 3,293 | 2,291 | 0 | 56% |
| `0x129246beaac356e104c397f0985c11b7469be5a6` | 5m | mom | 356 | 2,233 | 279 | 1,954 | 2,218 | 15 | 55% |
| `0x44832d0d2ec11187c1e77d786feb15f6a50254c6` | 15m | mom | 96 | 2,021 | -615 | 2,636 | 1,797 | 223 | 91% |
| `0x9d57c42e847173d06841703825d3fe2299e456ea` | 15m | arb | 347 | 1,999 | 3,625 | -1,626 | 2,855 | -856 | 52% |
| `0x2ed94d1a460379292d2e3b46f2cf7d94b033f271` | 4h | arb | 113 | 1,897 | 3,097 | -1,199 | 1,994 | -96 | 50% |

### Order mechanics

| wallet | fam | fills/mkt | fills/tx | tx $ p50 / p90 | top sizes (shares:share of fills) | taker USD | SELL USD | rho(size, edge) |
|---|---|---|---|---|---|---|---|---|
| `0x06dc51826bc524d9a83770e7de9dd7e005b04524` | daily | 107 | 1.00 | 39.0 / 427 | 100:0.03;20:0.03;40:0.02 | 66% | 0% | +0.02 |
| `0x55be7aa03ecfbe37aa5460db791205f7ac9ddca3` | daily | 46 | 1.00 | 28.2 / 732 | 5:0.07;20:0.05;10:0.04 | 75% | 0% | -0.01 |
| `0xc53375ff94e96100f2b30a4b5775db35218d69a9` | 5m | 42 | 1.00 | 10.8 / 40 | 60:0.26;5:0.10;100:0.04 | 87% | 0% | +0.13 |
| `0x3048d65321be3497164cdfc2996f94f98a2e7537` | 5m | 85 | 1.00 | 7.9 / 37 | 60:0.24;5:0.10;10:0.04 | 84% | 0% | +0.14 |
| `0xb55fa1296e6ec55d0ce53d93b9237389f11764d4` | 4h | 115 | 1.00 | 12.3 / 47 | 20:0.22;10:0.06;5:0.05 | 92% | 0% | +0.16 |
| `0xcc500cbcc8b7cf5bd21975ebbea34f21b5644c82` | 4h | 15 | 1.00 | 6.3 / 142 | 5:0.10;20:0.05;10:0.04 | 39% | 0% | -0.10 |
| `0x32ed2e546b187ca15e2841edc82b22c713cf8ec3` | 15m | 9 | 1.00 | 10.3 / 99 | 5:0.06;250:0.06;10:0.03 | 40% | 0% | +0.11 |
| `0x3725d52f3c252e8374999cc8617292ea2608ad88` | 15m | 8 | 1.00 | 13.7 / 123 | 250:0.08;5:0.06;10:0.03 | 40% | 0% | +0.12 |
| `0xb55fa1296e6ec55d0ce53d93b9237389f11764d4` | hourly | 62 | 1.00 | 15.7 / 82 | 50:0.07;20:0.07;5:0.03 | 56% | 0% | +0.14 |
| `0xb55fa1296e6ec55d0ce53d93b9237389f11764d4` | 15m | 23 | 1.00 | 20.2 / 117 | 5:0.06;10:0.04;20:0.03 | 95% | 0% | +0.15 |
| `0xc2ad03f79ca3f3c17d8c7de2612ce0c89b7d40ed` | 15m | 8 | 1.00 | 11.1 / 106 | 250:0.07;5:0.06;60:0.02 | 39% | 0% | +0.12 |
| `0x9d57c42e847173d06841703825d3fe2299e456ea` | hourly | 82 | 1.19 | 12.7 / 81 | 120:0.18;40:0.11;80:0.04 | 54% | 0% | +0.24 |
| `0x41e2e1ccf1e4940029af02259a31c6b89b9fa354` | 5m | 78 | 1.00 | 4.2 / 27 | 30:0.20;5:0.07;100:0.05 | 50% | 0% | +0.19 |
| `0x0ca4e9d27ff826a109ecbf74754fb66b93f277a6` | 5m | 24 | 1.00 | 11.4 / 45 | 60:0.21;5:0.10;100:0.10 | 88% | 0% | +0.11 |
| `0xb1d30490fa2ec8dc55591e8c71d3d64b6e0fc279` | 5m | 6 | 1.00 | 49.0 / 357 | 0.1:0.04;100:0.04;5:0.04 | 49% | 0% | -0.06 |
| `0x726fd4fd2d3f3a48fcbd54d1cecdd933d207d8e7` | daily | 51 | 1.00 | 10.0 / 106 | 300:0.11;100:0.09;200:0.08 | 59% | 13% | -0.00 |
| `0xdc3f46236700a2c7e89e2b952a123cd757ad4fa0` | hourly | 132 | 1.03 | 10.6 / 32 | 56:0.15;22.4:0.11;42:0.10 | 38% | 0% | +0.25 |
| `0xeebde7a0e019a63e6b476eb425505b7b3e6eba30` | 5m | 9 | 1.00 | 8.9 / 50 | 5:0.06;40:0.03;10:0.03 | 66% | 0% | +0.22 |
| `0xd84403efd50b49a1d8a7181627e00307e6ea5908` | 5m | 14 | 1.00 | 13.0 / 47 | 60:0.22;100:0.11;5:0.09 | 88% | 0% | +0.10 |
| `0x21f4c1a1be34a39a7bc20985df4b7e5a39fb691d` | 15m | 50 | 1.04 | 10.1 / 41 | 50:0.15;5:0.09;10:0.04 | 73% | 0% | +0.25 |
| `0xb1d30490fa2ec8dc55591e8c71d3d64b6e0fc279` | 15m | 8 | 1.00 | 32.7 / 196 | 10:0.05;5:0.04;20:0.03 | 43% | 0% | -0.08 |
| `0x576b0696fd5a9225d66fd9500fd98f5be10b0cab` | hourly | 79 | 1.01 | 12.0 / 32 | 50:0.37;5:0.08;20:0.07 | 78% | 0% | +0.26 |
| `0x2ed94d1a460379292d2e3b46f2cf7d94b033f271` | 15m | 7 | 1.00 | 10.0 / 64 | 24:0.10;25:0.06;5:0.06 | 78% | 0% | +0.28 |
| `0x576b0696fd5a9225d66fd9500fd98f5be10b0cab` | 15m | 14 | 1.02 | 2.6 / 38 | 5:0.26;24:0.04;25:0.03 | 72% | 0% | +0.26 |
| `0x41e2e1ccf1e4940029af02259a31c6b89b9fa354` | 15m | 19 | 1.00 | 8.4 / 25 | 30:0.55;5:0.10;10:0.05 | 100% | 0% | +0.37 |
| `0x3089fcf3fe5b67ec287654b4d627bcd1d51135e4` | 5m | 11 | 1.00 | 8.1 / 29 | 5:0.07;10:0.05;15:0.01 | 100% | 0% | -0.00 |
| `0x129246beaac356e104c397f0985c11b7469be5a6` | 5m | 1 | 1.00 | 29.5 / 52 | 60:0.30;50:0.27;80:0.21 | 100% | 0% | +0.10 |
| `0x44832d0d2ec11187c1e77d786feb15f6a50254c6` | 15m | 16 | 1.00 | 5.5 / 12 | 5:0.24;6:0.17;7:0.10 | 76% | 0% | +0.01 |
| `0x9d57c42e847173d06841703825d3fe2299e456ea` | 15m | 22 | 1.12 | 6.4 / 44 | 20:0.26;60:0.20;40:0.08 | 68% | 0% | +0.35 |
| `0x2ed94d1a460379292d2e3b46f2cf7d94b033f271` | 4h | 23 | 1.00 | 5.0 / 17 | 5:0.20;50:0.10;10:0.08 | 95% | 0% | -0.00 |

### Both sides, hedging and residual

| wallet | fam | mkts both sides | Up+Down cost med | pairs < $1 | net/gross exp. med | net side right (shares-wtd) | bursts/mkt | side flips/mkt |
|---|---|---|---|---|---|---|---|---|
| `0x06dc51826bc524d9a83770e7de9dd7e005b04524` | daily | 100% | 0.999 | 50% | 0.19 | 85% | 81 | 11 |
| `0x55be7aa03ecfbe37aa5460db791205f7ac9ddca3` | daily | 90% | 1.135 | 21% | 0.64 | 91% | 40 | 4 |
| `0xc53375ff94e96100f2b30a4b5775db35218d69a9` | 5m | 99% | 1.001 | 50% | 0.15 | 66% | 11 | 14 |
| `0x3048d65321be3497164cdfc2996f94f98a2e7537` | 5m | 100% | 0.989 | 59% | 0.10 | 56% | 9 | 27 |
| `0xb55fa1296e6ec55d0ce53d93b9237389f11764d4` | 4h | 100% | 1.043 | 39% | 0.20 | 87% | 80 | 15 |
| `0xcc500cbcc8b7cf5bd21975ebbea34f21b5644c82` | 4h | 51% | 1.207 | 22% | 1.00 | 76% | 12 | 1 |
| `0x32ed2e546b187ca15e2841edc82b22c713cf8ec3` | 15m | 79% | 0.975 | 55% | 0.33 | 47% | 5 | 2 |
| `0x3725d52f3c252e8374999cc8617292ea2608ad88` | 15m | 79% | 1.011 | 47% | 0.38 | 53% | 5 | 1 |
| `0xb55fa1296e6ec55d0ce53d93b9237389f11764d4` | hourly | 98% | 1.018 | 48% | 0.09 | 80% | 35 | 8 |
| `0xb55fa1296e6ec55d0ce53d93b9237389f11764d4` | 15m | 87% | 1.026 | 45% | 0.20 | 76% | 14 | 3 |
| `0xc2ad03f79ca3f3c17d8c7de2612ce0c89b7d40ed` | 15m | 75% | 0.976 | 57% | 0.39 | 45% | 4 | 1 |
| `0x9d57c42e847173d06841703825d3fe2299e456ea` | hourly | 99% | 0.950 | 63% | 0.05 | 54% | 37 | 8 |
| `0x41e2e1ccf1e4940029af02259a31c6b89b9fa354` | 5m | 100% | 1.000 | 50% | 0.04 | 66% | 13 | 25 |
| `0x0ca4e9d27ff826a109ecbf74754fb66b93f277a6` | 5m | 96% | 0.999 | 50% | 0.20 | 57% | 9 | 8 |
| `0xb1d30490fa2ec8dc55591e8c71d3d64b6e0fc279` | 5m | 1% | 1.440 | 0% | 1.00 | 100% | 1 | 0 |
| `0x726fd4fd2d3f3a48fcbd54d1cecdd933d207d8e7` | daily | 96% | 0.844 | 81% | 0.13 | 7% | 40 | 6 |
| `0xdc3f46236700a2c7e89e2b952a123cd757ad4fa0` | hourly | 100% | 1.018 | 32% | 0.04 | 85% | 67 | 35 |
| `0xeebde7a0e019a63e6b476eb425505b7b3e6eba30` | 5m | 86% | 1.017 | 47% | 0.48 | 69% | 5 | 2 |
| `0xd84403efd50b49a1d8a7181627e00307e6ea5908` | 5m | 90% | 1.010 | 45% | 0.25 | 58% | 7 | 5 |
| `0x21f4c1a1be34a39a7bc20985df4b7e5a39fb691d` | 15m | 98% | 1.076 | 27% | 0.21 | 88% | 24 | 10 |
| `0xb1d30490fa2ec8dc55591e8c71d3d64b6e0fc279` | 15m | 1% | 1.930 | 0% | 1.00 | 100% | 2 | 0 |
| `0x576b0696fd5a9225d66fd9500fd98f5be10b0cab` | hourly | 100% | 1.011 | 39% | 0.11 | 63% | 60 | 31 |
| `0x2ed94d1a460379292d2e3b46f2cf7d94b033f271` | 15m | 84% | 0.973 | 56% | 0.61 | 74% | 6 | 2 |
| `0x576b0696fd5a9225d66fd9500fd98f5be10b0cab` | 15m | 89% | 0.859 | 70% | 0.61 | 68% | 9 | 3 |
| `0x41e2e1ccf1e4940029af02259a31c6b89b9fa354` | 15m | 98% | 0.979 | 67% | 0.07 | 44% | 16 | 11 |
| `0x3089fcf3fe5b67ec287654b4d627bcd1d51135e4` | 5m | 77% | 1.016 | 28% | 0.49 | 60% | 3 | 1 |
| `0x129246beaac356e104c397f0985c11b7469be5a6` | 5m | 48% | 0.996 | 51% | 1.00 | 40% | 1 | 0 |
| `0x44832d0d2ec11187c1e77d786feb15f6a50254c6` | 15m | 22% | 1.405 | 0% | 1.00 | 97% | 2 | 0 |
| `0x9d57c42e847173d06841703825d3fe2299e456ea` | 15m | 95% | 0.944 | 68% | 0.09 | 36% | 11 | 4 |
| `0x2ed94d1a460379292d2e3b46f2cf7d94b033f271` | 4h | 89% | 0.887 | 78% | 0.36 | 34% | 21 | 6 |

### Timing: USD share by t_rel bin, seconds to end

| wallet | fam | pre | 0-.1 | .1-.25 | .25-.5 | .5-.75 | .75-.9 | .9-1 | secs_to_end p1/p10/p50/p90 | first fill t_rel |
|---|---|---|---|---|---|---|---|---|---|---|
| `0x06dc51826bc524d9a83770e7de9dd7e005b04524` | daily | 0% | 8% | 5% | 8% | 22% | 19% | 36% | -7 / 1020 / 13861 / 69524 | 0.002 |
| `0x55be7aa03ecfbe37aa5460db791205f7ac9ddca3` | daily | 0% | 14% | 12% | 13% | 45% | 14% | 2% | 7950 / 19141 / 48553 / 84474 | 0.003 |
| `0xc53375ff94e96100f2b30a4b5775db35218d69a9` | 5m | 0% | 15% | 19% | 24% | 27% | 13% | 1% | 30 / 66 / 183 / 279 | 0.023 |
| `0x3048d65321be3497164cdfc2996f94f98a2e7537` | 5m | 0% | 16% | 19% | 27% | 26% | 11% | 1% | 34 / 78 / 193 / 280 | 0.017 |
| `0xb55fa1296e6ec55d0ce53d93b9237389f11764d4` | 4h | 0% | 11% | 13% | 22% | 20% | 19% | 15% | 87 / 795 / 5932 / 13010 | 0.003 |
| `0xcc500cbcc8b7cf5bd21975ebbea34f21b5644c82` | 4h | 0% | 10% | 24% | 21% | 19% | 14% | 12% | 100 / 380 / 5295 / 13047 | 0.071 |
| `0x32ed2e546b187ca15e2841edc82b22c713cf8ec3` | 15m | 0% | 8% | 10% | 19% | 26% | 26% | 12% | 22 / 80 / 364 / 806 | 0.200 |
| `0x3725d52f3c252e8374999cc8617292ea2608ad88` | 15m | 0% | 9% | 11% | 19% | 26% | 23% | 12% | 28 / 79 / 343 / 805 | 0.204 |
| `0xb55fa1296e6ec55d0ce53d93b9237389f11764d4` | hourly | 0% | 17% | 14% | 21% | 20% | 17% | 11% | 53 / 235 / 1626 / 3363 | 0.010 |
| `0xb55fa1296e6ec55d0ce53d93b9237389f11764d4` | 15m | 0% | 10% | 19% | 21% | 26% | 16% | 7% | 42 / 113 / 458 / 826 | 0.039 |
| `0xc2ad03f79ca3f3c17d8c7de2612ce0c89b7d40ed` | 15m | 0% | 7% | 9% | 19% | 28% | 25% | 12% | 32 / 69 / 316 / 812 | 0.222 |
| `0x9d57c42e847173d06841703825d3fe2299e456ea` | hourly | 0% | 15% | 14% | 25% | 28% | 12% | 6% | 56 / 412 / 1730 / 3353 | 0.029 |
| `0x41e2e1ccf1e4940029af02259a31c6b89b9fa354` | 5m | 0% | 7% | 15% | 28% | 32% | 16% | 2% | 25 / 62 / 170 / 271 | 0.043 |
| `0x0ca4e9d27ff826a109ecbf74754fb66b93f277a6` | 5m | 0% | 15% | 17% | 23% | 28% | 16% | 2% | 28 / 57 / 166 / 277 | 0.030 |
| `0xb1d30490fa2ec8dc55591e8c71d3d64b6e0fc279` | 5m | 0% | 0% | 2% | 13% | 41% | 22% | 16% | -35 / 7 / 84 / 162 | 0.740 |
| `0x726fd4fd2d3f3a48fcbd54d1cecdd933d207d8e7` | daily | 0% | 4% | 2% | 8% | 21% | 21% | 40% | -48 / 571 / 8704 / 47248 | 0.019 |
| `0xdc3f46236700a2c7e89e2b952a123cd757ad4fa0` | hourly | 0% | 14% | 13% | 22% | 25% | 15% | 11% | 19 / 268 / 1714 / 3359 | 0.003 |
| `0xeebde7a0e019a63e6b476eb425505b7b3e6eba30` | 5m | 6% | 8% | 11% | 19% | 30% | 18% | 6% | 10 / 58 / 184 / 288 | 0.020 |
| `0xd84403efd50b49a1d8a7181627e00307e6ea5908` | 5m | 0% | 13% | 15% | 22% | 28% | 19% | 2% | 25 / 54 / 153 / 275 | 0.047 |
| `0x21f4c1a1be34a39a7bc20985df4b7e5a39fb691d` | 15m | 0% | 12% | 20% | 26% | 25% | 12% | 6% | 26 / 107 / 493 / 838 | 0.012 |
| `0xb1d30490fa2ec8dc55591e8c71d3d64b6e0fc279` | 15m | 0% | 0% | 0% | 0% | 33% | 30% | 35% | -21 / 25 / 136 / 280 | 0.874 |
| `0x576b0696fd5a9225d66fd9500fd98f5be10b0cab` | hourly | 0% | 17% | 18% | 29% | 29% | 7% | 0% | 640 / 1013 / 2235 / 3392 | 0.004 |
| `0x2ed94d1a460379292d2e3b46f2cf7d94b033f271` | 15m | 4% | 6% | 6% | 7% | 32% | 32% | 12% | 58 / 111 / 460 / 885 | 0.018 |
| `0x576b0696fd5a9225d66fd9500fd98f5be10b0cab` | 15m | 3% | 5% | 5% | 9% | 28% | 37% | 13% | 20 / 58 / 265 / 817 | 0.038 |
| `0x41e2e1ccf1e4940029af02259a31c6b89b9fa354` | 15m | 0% | 4% | 9% | 19% | 29% | 29% | 10% | 39 / 95 / 316 / 743 | 0.074 |
| `0x3089fcf3fe5b67ec287654b4d627bcd1d51135e4` | 5m | 91% | 9% | 0% | 0% | 0% | 0% | 0% | 298 / 302 / 322 / 342 | -0.143 |
| `0x129246beaac356e104c397f0985c11b7469be5a6` | 5m | 0% | 6% | 11% | 21% | 33% | 29% | 1% | 32 / 52 / 124 / 250 | 0.368 |
| `0x44832d0d2ec11187c1e77d786feb15f6a50254c6` | 15m | 0% | 0% | 0% | 0% | 0% | 0% | 100% | 10 / 23 / 44 / 56 | 0.937 |
| `0x9d57c42e847173d06841703825d3fe2299e456ea` | 15m | 0% | 12% | 19% | 30% | 27% | 8% | 5% | 47 / 123 / 429 / 821 | 0.052 |
| `0x2ed94d1a460379292d2e3b46f2cf7d94b033f271` | 4h | 0% | 0% | 21% | 28% | 27% | 18% | 7% | 486 / 1473 / 6101 / 11461 | 0.149 |

### Prices paid (USD share of buys by price bin), edge and time of day

| wallet | fam | <.1 | .1-.3 | .3-.5 | .5-.7 | .7-.9 | >.9 | taker edge>0 | edge med c | BTC moved in 3 s | mo2/USD | hours >1% | top-3 hours share |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `0x06dc51826bc524d9a83770e7de9dd7e005b04524` | daily | 1% | 6% | 11% | 20% | 40% | 22% | 68% | +3.03 | 76% | +0.028 | 21 | 40% |
| `0x55be7aa03ecfbe37aa5460db791205f7ac9ddca3` | daily | 0% | 3% | 8% | 22% | 24% | 43% | 56% | +1.93 | 71% | +0.021 | 21 | 38% |
| `0xc53375ff94e96100f2b30a4b5775db35218d69a9` | 5m | 0% | 7% | 25% | 39% | 28% | 0% | 57% | +0.41 | 43% | +0.033 | 24 | 18% |
| `0x3048d65321be3497164cdfc2996f94f98a2e7537` | 5m | 0% | 8% | 25% | 37% | 29% | 0% | 58% | +0.56 | 39% | +0.030 | 24 | 18% |
| `0xb55fa1296e6ec55d0ce53d93b9237389f11764d4` | 4h | 0% | 5% | 12% | 44% | 35% | 5% | 63% | +2.01 | 60% | +0.001 | 24 | 26% |
| `0xcc500cbcc8b7cf5bd21975ebbea34f21b5644c82` | 4h | 0% | 1% | 10% | 33% | 41% | 15% | 76% | +3.00 | 71% | +0.025 | 19 | 29% |
| `0x32ed2e546b187ca15e2841edc82b22c713cf8ec3` | 15m | 1% | 10% | 22% | 22% | 30% | 16% | 60% | -0.77 | 36% | +0.018 | 24 | 29% |
| `0x3725d52f3c252e8374999cc8617292ea2608ad88` | 15m | 1% | 9% | 19% | 24% | 33% | 15% | 62% | +0.59 | 35% | +0.005 | 24 | 29% |
| `0xb55fa1296e6ec55d0ce53d93b9237389f11764d4` | hourly | 1% | 2% | 13% | 48% | 28% | 7% | 68% | +1.50 | 55% | +0.007 | 24 | 22% |
| `0xb55fa1296e6ec55d0ce53d93b9237389f11764d4` | 15m | 1% | 4% | 14% | 39% | 38% | 5% | 63% | +0.99 | 45% | +0.008 | 22 | 25% |
| `0xc2ad03f79ca3f3c17d8c7de2612ce0c89b7d40ed` | 15m | 1% | 10% | 22% | 21% | 29% | 16% | 60% | -0.98 | 40% | +0.010 | 24 | 29% |
| `0x9d57c42e847173d06841703825d3fe2299e456ea` | hourly | 1% | 5% | 16% | 24% | 25% | 30% | 68% | +0.82 | 60% | +0.006 | 24 | 28% |
| `0x41e2e1ccf1e4940029af02259a31c6b89b9fa354` | 5m | 1% | 8% | 15% | 22% | 35% | 19% | 64% | +1.01 | 29% | +0.019 | 24 | 15% |
| `0x0ca4e9d27ff826a109ecbf74754fb66b93f277a6` | 5m | 0% | 8% | 25% | 40% | 27% | 1% | 55% | +0.14 | 45% | +0.034 | 24 | 19% |
| `0xb1d30490fa2ec8dc55591e8c71d3d64b6e0fc279` | 5m | 0% | 0% | 0% | 0% | 0% | 100% | 95% | +1.00 | 47% | +0.000 | 23 | 31% |
| `0x726fd4fd2d3f3a48fcbd54d1cecdd933d207d8e7` | daily | 2% | 11% | 18% | 21% | 32% | 16% | 61% | +1.61 | 71% | +0.026 | 17 | 45% |
| `0xdc3f46236700a2c7e89e2b952a123cd757ad4fa0` | hourly | 0% | 6% | 24% | 37% | 24% | 9% | 65% | +0.98 | 55% | +0.015 | 24 | 16% |
| `0xeebde7a0e019a63e6b476eb425505b7b3e6eba30` | 5m | 1% | 6% | 11% | 18% | 18% | 46% | 76% | +0.99 | 45% | +0.020 | 24 | 21% |
| `0xd84403efd50b49a1d8a7181627e00307e6ea5908` | 5m | 0% | 7% | 25% | 40% | 27% | 1% | 54% | +0.07 | 47% | +0.028 | 24 | 19% |
| `0x21f4c1a1be34a39a7bc20985df4b7e5a39fb691d` | 15m | 1% | 4% | 12% | 24% | 34% | 25% | 73% | +2.03 | 53% | +0.006 | 24 | 21% |
| `0xb1d30490fa2ec8dc55591e8c71d3d64b6e0fc279` | 15m | 0% | 0% | 0% | 0% | 0% | 100% | 94% | +1.00 | 25% | +0.002 | 24 | 20% |
| `0x576b0696fd5a9225d66fd9500fd98f5be10b0cab` | hourly | 0% | 7% | 25% | 39% | 25% | 4% | 58% | -0.18 | 44% | +0.007 | 24 | 18% |
| `0x2ed94d1a460379292d2e3b46f2cf7d94b033f271` | 15m | 1% | 4% | 11% | 15% | 8% | 61% | 83% | +0.89 | 40% | +0.011 | 24 | 21% |
| `0x576b0696fd5a9225d66fd9500fd98f5be10b0cab` | 15m | 1% | 4% | 9% | 12% | 7% | 68% | 85% | +1.00 | 40% | +0.014 | 24 | 19% |
| `0x41e2e1ccf1e4940029af02259a31c6b89b9fa354` | 15m | 1% | 9% | 16% | 24% | 33% | 17% | 69% | +0.82 | 32% | +0.018 | 24 | 17% |
| `0x3089fcf3fe5b67ec287654b4d627bcd1d51135e4` | 5m | 0% | 0% | 22% | 77% | 1% | 0% | 66% | +1.34 | 66% | +0.020 | 23 | 18% |
| `0x129246beaac356e104c397f0985c11b7469be5a6` | 5m | 1% | 7% | 27% | 51% | 15% | 0% | 45% | -2.04 | 50% | +0.059 | 24 | 20% |
| `0x44832d0d2ec11187c1e77d786feb15f6a50254c6` | 15m | 0% | 1% | 3% | 9% | 41% | 46% | 77% | +7.70 | 20% | +0.034 | 19 | 41% |
| `0x9d57c42e847173d06841703825d3fe2299e456ea` | 15m | 1% | 6% | 13% | 14% | 30% | 36% | 72% | +1.21 | 57% | +0.008 | 24 | 20% |
| `0x2ed94d1a460379292d2e3b46f2cf7d94b033f271` | 4h | 0% | 15% | 38% | 23% | 17% | 6% | 47% | -0.73 | 71% | +0.012 | 24 | 19% |

