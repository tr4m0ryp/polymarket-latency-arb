# Live taker hold: can a wider limit rescue the missed fills?

Data: the two live micro runs of 2026-10-13 (`dublin-micro-20261013`, 14:03-14:34, and
`dublin-micro-20261013b`, 15:39-19:39 UTC): **195 FAK orders, 36 fills, 36 markets**, primary arm
`vt_v1_m0.03_any`, 5 shares, limit = seen ask + 2 c. Book: the Dublin paper box's CLOB tape for
the same hours, replayed on the venue `timestamp` (its websocket lags the venue clock by 80 ms
median and > 1 s at p90, so receipt time is not used). Code: `research/livehold/`. Outputs:
`data/out/livehold/{summary,shift,leaders}.md`. Read-only, no orders.

## Verdict

**No limit rule fixes it.** The missed orders are worth +20-27 c/$ only at the price we saw. By the
time the venue matches a held order (send + 246 ms median), makers have pulled that depth and the
ask sits 6 c higher (median). Buying the repriced ask with a wider limit fills 36-85% of orders but
at **-2 to -7.5 c/$** (k = 3..10 c), negative at every width above +2 c. Edge-scaled limits
(seen + f x model edge) behave the same as the matching fixed k. The only lever with a measured,
positive effect is an **earlier match**: matching 200-230 ms earlier gives **+8.6 to +10.2 c/$**
with the CI above 0, while 30 ms earlier (about what co-location saves) changes nothing.
**Leaders A and B, on the same tape and hours, earn about 0 c/$ of 10 s markout at our 0% fee
tier** (A +0.0 [-1.2, +1.1], B +0.8 [-1.3, +3.2]) as 98% takers; they stay positive through the 50%
taker rebate and hold-to-resolution, not through a way around the hold.

## 1. The match instant and the replay

- **Match time:** all 36 of our fills appear on the tape (`last_trade_price`, joined by price and
  size) at **send + 246 ms** median (p10 213, p90 351) on the venue clock; the ack follows **14 ms**
  later. A held order therefore matches at about `ack - 14 ms`, and every counterfactual below is
  read there.
- **Replay check:** sweeping the replayed asks at that instant with the live limit reproduces the
  live outcome for **185 of 195** orders (154 misses and 31 fills right, 5 + 5 wrong).
- **Our feed was not the problem:** the ask we acted on equalled the true venue ask at send for 87%
  of missed and 94% of filled orders.

## 2. What happens during the hold

| | missed live (159) | filled live (36) |
|---|---|---|
| ask move, send to match (c), p10 / p50 / p90 | +3 / +6 / +12 | 0 / +2 / +3 |
| depth at <= limit at send, median shares | 381 | 731 |
| depth at <= limit at match, median shares | 0 | 114 |
| removed depth that was traded away / pulled | 6% / **94%** | 11% / 89% |

The depth is **pulled, not taken**: 94% of the shares at our limit that vanish before our match are
cancelled or requoted by makers, not hit by rival takers. For the missed orders the depth at our
limit is gone at **send + 146 ms** median (p10 43, p90 331). On book-triggered signals that is
**265 ms after the venue event** that triggered us, and our send itself left 112 ms after that
event. Older touch levels (> 47 ms since their last change) survived the hold less often (9% vs
24-27% for fresher ones, n = 45 per quartile), which fits makers sweeping stale quotes.

## 3. Counterfactual limits (all 195 orders, 10 s markout after the 0% tier fee)

| limit | fill rate | mk10 c/$ | 95% CI | $ per order |
|---|---|---|---|---|
| seen + 0 c | 0.07 | +6.3 | [-11.0, +21.1] | +0.01 |
| seen + 1 c | 0.11 | +2.8 | [-12.0, +15.7] | +0.01 |
| **seen + 2 c (live)** | 0.18 | -1.4 | [-13.8, +9.3] | -0.00 |
| seen + 3 c | 0.36 | -4.9 | [-13.2, +2.9] | -0.03 |
| seen + 5 c | 0.53 | -7.5 | [-14.7, -1.0] | -0.08 |
| seen + 7 c | 0.73 | -5.6 | [-12.1, -0.5] | -0.09 |
| seen + 10 c | 0.85 | -2.9 | [-8.7, +2.6] | -0.05 |
| seen + 0.5 x edge | 0.19 | -1.2 | [-12.2, +10.8] | -0.00 |
| seen + 1.0 x edge | 0.44 | -6.7 | [-15.6, +0.9] | -0.06 |

On the 159 orders that missed live, the few that still fill at <= +2 c earn +20-27 c/$ (5 orders),
and from +3 c upward the extra fills run -2 to -7 c/$. The +16.8 c/$ paper markout of the missed
orders was priced at an ask that no longer existed when the venue matched them.

## 4. An earlier match (live limit, same orders)

