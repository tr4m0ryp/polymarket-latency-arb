# Latency wallets: why one earns more than another

**Main cause: edge per dollar on the marginal trade, measured against a ~3 % taker fee.**
Speed does not explain the gap. The bots that lead the 5m family all hit the same stale quotes in
the same 2 s Polygon blocks. The losers add volume whose gross edge is at or below the taker
fee. Across the 49 latency_arb rows, **97 % of the cross-wallet variance in net PnL per $** comes
from gross edge per $. The effective fee per $ explains 1.7 % and maker rebates 1.6 %. The fee
still sets the zero line, so it decides who ends up profitable at all.

Code: `research/profit/` (extract, decompose, race, rebates, run, stats). Run with
`python3 research/profit/run.py --refresh && python3 research/profit/stats.py`.
Tables: `data/out/latency/profit/{summary,summary_stats,buckets,rebate_days,head_to_head}.csv`.

## 1. Fees were missing from every earlier PnL number

- **Fee rule (Gamma `feeSchedule`, every BTC family):** `crypto_fees_v2`, rate 0.07, exponent 1,
  takerOnly, rebateRate 0.2. The taker fee is `C * 0.07 * p * (1 - p)` USDC, where C is the share
  count and p the token price. That is 0.07(1-p) of notional, or **3.0 % at p = 0.57**, the
  typical bot entry. Makers pay nothing.
- **Formula verified against payouts:** for the 35 latency wallets with more than $500 of fees on
  2026-10-07/08, the observed `TAKER_REBATE / computed fee` clusters on the published tiers.
  11 wallets sit at **0.49-0.52 (Obsidian 50 %)**, for example 0xc53375ff94e96100f2b30a4b5775db35218d69a9
  at 0.504 and 0x3048d65321be3497164cdfc2996f94f98a2e7537 at 0.504. Others sit near 0.08 (Silver)
  or 0.18-0.19 (Gold). A rate above 0.5 means the wallet also pays fees outside the BTC families.
  Rates above 0.5 are capped at 0.5 before being applied.
- **Maker rebate model verified:** the pool is 20 % of each market's taker fees, split pro rata on
  maker fee-equivalent. Actual `MAKER_REBATE` divided by the estimate has a **median of 1.03**
  (IQR 0.99-1.26).
- **Taker-rebate program:** the 30-day weighted volume is size x (1 - price) x 2.3 for crypto.
  The tiers are 3 / 8 / 18 / 32 / 44 / 50 %, with 50 % at $10M of weighted volume.

| class (rows) | volume | gross PnL | taker fees | taker rebate | maker rebate | **net** | profitable gross / net |
|---|---|---|---|---|---|---|---|
| latency_arb (49) | $9.44M | +$245.6k | $163.8k | $76.9k | $13.8k | **+$172.5k** | 90 % / 78 % |
| latency_arb_partial (52) | $0.37M | +$1.1k | $8.6k | $1.7k | $0.2k | **-$5.7k** | 52 % / 19 % |
| momentum_taker (330) | $4.15M | +$96.7k | $52.8k | $18.2k | $1.7k | **+$63.8k** | 69 % / 51 % |

Taker fees equal **67 % of latency_arb gross PnL**. Taker fee per taker $ has a median of 2.55 %
(range 0.2-3.4 %). This fee wall is why the partial copies, with lower volume, weaker edge and
low tiers, lose money as a group.

## 2. 5m head-to-head: 0xc53375ff94e96100f2b30a4b5775db35218d69a9 vs 0x3048d65321be3497164cdfc2996f94f98a2e7537

Both wallets ran the same strategy at the same 50 % tier and made the same gross PnL. The net
results differ by $3.1k.

| | 0xc53375ff...69a9 | 0x3048d653...7537 |
|---|---|---|
| volume | $460k | $742k |
| gross PnL / per $ | +$20,857 / 4.54 % | +$20,746 / 2.80 % |
| taker fees | $12,016 | $18,721 |
| net after rebates / per $ | **+$15,177 / 3.30 %** | **+$12,074 / 1.63 %** |
| fills per market | 48.8 | 92.5 |
| per-market net t-stat | 4.45 | 3.30 |
| history.csv pre-window ROI (gross) | 2.44 % over 17,982 mkts | 1.69 % over 19,998 mkts |

- **Not speed:** the two fill the **same market, same direction, same block 10,313 times**. Those
  blocks hold 65 % of 0xc533's taker USD and 43 % of 0x3048's. Inside them **0x3048 gets the
  better price in 62 % of blocks** (0xc533 in 25 %), by 0.44 c on average. In both directions the
  burst-race metric shows no gap: lead share is 0.118 vs 0.127 and the median burst lag is 10 s
  vs 9 s.
- **Shared flow:** gross is 5.33 % vs 4.15 % per $, and net after the 50 % rebate is 3.81 % vs
  2.62 %.
- **Solo flow (the cause):** 0x3048 trades **$354k alone at 1.56 % gross**, which leaves
  **+0.07 % net** after the 2.98 % fee and 50 % rebate. 0xc533's solo flow is only $141k, at
  2.54 % gross and 1.10 % net. The extra $213k of volume 0x3048 runs adds about $6.7k of fees and
  almost no gross PnL. That is the entire net gap.
