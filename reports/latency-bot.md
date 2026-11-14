# The BTC up/down latency bot: what it does, who runs it, can we build it

Data: Polymarket fills for the five BTC up/down families plus Binance BTCUSDT 1 s closes. Windows differ per family: **5m 2.0 days** (576 markets, 2026-10-07 to 10-09), **15m 4.0 days** (383), **hourly 10 days** (240), **4h 20 days** (120), **daily 45 days** (45). Studies behind this report: `data/out/latency/{trigger,execution,peers,profit}.md`. All PnL is in the YES frame, `q*(R - pi)`. "Net" subtracts the taker fee (`C * 0.07 * p * (1-p)`, Gamma `crypto_fees_v2`) and adds back the wallet's measured taker-rebate tier and the estimated maker rebate. Fill times are Polygon block times (about 2 s blocks), so every latency number below is an upper bound on true reaction time.

## 1. Verdict

**It is a spot-to-book latency strategy, it is real in 5m, and it is simple to describe but hard to make pay.** The bot watches Binance BTC second by second and **takes the side of the latest 1-3 s Binance move** in small clips, about 2-3 s after the move in block time and about 1 s before the Polymarket book catches up. Whether it also compares a fair-value estimate with the book is **unverified**: the fair model measured here shows little or negative edge on the winners' fills (step 3). It almost never sells and ends each market holding both sides.
- **Totals (49 `latency_arb` rows):** **+$245.6k gross, +$172.5k net.** Taker fees equal **67% of gross before rebates**; after **$76.9k** of taker rebates and **$13.8k** of maker rebates the net cost is **30% of gross**.
- **How much of that is latency:** only **$109.8k (45%)** of gross is the 2 s markout (the book repricing toward the fill). **$84.0k** is hold-to-resolution residual, concentrated in 15m, 4h and daily, and **$51.7k** is maker PnL. In 5m the markout is $55.3k of $64.0k gross; in 4h it is $1.4k of $20.8k.
- **Best taker bot:** **0xc53375ff94e96100f2b30a4b5775db35218d69a9** (5m, **+$7.6k/day net**, t = 4.4).
- **Highest net per day, unexplained:** the 15m trio (0x32ed2e546b187ca15e2841edc82b22c713cf8ec3, 0x3725d52f3c252e8374999cc8617292ea2608ad88, 0xc2ad03f79ca3f3c17d8c7de2612ce0c89b7d40ed) nets about **+$12.8k/day** across all BTC families, but over 4 days, mostly as maker, with Down-regime exposure. Mechanism unknown; not a proven latency result.
- **"Most profitable" correction:** 0x06dc51826bc524d9a83770e7de9dd7e005b04524 (+$77.1k) earned that over **44 of the 45 daily markets (a 45-day window)**, which is **+$1.6k/day**, and two thirds of its taker PnL is hold, not markout.
- **What separates the two 5m leaders:** not the latency component. 0x3048d65321be3497164cdfc2996f94f98a2e7537 has the larger 2 s markout; 0xc53375ff94e96100f2b30a4b5775db35218d69a9 wins on post-2 s hold PnL in the blocks both trade (t = 2.3 over 564 markets, 2 days, possibly luck) and on lower solo fee drag (section 4).
- **Recreating it is hard (7/10):** the code is small, but the edge is a 1-3 s window shared by a median of 4 rival bots per burst, the stale liquidity per block appears small (inferred, not measured), and a new wallet starts at the 0% rebate tier, where most of the incumbents' edge disappears.

## 2. What the bot does: the decision rule

The rule below is reconstructed from fills, not from code, and is measured on 5m and 15m (`trigger.md`).

1. **Know the settlement rule.**
   - **5m and 15m:** Up wins if the Chainlink BTC/USD 60 s TWAP at the end is >= the TWAP at the start (Gamma text, checked). A Binance 60 s TWAP proxy reproduces **99.0%** of outcomes, raw spot only 86.6% (5m) and 93.5% (15m).
   - **Hourly:** the Binance BTC/USDT 1H candle, close >= open (proxy matches 100%).
   - **The strike forms in the 60 s before the 5m/15m window opens.** One variant trades only there (step 7).
2. **Watch Binance BTCUSDT every second.**
   - **Trigger second:** the side bought matches the Binance move of the single second about 3 s before the fill's block time in **66.0% of USD (5m)** and **70.8% (15m)**. Other takers manage 55.7% and 56.6%.
   - **Not the trend:** seconds 6-8 back fall to 53-59%, and the cumulative move since open does not drive them.
3. **Possibly compare fair P(Up) with the book (unverified).** The firing pattern below conditions on the fair-vs-book gap, but the fair model's edge on the winners' own taker fills is small or negative: 0xc53375ff94e96100f2b30a4b5775db35218d69a9 +$1,342 model edge vs +$13.2k 2 s markout, 0x0ca4e9d27ff826a109ecbf74754fb66b93f277a6 -$91 vs +$8.8k, the 15m trio -1.2% to -1.8%/$ against 7.9-10.0%/$ taker gross, and the 4h look-alike trio -5.1% to -6.8%/$ against +5-9%/$. The supported rule is the narrower one in step 2: take the side of the latest Binance second(s).
   - **Gate:** after a >= 2 bp move, the top-5 bots fire in **15-20%** of seconds when the book already sits within 2 c of fair.
   - **Stale book:** when fair is more than 10 c ahead of the book they fire in **82% (5m, right direction 73%)** and **53% (15m, right direction 93%)** of seconds.
   - **Background rate:** with no move they still take in 33% (5m) and 9% (15m) of seconds at 55-58% direction accuracy.
4. **Take the stale side with a single-level marketable buy.**
   - **Clip:** fixed share count per bot (60 shares for the four big 5m bots, 30 for 0x41e2e1ccf1e4940029af02259a31c6b89b9fa354). The 15m trio is not fixed-clip: 250 shares is its most common size but covers only 6-8% of fills, with 5-share fills nearly as frequent. One fill per transaction (median 1.001), so they never sweep the book.
   - **Size:** median fill $12-13. Size barely scales with edge (rank corr +0.14) and not with move size (-0.01).
   - **Price range:** the 5m bots spend 62-66% of buy USD between 0.30 and 0.70, under 1% above 0.90.