| match earlier by | fill rate | mk10 c/$ | 95% CI | $ per order |
|---|---|---|---|---|
| 0 ms (live) | 0.18 | -1.4 | [-14.0, +10.4] | -0.00 |
| 30 ms | 0.26 | -0.6 | [-12.3, +10.7] | -0.00 |
| 60 ms | 0.35 | +1.3 | [-7.1, +10.4] | +0.01 |
| 100 ms | 0.50 | +3.2 | [-3.9, +9.5] | +0.03 |
| 150 ms | 0.70 | +3.7 | [-1.9, +9.3] | +0.05 |
| 200 ms | 0.81 | **+8.6** | [+2.4, +14.7] | +0.14 |
| 230 ms (no hold) | 0.88 | **+10.2** | [+4.4, +15.6] | +0.18 |

The signal is real when it can trade at the price it saw; the hold removes it. A network gain of
~30 ms does nothing measurable; only an order path the hold does not apply to, or a maker route,
recovers the 200+ ms.

## 5. Leaders A and B on the same tape

Their Data API fills for 14:00-20:00 UTC (A 3,955 BUY fills, B 955), each joined to the tape's
`last_trade_price` by transaction hash for its venue match time.

| leader | role | fills | share of USD | mk10 c/$ at 0% tier | 95% CI | at 50% rebate | median size |
|---|---|---|---|---|---|---|---|
| A 0xc53375ff94e96100f2b30a4b5775db35218d69a9 | taker | 3,722 | 98% | +0.0 | [-1.2, +1.1] | +1.6 | 30 |
| A | maker | 233 | 2% | +1.9 | [-5.5, +8.6] | | 4.7 |
| B 0x3048d65321be3497164cdfc2996f94f98a2e7537 | taker | 912 | 98% | +0.8 | [-1.3, +3.2] | +2.4 | 30 |
| B | maker | 43 | 2% | +20.3 | [+8.0, +39.5] | | 3.9 |

- **Method today:** both are takers (98% of USD), fixed 30-share clips (60 in the 2026-10-07/09
  study), one level per fill.
- **Limit width:** A pays the ask that stood 250 ms before its match in 83% of fills (median 0 c
  above it), so A takes what survives the hold, like us. B pays a median **+2 c** above that ask
  (69% of fills above it): consistent with a wider limit sweep. B's wider fills are not worse (3-5 c
  above: +1.3 c/$, CI [-1.3, +3.9]), A's are slightly negative (-1.6 c/$).
- **Where their money comes from:** at our 0% tier their 10 s markout is about zero; the 50% taker
  rebate adds about 1.6 c/$ and the earlier study attributes the rest to hold-to-resolution and pairs.
  Neither shows a route around the hold.

## 6. Live hold and duplicate-send tests (2026-10-14, Dublin)

**The hold applies to every marketable order type; hedged sends are safe and cut the tail.**

| test | result |
|---|---|
| marketable FAK / FOK / GTC ack p50 | 210 / 222 / 216 ms vs resting GTC 45 ms: **+165-176 ms** hold on all three (n 2/1/1) |
| marketable GTD | rejected: venue requires expiration >= now + 180 s |
| duplicate send, k = 1 / 2 / 3 copies | one order per payload every time (deduped); first-ack p50 63 / 39 / 38 ms, **p90 334 / 45 / 46 ms** |
| cost | 4 fills, $4.50 (cheap-side tokens bought to trigger matches) |

Verdict: order type does not escape the hold, so the taker route stays closed. The maker route's
condition (cancels under ~50 ms) is met at p90 by sending each cancel on 2-3 connections. Runs:
`data/trade/dublin-dup-20261014`, `data/trade/dublin-hold-20261014`.

## Caveats

- **Small sample:** 195 orders, 36 fills, 36 markets over 4.5 h; every CI above is wide.
- **Counterfactuals assume our order changes nothing:** a held order of ours does not alter maker
  behaviour, and we match after any rival held order stamped earlier. The replay reproduces 95% of
  live outcomes, so the book is right, but queue position among simultaneous held orders is not
  observable.
- **Level-aggregated tape:** "pulled" counts any size decrease without a print at that level, so it
  includes requotes; quote age is per level, not per order.
- **Leaders:** one afternoon; 10 s markout only (no resolution PnL); fill side BUY only.

## Reproduce

```
# tape hours copied from the paper box: /opt/btclat/data/paper/dublin-20261012/raw/2026-10-13/clob_5m-4977{50..55}.tsv.gz -> data/trade/tape/
PYTHONPATH=. python3 -m research.livehold.tape
PYTHONPATH=. python3 -m research.livehold.run
PYTHONPATH=. python3 -m research.livehold.shift
PYTHONPATH=. python3 -m research.livehold.age
PYTHONPATH=. python3 -m research.livehold.leaders --fetch
PYTHONPATH=. python3 -m research.livehold.lbook
PYTHONPATH=. python3 -m research.livehold.lstats
```