- **Sizing:** blocks of $25-50 earn **0.33 % gross for 0x3048 on $289k** (-1.07 % net), against
  2.21 % for 0xc533 on $189k. Blocks of $10-25 are where the edge sits: 11.4 % and 7.3 % gross.
  The stale liquidity at the touch is roughly $10-25 per block, and above that the bots walk into
  fairly priced levels.
- **Allocation by spot-implied model edge is identical** (USD shares within 1 pt in every
  `fair - pi` bucket). The model fills that look negative cost 0x3048 -9.7 % per $ against -4.7 %
  for 0xc533.
- **Other 5m bots, same tier:** 0x0ca4e9d27ff826a109ecbf74754fb66b93f277a6 (net 1.36 %/$) and
  0xd84403efd50b49a1d8a7181627e00307e6ea5908 (0.74 %/$) pay up more versus the previous block
  (-3.0 % and -3.7 % per taker $, against -2.1 % for 0xc533). Both have a negative second half
  (net_B -$129 and -$466).
- **0x41e2e1ccf1e4940029af02259a31c6b89b9fa354** is a hybrid that is 50 % maker. It has low edge
  (1.25 %/$ net) but is the most consistent row: t = 5.49 in 5m and 4.30 in 15m, with $1,256 of
  estimated maker rebates. Its implied rate of 0.754 means it pays fees outside the BTC families.

## 3. Other families

- **15m trio, best edge per $ at scale:** 0x32ed2e546b187ca15e2841edc82b22c713cf8ec3,
  0x3725d52f3c252e8374999cc8617292ea2608ad88 and 0xc2ad03f79ca3f3c17d8c7de2612ce0c89b7d40ed net
  **5.8-6.0 %/$**. About 60 % of their USD is **maker** (no fee, 4.3-5.2 % gross, $437-472 of
  maker rebate each). Their taker fills earn 7.9-10.0 % gross, almost all on cheap tokens
  (0.1-0.5: +25-50 %/$), and they lose on 0.7-0.9 tokens (-8 to -14 %/$).
- **The trio looks like one operator:** fingerprints are near-identical and wallet_links has a
  co-signal edge between 0x32ed and 0xc2ad. Splitting the flow keeps each wallet at Gold (18.6 %).
  The evidence is weaker here: t = 2.0-2.2, and 0x3725's second half is -$524.
- **0xb55fa1296e6ec55d0ce53d93b9237389f11764d4 in 15m:** 95 % taker with only 2.65 % gross per $,
  so the fee (2.48 %/$ before rebate) consumes most of it. Net is 1.50 %/$.
- **0xb55fa1296e6ec55d0ce53d93b9237389f11764d4 overall:** it wins on **breadth, not edge**. Its 3
  latency_arb families (15m, hourly, 4h) total $1.35M of volume and **+$21.6k net**, at
  1.2-2.1 %/$ with t < 1.3 per family.
- **0x06dc51826bc524d9a83770e7de9dd7e005b04524 (daily):** +$70.4k net at 5.9 %/$, t = 3.40. Its
  taker-rebate payouts are about 110x the fees of its BTC-daily fills, so this slice is a small
  part of a larger fee-paying operation.
- **Losers:** 0x5e60d871c2d646de185e541290689b727ef0e468 (15m, **-$5.0k net**) is
  adversely selected as a maker: its maker fills earn -8.8 %/$.
  0x2ed94d1a460379292d2e3b46f2cf7d94b033f271 makes +$50 gross in 5m and **-$925 net**, and -$3.4k
  net in hourly. 0xeebde7a0e019a63e6b476eb425505b7b3e6eba30 hourly is +$1.45k gross and -$1.6k
  net. 0xd30d67e84ab372cde3990cb2500177f4a3104f6d (5m, Gold 18 %) is +$287 gross and -$487 net:
  without a high tier, a 1 % gross edge is a loss.

## 4. Buckets (5m leaders, `buckets.csv`)

- **Seconds left:** 60-70 % of USD and most PnL fall 120-300 s before the close. The last 10 s
  are negative for every bot that trades there.
- **Size of the BTC move over the previous 10 s:** most PnL comes from moves under 5 bp. Moves of
  5-10 bp are flat or negative (0xc533 -$305, 0x0ca4 -$957) because the book has already repriced.
- **Side:** every 5m bot earned more buying Up than buying Down. This is the regime of the 2
  sampled days, not skill.
- **Token price:** 0.1-0.5 tokens carry the edge. Every leader loses on 0.7-0.9 tokens (0x3048
  -$5.3k gross on $215k).

## 5. Caveats

- **Short window:** the window is about 2 days (5m), so per-market t-stats are only 0.2-5.5. Of
  the gaps, only 0xc533 > 0x3048 (both t > 3, and history.csv agrees) and the trio > 0xb55f are
  backed by more than one test.
- **Fee assumption:** fills are assumed to be at the match price, excluding fees. The tier-matching
  rebate rates support this but do not prove it.
- **Lifetime figures do not reconcile:** 0x3048 has $185k of lifetime TAKER_REBATE since
  2026-06-19, which implies at least $370k of fees, against $53.9k of gross PnL in history.csv.
  Either history.csv undercounts or the wallet pays fees elsewhere. Do not read long-run net PnL
  from these numbers.
- **Block resolution:** fill timestamps are Polygon block times (~2 s), so the race metrics cannot
  see sub-block speed differences.