5. **Speed achieved (block time):**
   - **Peak:** bot flow peaks **3 s (5m) / 4 s (15m)** after the Binance second; the book's last print peaks at 4 s.
   - **After a >= 3 bp jump:** a bot fills on the jump side within 6 s in **78% of 947 events (5m)** vs 52% at random, median first fill **2 s**; 15m 66% of 1,578 vs 25%, median **3 s**.
6. **Flip on reversals, never sell, hold to resolution.**
   - **No exits:** 38 of 49 `latency_arb` rows have zero SELL fills.
   - **Both sides:** they buy Up and Down in a median **90%** of markets, flipping 5-27 times per 5m market. Pooled, Up+Down pairs cost **$1.000** at the median, but that hides one leader: 0x3048d65321be3497164cdfc2996f94f98a2e7537 pairs at a share-weighted **0.986** over 569 markets for **+$9,396** (45% of its $20,746 gross), while 0xc53375ff94e96100f2b30a4b5775db35218d69a9 pairs at 1.0005 (-$204). At the 50% tier two taker legs cost about 1.75 c per pair near p = 0.5, more than the 1.4 c discount, so these pairs only pay where a leg is maker.
   - **Pairs vs lean (accounting split, not a cause):** pooled, pairs and round trips lost **-$24.6k** and the residual lean made **+$270.2k**. The lean is a median 19% of gross shares and sits on the winner for 56-66% of shares (5m bots). In 5m the edge is realized at entry (the 2 s markout) and merely stored in the lean.
   - **Timing in a 5m cycle:** first buy about 6 s after the open, 14-85 buys per market, 7-15% of USD in the last 60 s, last fill typically **97-117 s** before close (median per market; p10 41-44 s), and never later than about 25-34 s before close (p1).
7. **Variants seen:**
   - **Pre-open sniper:** 0x3089fcf3fe5b67ec287654b4d627bcd1d51135e4 puts 91% of USD into the 60 s strike-TWAP window before the 5m open.
   - **Maker-heavy:** the 15m trio is 60% maker by USD and pays no fee on that side.
   - **Long-horizon accumulators:** 0x06dc51826bc524d9a83770e7de9dd7e005b04524 (daily) and 0xb55fa1296e6ec55d0ce53d93b9237389f11764d4 (4h/hourly/15m), 60-130 fills per market across the whole window.

**Edge per trade (pooled taker fills):**
- **5m:** paid 0.612 for a side the spot model valued at 0.626, **1.40 c/share**; realized **2.44 c per USD** gross; other takers -0.96 c.
- **15m:** **2.47 c/share** model edge, **3.47 c per USD** realized.
- **Concentration:** fills right after an aligned 3 s move > 1 bp earn **10.7 c/USD (5m)** and **8.2 c (15m)**; fills against such a move lose 10.4 c and 4.6 c.

## 3. Everyone running it, ranked

**Ranking is by net PnL per day**, because the family windows run from 2 to 45 days and raw totals are not comparable. Rows are the 49 `latency_arb` wallet x family rows. The class gate includes **mo2 > 0**, which is a component of gross PnL, so the class's profitability rate is partly selection: across `latency_arb` plus `latency_arb_partial`, mo2 > 0 rows are 86.8% profitable (68 rows) vs 36.4% for mo2 <= 0 (33); even in class `none` it is 58% vs 41%. Speed rank comes from the peers burst duel (1 = fastest) among wallets with >= 100 contested bursts. First-block share is the share of contested bursts where the wallet lands in the first block. Net t is the per-market t-stat of net PnL. Gross %/$ is the realized edge per dollar traded.

| # | wallet | family | mkts | gross $ | net $ | net $/day | gross %/$ | net %/$ | taker % | med fill $ | net t | speed rank | first-block share |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0xc53375ff94e96100f2b30a4b5775db35218d69a9 | 5m | 571 | +20,857 | +15,177 | +7,588 | +4.54 | +3.30 | 87 | 10.8 | 4.4 | 4/267 | 0.50 |
| 2 | 0x3048d65321be3497164cdfc2996f94f98a2e7537 | 5m | 571 | +20,746 | +12,074 | +6,037 | +2.80 | +1.63 | 84 | 7.9 | 3.3 | 2/267 | 0.59 |
| 3 | 0x41e2e1ccf1e4940029af02259a31c6b89b9fa354 | 5m | 575 | +7,906 | +6,361 | +3,180 | +1.55 | +1.25 | 50 | 4.2 | 5.5 | 38/267 | 0.44 |
| 4 | 0x32ed2e546b187ca15e2841edc82b22c713cf8ec3 | 15m | 349 | +9,805 | +9,010 | +2,258 | +6.58 | +6.04 | 40 | 10.4 | 2.2 | 54/76 | 0.52 |
| 5 | 0x3725d52f3c252e8374999cc8617292ea2608ad88 | 15m | 332 | +9,687 | +8,850 | +2,218 | +6.29 | +5.75 | 40 | 13.7 | 2.0 | 45/76 | 0.54 |
| 6 | 0x0ca4e9d27ff826a109ecbf74754fb66b93f277a6 | 5m | 569 | +7,777 | +4,054 | +2,027 | +2.60 | +1.36 | 88 | 11.4 | 1.4 | 13/267 | 0.44 |
| 7 | 0xc2ad03f79ca3f3c17d8c7de2612ce0c89b7d40ed | 15m | 339 | +8,584 | +7,896 | +1,979 | +6.36 | +5.85 | 39 | 11.1 | 2.0 | 55/76 | 0.54 |
| 8 | 0x06dc51826bc524d9a83770e7de9dd7e005b04524 | daily | 44 | +77,147 | +70,391 | +1,564 | +6.48 | +5.92 | 66 | 39.0 | 3.4 | 5/7 | 0.68 |
| 9 | 0xb55fa1296e6ec55d0ce53d93b9237389f11764d4 | 15m | 251 | +8,944 | +5,054 | +1,267 | +2.65 | +1.50 | 95 | 20.2 | 0.9 | 32/76 | 0.55 |
| 10 | 0xd84403efd50b49a1d8a7181627e00307e6ea5908 | 5m | 561 | +3,894 | +1,454 | +727 | +1.98 | +0.74 | 88 | 13.0 | 0.7 | 18/267 | 0.42 |
| 11 | 0x9d57c42e847173d06841703825d3fe2299e456ea | hourly | 202 | +8,527 | +6,821 | +682 | +1.70 | +1.36 | 54 | 12.0 | 0.9 | 36/40 | 0.55 |
| 12 | 0xb55fa1296e6ec55d0ce53d93b9237389f11764d4 | hourly | 216 | +9,067 | +6,348 | +635 | +1.73 | +1.21 | 56 | 15.7 | 0.8 | 35/40 | 0.57 |
| 13 | 0xb55fa1296e6ec55d0ce53d93b9237389f11764d4 | 4h | 116 | +15,755 | +10,196 | +510 | +3.21 | +2.08 | 92 | 12.3 | 1.2 | 4/6 | 0.76 |
| 14 | 0xdc3f46236700a2c7e89e2b952a123cd757ad4fa0 | hourly | 240 | +5,106 | +4,355 | +435 | +1.08 | +0.92 | 38 | 10.6 | 3.7 | 13/40 | 0.60 |
| 15 | 0x21f4c1a1be34a39a7bc20985df4b7e5a39fb691d | 15m | 347 | +3,806 | +1,575 | +395 | +1.15 | +0.48 | 73 | 9.9 | 0.6 | 57/76 | 0.54 |
| 16 | 0x576b0696fd5a9225d66fd9500fd98f5be10b0cab | 5m | 575 | +1,788 | +782 | +391 | +1.08 | +0.47 | 67 | 2.4 | 0.4 | 67/267 | 0.40 |
| 17 | 0x9d57c42e847173d06841703825d3fe2299e456ea | 15m | 347 | +1,999 | +1,390 | +348 | +1.67 | +1.16 | 68 | 5.5 | 1.4 | 63/76 | 0.56 |
| 18 | 0x41e2e1ccf1e4940029af02259a31c6b89b9fa354 | 15m | 381 | +2,326 | +1,166 | +292 | +2.46 | +1.24 | 100 | 8.4 | 4.3 | 17/76 | 0.57 |
| 19 | 0xce25e214d5cfe4f459cf67f08df581885aae7fdc | 15m | 224 | +1,835 | +709 | +178 | +1.76 | +0.68 | 84 | 9.4 | 0.7 | 16/76 | 0.57 |
| 20 | 0xe349bbbc5c179ed7f8f13ab5502381980f532147 | 15m | 324 | +1,412 | +593 | +149 | +3.09 | +1.30 | 97 | 18.4 | 0.5 | 38/76 | 0.59 |
| 21 | 0x5e2b9261b0c4f697b55bf921ff2bc227183d9101 | 15m | 371 | +767 | +585 | +147 | +5.40 | +4.12 | 100 | 4.4 | 3.6 | 14/76 | 0.57 |
| 22 | 0x726fd4fd2d3f3a48fcbd54d1cecdd933d207d8e7 | daily | 45 | +6,793 | +6,197 | +138 | +7.36 | +6.71 | 59 | 10.0 | 1.9 | 4/7 | 0.68 |
| 23 | 0xafdcbcebe7cc1a61c9317dd663ab4ef7f8b0d278 | 15m | 229 | +512 | +462 | +116 | +2.03 | +1.83 | 32 | 6.4 | 0.7 | 58/76 | 0.48 |
| 24 | 0xfac01d79eb5d273ab0cbd3f8fd46a5da204584c8 | 15m | 235 | +640 | +369 | +92 | +3.26 | +1.88 | 100 | 8.4 | 2.2 | 29/76 | 0.58 |
| 25 | 0x5078f57065a338bd58065e76f02a9f9f5dd28082 | hourly | 204 | +1,056 | +819 | +82 | +2.11 | +1.64 | 30 | 2.5 | 1.3 | 17/40 | 0.62 |
| 26 | 0x2ed94d1a460379292d2e3b46f2cf7d94b033f271 | 4h | 113 | +1,897 | +1,530 | +76 | +8.34 | +6.72 | 95 | 5.0 | 1.9 | 3/6 | 0.64 |
| 27 | 0x576b0696fd5a9225d66fd9500fd98f5be10b0cab | 4h | 119 | +1,855 | +1,487 | +74 | +7.75 | +6.22 | 96 | 5.0 | 1.9 | 2/6 | 0.66 |
| 28 | 0x3a3749264a27ad3df99832f14dfa0789e06b3b1d | hourly | 183 | +725 | +708 | +71 | +6.22 | +6.07 | 37 | 4.3 | 1.4 | 31/40 | 0.51 |
| 29 | 0x576b0696fd5a9225d66fd9500fd98f5be10b0cab | hourly | 238 | +3,762 | +691 | +69 | +1.30 | +0.24 | 78 | 12.0 | 0.3 | 6/40 | 0.62 |
| 30 | 0xf31819f7f05eeb17ab40ff8e417447df339c68f0 | hourly | 180 | +687 | +685 | +69 | +6.91 | +6.89 | 31 | 4.0 | 1.6 | 33/40 | 0.57 |
| 31 | 0xc6accd5b5f647aacb751b8f3e9d640e723733778 | 15m | 354 | +1,326 | +271 | +68 | +2.35 | +0.48 | 100 | 18.9 | 0.2 | 11/76 | 0.62 |
| 32 | 0xeebde7a0e019a63e6b476eb425505b7b3e6eba30 | 4h | 120 | +1,339 | +951 | +48 | +5.38 | +3.83 | 96 | 5.0 | 1.1 | 5/6 | 0.60 |
| 33 | 0x50ea9d870f0347402afbf9d42713bb857bda5963 | 5m | 422 | +457 | +87 | +44 | +2.21 | +0.42 | 85 | 5.2 | 0.5 | 119/267 | 0.36 |
| 34 | 0xbd050887b28ef80590e25b0d0e4110154d930a55 | 5m | 487 | +108 | +72 | +36 | +0.97 | +0.65 | 33 | 2.4 | 1.4 | 131/267 | 0.37 |
| 35 | 0xa42f127d7e8df9f16881ffcc9ed0bc0326875f5a | daily | 45 | +1,549 | +853 | +19 | +0.65 | +0.36 | 40 | 10.8 | 0.8 | 1/7 | 0.87 |
| 36 | 0x24cee225701a99613577dbb95b3f71c53d59da46 | hourly | 230 | +364 | +91 | +9 | +1.37 | +0.34 | 77 | 13.5 | 0.1 | 22/40 | 0.64 |
| 37 | 0x60062ecbce1b143ed4955129377d2ff3632ac7e4 | daily | 42 | +411 | +206 | +5 | +3.44 | +1.73 | 100 | 5.0 | 0.7 | 3/7 | 0.67 |
| 38 | 0x596b928ea8168b239c9d846282777f79030c21e5 | 5m | 571 | +1 | +0 | +0 | +2.76 | +0.37 | 100 | 0.0 | 0.2 | 65/267 | 0.41 |
| 39 | 0x71f598dd23a96fc68c7f125f916c4a9b400e966e | hourly | 139 | +480 | -33 | -3 | +2.21 | -0.15 | 100 | 3.0 | -0.3 | 1/40 | 0.70 |
| 40 | 0x797f51dbff69ca70d0fbf87993176d0d788f37e8 | 5m | 574 | -32 | -58 | -29 | -0.05 | -0.10 | 43 | 0.2 | -0.3 | 105/267 | 0.32 |
| 41 | 0xab36e68001b55b97207d14e75fd7d922afc238da | 5m | 518 | -58 | -68 | -34 | -0.14 | -0.17 | 39 | 0.4 | -0.4 | 99/267 | 0.34 |
| 42 | 0x19b3823092892c026517fd0ff58df4889abe0b9b | 5m | 561 | +175 | -117 | -59 | +0.30 | -0.20 | 65 | 3.2 | -0.2 | 25/267 | 0.42 |
| 43 | 0x8320b90db15e5b777e5a023b5ba3cfa214d4904e | daily | 35 | -4,238 | -4,988 | -111 | -3.73 | -4.39 | 100 | 49.1 | -1.3 | 2/7 | 0.75 |
| 44 | 0x8b066217c8c3294a989ca9330e94d9c0810e8d91 | hourly | 240 | +638 | -1,140 | -114 | +0.46 | -0.82 | 61 | 4.3 | -2.3 | 3/40 | 0.67 |
| 45 | 0xeebde7a0e019a63e6b476eb425505b7b3e6eba30 | hourly | 238 | +1,451 | -1,620 | -162 | +0.51 | -0.57 | 79 | 11.8 | -0.7 | 4/40 | 0.66 |
| 46 | 0xd30d67e84ab372cde3990cb2500177f4a3104f6d | 5m | 574 | +287 | -487 | -244 | +0.97 | -1.64 | 100 | 6.2 | -1.2 | 11/267 | 0.48 |
| 47 | 0x2ed94d1a460379292d2e3b46f2cf7d94b033f271 | hourly | 238 | -347 | -3,414 | -341 | -0.12 | -1.18 | 79 | 11.7 | -1.4 | 5/40 | 0.62 |
| 48 | 0x2ed94d1a460379292d2e3b46f2cf7d94b033f271 | 5m | 561 | +50 | -925 | -463 | +0.03 | -0.57 | 69 | 9.0 | -0.5 | 70/267 | 0.39 |
| 49 | 0x5e60d871c2d646de185e541290689b727ef0e468 | 15m | 334 | -4,051 | -5,003 | -1,254 | -1.49 | -1.84 | 57 | 4.2 | -0.8 | 69/76 | 0.50 |

**Non-arb variants worth knowing (`momentum_taker`, one spot-triggered bet per market):** 0x55be7aa03ecfbe37aa5460db791205f7ac9ddca3 (daily, +$26.0k gross over 45 days), 0xcc500cbcc8b7cf5bd21975ebbea34f21b5644c82 (4h, +$11.9k over 20 days), 0x3089fcf3fe5b67ec287654b4d627bcd1d51135e4 (5m pre-open, +$2.3k). **0xb1d30490fa2ec8dc55591e8c71d3d64b6e0fc279 is excluded**: it buys only at >= 0.90 once the outcome is nearly settled, which is favourite-buying, not latency.

### By trader, not by wallet

Wallets were grouped when per-market net position **and** PnL correlate >= 0.7 (`peers_operators.csv`); rival bots sit at 0.0-0.3. Net here is recomputed per operator over **every** BTC family the wallets trade, with each wallet's measured rebate tier and **without** maker rebates, so it runs slightly under the table above.

| operator | wallets | gross $ | net $ | net $/day | USD traded/day | where the net comes from ($/day) |
|---|---|---|---|---|---|---|
| 15m trio | 0x32ed2e546b187ca15e2841edc82b22c713cf8ec3, 0x3725d52f3c252e8374999cc8617292ea2608ad88, 0xc2ad03f79ca3f3c17d8c7de2612ce0c89b7d40ed | +62,334 | +56,897 | **+12,777** | 328,715 | 15m +6,113; 5m +4,806; hourly +1,362; 4h +520 |
| single wallet | 0xc53375ff94e96100f2b30a4b5775db35218d69a9 | +20,857 | +14,849 | **+7,424** | 229,941 | 5m only |
| single wallet | 0x3048d65321be3497164cdfc2996f94f98a2e7537 | +20,746 | +11,386 | +5,693 | 370,780 | 5m only |
| single wallet | 0x41e2e1ccf1e4940029af02259a31c6b89b9fa354 | +10,232 | +6,271 | +2,845 | 278,742 | 5m +2,552; 15m +292 |
| pair | 0xb55fa1296e6ec55d0ce53d93b9237389f11764d4, 0xce25e214d5cfe4f459cf67f08df581885aae7fdc | +36,341 | +20,794 | +2,399 | 219,565 | 15m +1,405; hourly +523; 4h +501 |
| single wallet | 0x0ca4e9d27ff826a109ecbf74754fb66b93f277a6 | +7,777 | +3,841 | +1,921 | 149,496 | 5m only |
| single wallet | 0x06dc51826bc524d9a83770e7de9dd7e005b04524 | +77,147 | +68,854 | +1,530 | 26,443 | daily only |

- **The trio has the highest net per day, mechanism unknown.** Most of its non-15m flow is maker (taker share 16-18% in 5m, 10-12% hourly, 5-8% 4h, 0-3% daily). Its maker side was never tested for spot-awareness. Its 15m PnL is outcome-skewed in a Down-leaning window (15m Up rate 45.4%, every one of the 4 days below 48%): per-market PnL is +$39-47 when Down won vs +$7-10 when Up won, and Down-token buys made +$12.6k / +$9.4k / +$12.0k against Up-token buys of -$2.8k / +$0.3k / -$3.4k. Per-wallet t is only 2.0-2.2, and 0x3725d52f3c252e8374999cc8617292ea2608ad88 lost -$1,337 on one of the 4 days. Read it as high gross over 4 days with Down-regime exposure.
- **0xc53375ff94e96100f2b30a4b5775db35218d69a9 and 0x3048d65321be3497164cdfc2996f94f98a2e7537 are rivals, not one trader** (position and PnL corr 0.14 over 571 markets).
- **The look-alike trio 0x576b0696fd5a9225d66fd9500fd98f5be10b0cab, 0xeebde7a0e019a63e6b476eb425505b7b3e6eba30, 0x2ed94d1a460379292d2e3b46f2cf7d94b033f271 is not one book** (position corr -0.14 to +0.31): same software, separate accounts.
- **No on-chain funding link was checked** for any group; the grouping is behavioural.

### Contradictions resolved

- **"Most profitable = 0x06dc51826bc524d9a83770e7de9dd7e005b04524 (+$77.1k)" (peers):** true in total, false per unit of time. Its fills span 2026-08-24 to 10-07, 44 of the 45 daily markets in a 45-day window, so it is +$1.6k/day net. Its taker PnL is mo2 +$21.6k vs hold +$43.0k (plus +$12.6k maker), and the top 5 of 44 markets give 49% of PnL: mostly a directional hold, not latency. The 5m bots' totals cover 2 days.
- **"Largest operator group +$62.3k" (peers) vs "+$9.7k each" (execution/profit):** both are right. The $62.3k sums every BTC family; only the 15m rows are classed `latency_arb`. 0x3725d52f3c252e8374999cc8617292ea2608ad88 alone adds +$7.0k in 5m, +$4.0k hourly and +$3.4k 4h as a mostly-maker wallet.
- **"About 2 days of data" (several studies):** holds for 5m only. 15m covers 4 days, hourly 10, 4h 20, daily 45.
- **Lag "10 s vs 9 s" (profit, median) vs "1.33 s vs 1.07 s" (peers, mean; the peers median is 0 for both) for 0xc53375ff94e96100f2b30a4b5775db35218d69a9 and 0x3048d65321be3497164cdfc2996f94f98a2e7537:** different burst definitions. Profit chains fills while gaps stay <= 4 s, so long bursts inflate the median; peers uses a fixed 5 s window from the first fill. Peers shows 0x3048d65321be3497164cdfc2996f94f98a2e7537 modestly faster (first-block share 0.59 vs 0.50, duel 0.257 vs 0.171, speed rank 2 vs 4), and speed still does not explain the PnL gap. The speed column above uses the peers metric.
- **Model edge per $:** the profit study's `taker_model_per_usd` (for example +0.33%/$ for 0xc53375ff94e96100f2b30a4b5775db35218d69a9) does not match the trigger study's 1.22 c/share at a 0.573 average price (about 2.1%/$). The weighting differs (share-weighted vs USD-weighted) and the fair-value inputs may differ. I did not reconcile it, so the table uses realized gross %/$ instead of model edge (open question 3).

## 4. Why the best one beats the others

**Decomposition first, not a cause.** Net = gross - fee + rebates by construction, and across the 49 `latency_arb` rows gross per $ varies far more than fee per $ (std 2.57 pp vs 0.82 pp), so gross per $ explains **r^2 = 0.94** of the variance in net per $ arithmetically. The fee does not rank the winners, but it sets the zero line, which is why 52% of `latency_arb_partial` rows are gross-profitable and only 19% are net-profitable. The real question is why gross per $ differs, and the split below answers it with markout (mo2), hold and pair components.

**Gross by component (49 `latency_arb` rows, $):**

| family | rows | gross | taker mo2 (latency) | taker hold | maker |
|---|---|---|---|---|---|
| 5m | 14 | +63,956 | +55,269 | -4,907 | +13,594 |
| 15m | 14 | +47,591 | +15,840 | +29,053 | +2,699 |
| hourly | 12 | +31,516 | +12,301 | +2,875 | +16,340 |
| 4h | 4 | +20,846 | +1,385 | +15,737 | +3,724 |
| daily | 5 | +81,662 | +25,036 | +41,251 | +15,375 |
| all | 49 | +245,571 | +109,831 | +84,008 | +51,732 |

Only in 5m is the profit mostly latency. **4h and daily are a different strategy**: 0xb55fa1296e6ec55d0ce53d93b9237389f11764d4 4h has mo2 +$486 against hold +$11.7k and made +$13.7k in Up-won markets vs +$2.0k in Down-won ones (4h Up rate 55%); the 4h look-alike rows have mo2 +$263 to +$324, hold +$0.9-1.7k, negative model edge and top-5 markets 53-77% of PnL. Treat their PnL as directional or regime exposure, not spot-to-book latency.

**Cleanest test, 5m: 0xc53375ff94e96100f2b30a4b5775db35218d69a9 vs 0x3048d65321be3497164cdfc2996f94f98a2e7537.** Same strategy, same 50% rebate tier, same gross.

| | 0xc53375ff94e96100f2b30a4b5775db35218d69a9 | 0x3048d65321be3497164cdfc2996f94f98a2e7537 |
|---|---|---|
| volume | $460k | $742k |
| gross / per $ | +$20,857 / 4.54% | +$20,746 / 2.80% |
| taker fees (before rebate) | $12,016 | $18,721 |
| net / per $ | **+$15,177 / 3.30%** | **+$12,074 / 1.63%** |
| net: shared same-block taker flow | +$9,919 on $260.6k (5.33% gross/$) | +$7,012 on $267.7k (4.15% gross/$) |
| net: solo taker flow | +$1,552 on $141.3k | +$261 on $353.9k |
| net: maker flow | +$3,706 | +$4,800 |
| taker mo2 (2 s markout) | +$13,153 | +$18,570 |
| taker hold (pnl - mo2) | +$4,326 | -$1,937 |
| Up+Down pair PnL | -$204 (cost 1.0005) | +$9,396 (cost 0.986) |
| fills per market | 48.8 | 92.5 |
| net t-stat | 4.45 | 3.30 |
| pre-window gross ROI, current history.csv (from 2026-10-03) | 1.48% over 2,205 markets | 0.37% over 2,253 markets |
| pre-window gross ROI, history_v1_closed_only.csv (from Jun/Jul 2026) | 2.44% over 17,982 markets | 1.69% over 19,998 markets |

- **Not speed:** they fill the same market, direction and block **10,313 times**, and in those blocks 0x3048d65321be3497164cdfc2996f94f98a2e7537 gets the better price **62%** of the time. Its speed rank is 2 vs 4.
- **Where the $3.1k net gap arises:** **+$2.9k** in the shared same-block flow, where 0xc53375ff94e96100f2b30a4b5775db35218d69a9 earns 5.33% vs 4.15% gross per $. The extra solo volume adds **+$1.3k** (0x3048d65321be3497164cdfc2996f94f98a2e7537's solo $354k earns 1.56% gross and +0.07% net; its solo fees are $10,532 vs $4,063, about $3.2k more after the 50% rebate). 0x3048d65321be3497164cdfc2996f94f98a2e7537's larger maker PnL offsets **-$1.1k**. With zero solo flow it would still net about $11.8k against $15.2k.
- **The gap is not the latency component:** on the shared blocks 0x3048d65321be3497164cdfc2996f94f98a2e7537 has the higher 2 s markout (+$12,452 vs +$10,157). The difference is the **post-2 s hold** on those blocks (+$3,739 vs -$1,345): per market the hold difference is +$5,084 over 564 markets, **t = 2.3**. That is outcome-dependent PnL over 2 days and may be luck.
- **Pairs:** 0x3048d65321be3497164cdfc2996f94f98a2e7537 earns about half its gross from sub-$1 Up+Down pairs, which also explains its fee-heavy volume.
- **Sizing (inference):** per (market, block, direction), blocks of $10-25 earn **11.34%** (0xc53375ff94e96100f2b30a4b5775db35218d69a9) and **7.33%** (0x3048d65321be3497164cdfc2996f94f98a2e7537) gross; blocks of $25-50 earn **2.31%** on $188.3k and **0.40%** on $289.2k (`profit/h2h_blocks.csv`). This suggests the stale liquidity at the touch is small, but block size is confounded with move size (larger blocks cluster on larger moves, where the book has already repriced), so it is not a depth measurement.
- **Price band:** every 5m leader loses on 0.7-0.9 tokens (0x3048d65321be3497164cdfc2996f94f98a2e7537 -$5.3k gross on $215k) and earns on 0.1-0.5.
- **Durable ordering:** both history pulls rank 0xc53375ff94e96100f2b30a4b5775db35218d69a9 ahead: the closed-only pull covers months, the current one about 4 days before the study window. This is the only independent support for the hold advantage being skill.

**Across families:**
- **15m trio vs 0xb55fa1296e6ec55d0ce53d93b9237389f11764d4:** the trio is 60% maker (no fee) and nets 5.8-6.0%/$ in 15m; 0xb55fa1296e6ec55d0ce53d93b9237389f11764d4 is 95% taker, so the fee eats most of its 2.65% gross and it nets 1.50%/$. The trio's edge is mostly hold (taker hold 7.4-8.6%/$) in a Down-leaning window, so this ranks fee structure, not a proven mechanism.
- **0xb55fa1296e6ec55d0ce53d93b9237389f11764d4 wins on breadth:** $1.35M of volume over three families at 1.2-2.1%/$ net, t < 1.3 per family.
- **Losers turned by fees:** 0x2ed94d1a460379292d2e3b46f2cf7d94b033f271 (5m +$50 gross, -$925 net), 0xd30d67e84ab372cde3990cb2500177f4a3104f6d (5m +$287 gross, -$487 net on the 18% tier), 0xeebde7a0e019a63e6b476eb425505b7b3e6eba30 (hourly +$1.45k gross, -$1.6k net). 0x5e60d871c2d646de185e541290689b727ef0e468 (15m, -$5.0k net) is adversely selected as a maker (-8.8%/$ on maker fills).

**Speed: suggestive inside 5m only.** Rank correlation of speed (burst duel) with PnL is +0.30 (5m), +0.19 (15m), +0.02 (hourly). Among 5m `latency_arb` and `latency_arb_partial` (47 wallets) it is **+0.61** (p < 0.001, bootstrap 95% CI 0.39-0.77); among the 14 strict 5m `latency_arb` it is **+0.69** (p = 0.006, CI 0.28-0.90). That is 2 days, and the headline pair runs against it (rank 2 loses to rank 4; 0x41e2e1ccf1e4940029af02259a31c6b89b9fa354, rank 38, is third by net/day). What predicts ROI in every family is the edge of a wallet's first-block entries (rank corr +0.31 to +0.86). Being late does cost price: in 5m, first-block entries earn **+3.07%/$** at 0.83 c above the first print, entries 1-5 s later **+1.48%/$** at 3.27 c.

## 5. Is it easy to recreate?

**The logic is easy; making money with it is not.** A working version is a few hundred lines: a Binance websocket, a fair-value function under the real settlement rule, a Polymarket CLOB websocket for the book, and an order sender. The hard parts are below.

- **Data feeds:**
  - **Binance BTCUSDT trades or bookTicker websocket.** 1 s klines are too coarse to trade on; the bots key off a single second.
  - **Polymarket CLOB market websocket** for the live book of the current 5m/15m market, plus Gamma for market discovery (a new 5m market every 300 s).
  - **Chainlink BTC/USD 60 s TWAP stream** is the actual settlement source for 5m/15m. It needs Data Streams credentials; a Binance 60 s TWAP proxy matches 99.0% of outcomes, so it is optional for v1.
- **Latency budget:**
  - **Book catch-up:** the Polymarket last print peaks about **4 s** after the Binance second.
  - **Incumbents:** bot fills land **2-3 s** after it in block time, and block time lags the off-chain match, so their true reaction is shorter.
  - **Target:** Binance tick to signed order accepted by the CLOB in **under ~1 s**, so the fill lands in the first block. Late entries in 5m keep about half the edge (+1.48% vs +3.07%/$ gross), which is below the ~3% fee.
  - **Hosting:** a VPS near the Polymarket CLOB and Binance endpoints. I did not measure where either is hosted.
- **Capital:**
  - **Per 5m market:** 0xc53375ff94e96100f2b30a4b5775db35218d69a9 spends a median **$645** (p90 $1,687, max $3,417); 0x3048d65321be3497164cdfc2996f94f98a2e7537 a median **$1,090** (max $4,641).
  - **Working capital:** a 5m market settles every 300 s, so a few $k plus redemption float is enough for one family. This is an estimate from per-market spend, not a measured balance.
- **Infra:** a Polygon wallet with USDC, CLOB API keys, automatic redeem or merge after each market, and monitoring. Nothing exotic.
- **Competition:**
  - **Crowding:** a median **4** latency wallets join each 5m burst (11 USD-weighted), and the biggest 5m bots reach the first block in only 35-65% of contested bursts.
  - **Capacity (inferred, not measured):** PnL by block size suggests roughly $10-25 of stale liquidity per block, but block size is confounded with move size and no order book snapshots exist here. Measure depth from CLOB book snapshots before sizing a bot. Either way, a new bot splits a fixed pool; it does not add one.
  - **Copy trading does not work in 5m:** non-latency fills 1-30 s after a burst lose 0.9-2.2%/$ there; in 15m the picture is mixed (3-5 s after a burst earns +3.0%/$ on $1.10M, 0 s +1.1%/$, 1-2 s and 6-30 s lose 1.5-1.9%/$). And 0xc53375ff94e96100f2b30a4b5775db35218d69a9 keeps only 0.29 of its PnL when copied 2 s late.
- **Fees (the real barrier):**
  - **Rate:** the taker fee is `0.07 * p * (1-p)` per share, **3.0% of notional at p = 0.57**. Makers pay nothing and share a 20% rebate pool.
  - **Tier:** taker rebate tiers are 3/8/18/32/44/50%, with 50% at **$10M of 30-day weighted volume** (size x (1 - price) x 2.3). Every big 5m bot sits at 50%.
  - **Without the tier:** net at a 0% rebate would be **$9,169** for 0xc53375ff94e96100f2b30a4b5775db35218d69a9 (vs $15,177), **$2,713** for 0x3048d65321be3497164cdfc2996f94f98a2e7537 (vs $12,074) and **$118** for 0x0ca4e9d27ff826a109ecbf74754fb66b93f277a6 (vs $4,054). A newcomer has to earn the tier while losing most of the edge to fees.
- **Difficulty: 7/10.**
  - **Easy (2/10):** the signal and the code.
  - **Hard (8-9/10):** sub-second execution, a fee tier you only get by already trading $10M a month, and what looks like (inferred) tens of dollars of stale liquidity per block contested by a dozen bots.
  - **No maker recommendation yet:** the trio's maker quoting looks attractive on paper (no fee, rebate income, 5.8-6.0%/$ net in 15m), but its maker fills were never tested for spot alignment or adverse selection, and its PnL comes from a Down-leaning 4-day window. Test that over an Up-heavy period before copying it. The measured latency edge is the 5m taker markout.

## 6. Open questions

1. **Does Binance lead the Chainlink TWAP that settles 5m/15m, and by how much?** Not measured (credentials needed); only Binance leading the Polymarket book (about 4 s) is measured.
2. **True reaction time:** fill times are Polygon block times. The off-chain match time (CLOB trade feed) would give the real latency budget.
3. **Model edge disagreement:** the profit study's model edge per $ (+0.33%/$ for 0xc53375ff94e96100f2b30a4b5775db35218d69a9) and the trigger study's (about 2.1%/$) disagree; check the weighting and fair inputs before using model edge for a live gate.
4. **Is the trio's maker quoting spot-aware, and is it adversely selected?** Only its taker side was tested, and even there the Binance-vs-tape test is unstable (errata). Its 5m/hourly/4h/daily net (+$6.7k/day combined) comes from mostly-maker rows classed `none`.
5. **Same owner?** No funding trace was run for the trio, the 0xb55fa1296e6ec55d0ce53d93b9237389f11764d4 / 0xce25e214d5cfe4f459cf67f08df581885aae7fdc pair, or the 0x576b0696fd5a9225d66fd9500fd98f5be10b0cab / 0xeebde7a0e019a63e6b476eb425505b7b3e6eba30 / 0x2ed94d1a460379292d2e3b46f2cf7d94b033f271 trio. `scripts/scan/trace_funding.py` can do this.
6. **Short windows:** 5m is 2 days and t-stats are 0.2-5.5. Only 0xc53375ff94e96100f2b30a4b5775db35218d69a9 > 0x3048d65321be3497164cdfc2996f94f98a2e7537 is backed by more than one test. Every large 5m bot (top 6 by gross) earned more buying Up than Down (0xc53375ff94e96100f2b30a4b5775db35218d69a9 +$13.9k vs +$7.0k; 0x3048d65321be3497164cdfc2996f94f98a2e7537 +$19.2k vs +$1.6k); 0x50ea9d870f0347402afbf9d42713bb857bda5963 and 0x797f51dbff69ca70d0fbf87993176d0d788f37e8 earned more buying Down, and 0xab36e68001b55b97207d14e75fd7d922afc238da lost on both. Up won 285 of 575 markets (49.6%), so this is **not a regime**. Open finding: book-side staleness or retail Up flow are candidates.
7. **Fee assumption:** fills are assumed to exclude the fee. Rebate payouts landing on the published tiers support this but do not prove it.
8. **Unreconciled lifetime numbers:** 0x3048d65321be3497164cdfc2996f94f98a2e7537 received $185k of lifetime taker rebates (at least $370k of fees) against $3.7k of gross PnL in the current history.csv ($53.9k in history_v1_closed_only.csv), so it trades elsewhere or both history pulls undercount.
9. **0x06dc51826bc524d9a83770e7de9dd7e005b04524** gets taker rebates about 110x its BTC-daily fees, so the daily slice is a small part of a larger operation that has not been mapped.

## Errata / verification

A review challenged 25 points. Each was rechecked against the data with `research/profit/verify_h2h.py` and `research/profit/verify_misc.py` (outputs `data/out/latency/profit/h2h_{flows,blocks,pairs}.csv`).

**Upheld and fixed:**
- **5m net gap cause:** "the extra solo volume accounts for the whole $3.1k gap" was wrong. Shared same-block flow gives +$2.9k, solo +$1.3k, maker -$1.1k. The $6.7k extra fee was pre-rebate (about $3.2k after). Within shared blocks the gap is post-2 s hold PnL (t = 2.3), while 0x3048d65321be3497164cdfc2996f94f98a2e7537 has the larger 2 s markout. Head-to-head table now carries flow, mo2, hold and pair rows.
- **history.csv figures:** 2.44% / 1.69% over 17,982 / 19,998 markets and $53.9k come from `history_v1_closed_only.csv`. The current `history.csv` (from 2026-10-03, about 4 days) gives 1.48% over 2,205 vs 0.37% over 2,253 and $3.7k. Both are now cited; the ordering holds in both.
- **Speed correlation:** +0.61 covers 47 `latency_arb` + `latency_arb_partial` wallets. The 14 strict rows give +0.69 (p = 0.006, CI 0.28-0.90). Now labelled suggestive.
- **Stop time:** 25-34 s was the p1 of secs_to_end. The median last fill per market is 97-117 s before close (p10 41-44 s).
- **Lag figures:** 1.33 s / 1.07 s are mean lags (median 0 for both), and peers shows 0x3048d65321be3497164cdfc2996f94f98a2e7537 modestly faster, not "equally fast".
- **Up vs Down:** 11 of 14 5m `latency_arb` rows earned more buying Up. 0x50ea9d870f0347402afbf9d42713bb857bda5963 and 0x797f51dbff69ca70d0fbf87993176d0d788f37e8 earned more on Down, and 0xab36e68001b55b97207d14e75fd7d922afc238da lost on both (-$27 / -$31). Up won 49.6% of 5m markets, so the "regime" explanation was removed.
- **Fee share:** 67% is fees before rebates. After rebates costs take 30% of gross.
- **0x06dc51826bc524d9a83770e7de9dd7e005b04524:** 44 of 45 daily markets, not 45.
- **Seconds 6-8 back:** 53-59%, not 53-57% (15m second 6 is 0.591).
- **Trio taker share outside 15m:** 16-18% (5m), 10-12% (hourly), 5-8% (4h), 0-3% (daily).
- **Trio clip:** 250 shares covers only 6-8% of fills; not a fixed clip.
- **Copy-trade curve:** the 1-30 s loss holds in 5m only. In 15m, 3-5 s earns +3.0%/$.
- **First-block share 35-65%:** holds for 5m only. Long-horizon rows reach 0.68-0.87.
- **Block buckets:** recomputed at 2.31% / 0.40% for $25-50 blocks (was 2.21% / 0.33%). The table is now saved, and the depth reading is labelled an inference confounded with move size.
- **Decision rule:** the fair model shows little or negative edge on winners' fills, so the rule is stated as "take the side of the latest 1-3 s Binance move" and fair-vs-book thresholding is marked unverified.
- **Pairs:** 0x3048d65321be3497164cdfc2996f94f98a2e7537 gets +$9,396 (45% of gross) from pairs at 0.986. The pooled median hid this. Pair PnL is now reported per wallet, and the lean-vs-pairs split is labelled an accounting identity.
- **"97% of variance":** recomputed r^2 is 0.94, and it is an arithmetic decomposition, not a cause.
- **4h and daily:** profit is hold-dominated (all 49 rows: mo2 $109.8k, hold $84.0k, maker $51.7k). Only the markout is counted as latency profit.
- **Capacity:** "$10-25 of stale liquidity per block" came from PnL by block size, which is confounded with move size, and no order book data exists. It is now labelled an inference in sections 4 and 5.
- **mo2 gate:** mo2 > 0 is PnL-linked, so class profitability is partly selection. This is now stated.

**Partly upheld, or not reproduced:**
- **Trio downgrade:** upheld. The maker side is untested, the 15m Up rate was 45.4% with every day below 48%, Down-token buys carry the PnL, and 0x3725d52f3c252e8374999cc8617292ea2608ad88 lost -$1,337 on 2026-10-07. The recommendation to copy its maker quoting is withdrawn.
- **Trio Binance-vs-tape numbers:** the challenge's figures (-5.6% / -6.4%/$ following Binance, +10.8% / +4.5% following the tape) were not reproduced. The result depends on how the "tape" move is defined:
  - **Tape = change of the last print (previous block VWAP vs the one before):** following Binance gives -2.3%/$ for 0x32ed2e546b187ca15e2841edc82b22c713cf8ec3 and -11.8%/$ for 0xc2ad03f79ca3f3c17d8c7de2612ce0c89b7d40ed; following the tape gives +8.2% and +10.3%.
  - **Tape = 10 s print change:** 0xc2ad03f79ca3f3c17d8c7de2612ce0c89b7d40ed flips to +10.6%/$ following Binance vs +2.9% following the tape.
  - **Verdict:** inconclusive at $12-17k per wallet, and not used.
- **0x41e2e1ccf1e4940029af02259a31c6b89b9fa354 "51.3% follow Binance":** not reproduced. Under both tape definitions it follows Binance in 62-68% of disagreements (5m and 15m), and those fills earn +7% to +11%/$. The point that speed rank does not order the 5m PnL table still stands.

**Not changed:** every other figure in sections 2-3 and the ranked table.

## Reproduce

```
python3 research/fingerprint.py
python3 research/trigger/run.py
python3 research/execution.py
python3 research/peers && python3 research/peers/report.py
python3 research/profit/run.py --refresh && python3 research/profit/stats.py
python3 research/profit/verify_h2h.py && python3 research/profit/verify_misc.py
```
