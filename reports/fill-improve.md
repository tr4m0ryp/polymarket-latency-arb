# Order fill improvement: synthesis of 18 ideas and their adversarial reviews (2026-10-14)

## 2026-10-14 14:45 UTC: the live inside hour, the missing $1.65 and the ~100 ms

**The $1.65 is one real fill the bot never saw: order m34, BUY 5 Down at 0.33, matched while its cancel was in flight, on a market that resolved Up.** The bot then read six "order not found" lookups as "0 matched". The ~100 ms of extra ack latency is **on the venue's write path**, not in our process: our client adds ~3-5 ms, and the sender process now built cuts the tail of that further. Run: `dublin-maker-inside-20261014` (13:14-14:14 UTC, `--rule inside`, k = 3 hedged sends, `--record`).

### Reconciliation (public Data API, wallet 0xD664...59E3, 13:00-14:30 UTC)

- **Trades:** exactly one. `/activity` and `/trades`: TRADE BUY 5 Down @ 0.33 = **$1.65**, `btc-updown-5m-1791986700` (14:05-14:10 UTC), tx `0x0704523f...ddc6`, block time 14:09:21. No other trade, no redeem in the window.
- **Order:** our `m34`, oid `<ORDER_ID>` (ask tick 67 = BUY Down at 0.33, 5 sh, GTD expiry 14:12:22). The only order of the run at that token, price and size.
- **Position:** none open. The market resolved **Up** (Gamma `outcomePrices` ["1","0"]), so the 5 Down shares are worth 0 (`/positions`: curPrice 0, redeemable). Balance **68.88367 - 1.65 = 67.23367**, the post-run $67.23 to the cent.

m34 timeline (our SNTP clock; venue stamps from the recorded CLOB market channel):

| t (14:09:xx) | event |
|---|---|
| 17.787 | rule sets the ask target to 67 (fair 0.62, Up book 61/69) |
| 17.790 | insert sent (3 copies, sign 1.0 ms) |
| 17.857 / 17.901 | target 66, then **pull** (target 0): no order id yet, so no cancel possible |
| 18.115 | our 5 sh appear on the Down book at 0.33 (venue stamp): **325 ms after the send** |
| 18.131 | insert ack (RTT 341 ms); cancel sent 1 ms later |
| 18.136 / 18.220 / 18.243 | Up BUY 0.68 x 22.7 prints through us; our level empties; Down SELL 0.33 x 5 prints (our fill) |
| 18.173-18.504 | six GET /data/order lookups: HTTP 200, **no order in the body** |
| 18.416 | cancel ack: "order can't be found - already canceled or matched" |
| 21 (block) | trade settles on chain (Data API timestamp) |

**Why the bot missed it.** Not GTD expiry (14:12:22) and not a lookup gap in time: a **cancel race plus a misread "not found"**. (1) The cancel waits for the insert ack (the manager has no order id before it), and the venue held the insert 325 ms, so the pull at 17.901 could only act at 18.133, after a taker hit us. (2) The cancel's "can't be found - already canceled or matched" went down the unconfirmed path, a lookup. (3) GET /data/order answered 200 with no order, which `parse.lookup` turned into status None and size_matched 0; `None` is not a resting status, so the order was marked done with 0 filled. The read side lags the engine: on the 35 confirmed cancels, the final lookup (30-190 ms after the ack) found **no order 21 times and LIVE 6 times**; only 8 said CANCELED. Lookups alone cannot settle fills. The inferred-fill engine did flag it (`infer`: 5 sh, trade-through at 18.136).

**Fix (btclat/trade/maker, tests in tests/trade/maker/test_settle.py, test_sender.py, tests/trade/test_client.py):**
- **Not found is unknown:** `parse.lookup` returns `found`; a 200 without the order is `unknown` and never books "0 matched" or settles anything.
- **"Gone" cancels:** `parse.gone` reads the venue's reason; a gone cancel frees the slot at once but leaves the order **unsettled**, and its unfilled notional keeps counting in every cap (`Working.at_risk`, `OrderManager.exposed()`).
- **Settlement from three sources** (`fills/settle.py`): lookups at +1 / +3 / +10 s until one returns a final status; **GET /data/trades** (L2, all our trades since the run start, every 2 s while anything works or is unsettled) mapped by `maker_orders[].order_id` (`fills/ledger.py`, each trade id once, FAILED taken back out); the **user websocket channel** (`fills/userws.py`, trade and order events within ms). An order gone > 10 s before a trade read is settled by it. All sources feed the order's matched total, so double sightings count once.
- **Reconcile line:** each live run ends with booked fills vs GET /data/trades vs the public Data API's TRADE rows (`fills/reconcile.py`), printed by the report, plus a `fill_found` note for every fill only the trade records saw.
- Replayed m34 offline: the trade read books 5 sh at 0.33, exposure $1.65, settled; the same trade from the websocket adds nothing.

### Latency: where the ~100 ms goes

Offline from the run's own stamps (`python3 -m research.infra.maker_latency.run --run dublin-maker-inside-20261014`, CSV in data/out/infra/). The CLOB feed's venue stamp of our order appearing on (leaving) the book splits each round trip into **in** (our send to the venue's book) and **out** (book to our ack). Rows with a normal feed lag (< 25 ms, so the stamp is readable), ms:

| ms | n | p10 | p50 | p90 |
|---|---|---|---|---|
| insert: decision to first copy sent (incl. signing) | 36 | 1.5 | 2.9 | 5.9 |
| insert: signing alone | 36 | 1.1 | 1.4 | 4.8 |
| insert: skew between the 3 copies' sends | 36 | 1.3 | 1.4 | 2.0 |
| insert ack RTT (first copy) | 36 | 63 | 139 | 290 |
| insert in: send to on the book | 24 | 17 | 77 | 161 |
| insert out: on the book to ack | 24 | 15 | 51 | 103 |
| cancel ack RTT | 35 | 53 | 85 | 231 |
| cancel in: send to off the book | 25 | 23 | 50 | 104 |
| cancel out: off the book to ack | 25 | 13 | 16 | 81 |
| same process, same minutes: GET /data/order | 41 | 26 | 34 | 42 |
| same process: keep-warm GET /time | 177 | 26 | 29 | 36 |

**Verdict: venue-side write path, not GIL / CPU contention.**
- **Our client is ~3-5 ms:** decision to wire 2.9 ms p50 (signing 1.4), copies leave within 1.4 ms of each other.
- **Same process, same moments, reads are fast:** lookups 34 ms and pings 29 ms (one-way ~14 ms) run on the same HTTP stack under the same feed load.
- **The same receive path answers cancels at one-way speed:** cancel `out` p50 16 ms, insert `out` 51 ms. Our threads read both kinds of answer identically, so the extra ~35 ms after placement is the venue answering inserts later.
- **No load dependence:** corr(insert RTT, feed messages in the 1 s before the send) +0.06; vs CLOB messages only -0.45. Cancels -0.25 / -0.28.
- **All 3 copies wait together:** they ack within 4 ms p50 of each other on three separate TLS connections.
- **The venue is slow at this hour without us:** the idle-loop probe at 13 h UTC on 10-13 got insert 59 / 275 ms (p50 / p90), cancel 45 / 148. The 07 h UTC holdtest got 38-45. Our sends also cluster where the inside gate fires (fast moves, e.g. 11 inserts in 14:09:05-14:09:18), likely the venue's busiest instants.
- **Unexplained:** the remaining gap (139 vs the probe's 59 at the same hour) is either at-touch vs far-from-book orders, or burst timing. The `--far` A/B run tests exactly this.

**Local micro benchmark** (`taskset -c 0,1 python3 -m btclat.trade.maker.send.bench.run --sign emulated`: stand-in venue on 127.0.0.1, 2 CPUs like the c7g.large, k = 3, feed-like load 3.8k msgs/s at 150 us each ~ 0.7 core). Loop-to-loop ms, p50 / p90 / p99:

| sender | load | insert | cancel |
|---|---|---|---|
| thread (today) | idle | 8.9 / 10.0 / 17.0 | 5.2 / 6.4 / 6.9 |
| thread (today) | 3.8k/s | 12.2 / 22.3 / 28.0 | 7.1 / 10.5 / 26.8 |
| proc (new) | idle | 9.1 / 9.9 / 10.3 | 5.6 / 6.5 / 7.2 |
| proc (new) | 3.8k/s | 8.2 / 9.9 / 11.0 | 6.8 / 8.3 / 10.0 |

Feed load costs the in-process sender ~3 ms at p50 and **12-20 ms at p90 / p99**; the sender process holds its idle numbers. Real, but small next to the venue's 100 ms.

**Built:**
- **Sender process** (`--sender proc|ab`, maker/send/): own interpreter and GIL. It signs and sends inserts and cancels on k warm HTTP/2 sessions, keeps them warm itself, and answers on the loop through `add_reader`. It fails closed: a dead sender makes every op `unknown`, the manager stops, cancel-all follows. `ab` routes each op at random and tags `via`, so one run compares both on identical decisions.
- **`--far`:** the rule's exact decisions and timing, every insert at 0.01 (no fill risk, $0.05 per order at most).
- **Analysis and benchmark:** the offline split (research/infra/maker_latency/) and the local benchmark (maker/send/bench/).

**Not built, on this evidence:**
- **uvloop / orjson / dropping `--record`:** they shave our ~3-5 ms, not the venue's ~100 ms. `--record` stays on for the A/B run, because the book-stamp split needs the CLOB feed and both arms carry it equally.

**What would have saved m34:** a cancel that does not wait for the ack. The order id is the EIP-712 hash of the signed order (idea 2 above), so it can be computed locally. The pull fired 230 ms before the ack. The open risk is a cancel that reaches the venue before its order; it needs a re-cancel on the ack. Because the venue held this insert 325 ms, ack-gated cancels lose every race in that state. This is the latency lever that matters for fills, more than our client.

**Next (coordinator, box):**
- **A/B run:** 1 h `--far --sender ab` at the same UTC hour (command in btclat/trade/deploy/DEPLOY.md). Read `via` thread vs proc (our process) and far vs this run's at-touch RTT (venue order location).
- **Default sender:** switch to `--sender proc` if it wins at p90.

## 2026-10-14 12:45 UTC: inside gate passes its pre-registered sealed-hours test

**Verdict: GO for a live 1 h test at 5 shares, `--rule inside` with h = 0.** All three primary criteria of `data/out/predict/inside-prereg.json` (frozen 12:37:36 UTC, config sha256 `85df69ed...`, code and model hashed, committed in 57390e5 before any sealed scoring) pass on 360 sealed markets (30 h). With the rival-improver haircut, at L = 50 ms and 60-share quotes, the inside gate earns **+15.4 c/$ [+5.3, +23.8]**, +$208/day, against **-8.1 c/$ [-17.0, +0.4]**, -$539/day for the frozen maker base_lat2. Paired gain **+$747/day [+201, +1,386]**, drop-top-5 +$215/day. Most of the paired gain is the base's loss avoided; the inside arm's own money is +$208/day at 60 sh and **+$34/day at our 5-share size** (+15.3 c/$ [+5.2, +24.9], 4.7 fill events/h). Hysteresis h = 0.005 ties h = 0 and does not earn its place.

**Incidence (test 1, dry run, before the freeze).** The inside gate (fair -/+ 0.04 strictly inside the spread, pull -0.02) would have inserted **675 times in 4.1 h, ~166/h** (full hours 154 / 211 / 224 per hour; partial 08:15-09:00 67, 12:00-12:18 19). With h = 0.005: ~139/h. Both clear the ~130/h capacity line. On the logged quote rows (only rows where the frozen rule changed its quote), 4-6% had an inside quote available: 105 / 409 / 268 / 341 / 29 rows per clock hour. The sealed Dublin hours were quieter: 80 inserts/h there, so capacity varies about 2x with the tape.

**Method.** `research/predict/inside/` (prereg, engine, run, report). The fill-improve study's mk engine, reproduced exactly with the haircut off (checked on 6 local markets: same fills, inserts and rejects). Insert and cancel latency = min of 2 draws from the Dublin probe quantiles, + (L - 50 ms). The cancel waits for the insert ack. Hold 0.27 s, model v1_L50. Haircut: we sit behind the largest depth at our price seen between our decision and one insert latency after our order went live, and crossing orders also eat that queue first. Sealed sets: the Dublin paper recording from 2026-10-12 22:05 UTC (312 markets, after the local recorder that every selection used had stopped) and the 4 h dry run (48 markets, ingested with hour 12:00-12:18 added). Market bootstrap B = 2000.

Pooled sealed hours (360 markets, 30 h). Base = base_lat2, no haircut. Inside arms with the haircut. gain = paired 10 s markout $/day vs base, 95% CI:

| size | L ms | arm | fills/h | ins/h | c/$ [95% CI] | $/day | gain $/day [95% CI] | drop-top-5 gain |
|---|---|---|---|---|---|---|---|---|
| 60 | 50 | base_lat2 | 37.6 | 3,625 | -8.1 [-17.0, +0.4] | -539 | 0 | 0 |
| 60 | 50 | inside | 7.0 | 91 | **+15.4 [+5.3, +23.8]** | +208 | **+747 [+201, +1,386]** | +215 |
| 60 | 50 | inside_h0.005 | 6.2 | 77 | +21.6 [+7.2, +33.7] | +257 | +796 [+238, +1,452] | +264 |
| 60 | 100 | base_lat2 | 59.7 | 3,625 | -14.4 [-21.4, -7.3] | -1,329 | 0 | 0 |
| 60 | 100 | inside | 7.4 | 91 | +11.3 [-1.4, +20.7] | +173 | +1,503 [+789, +2,289] | +905 |
| 60 | 100 | inside_h0.005 | 6.8 | 77 | +14.0 [+2.2, +24.3] | +183 | +1,513 [+797, +2,296] | +915 |
| 60 | 150 | base_lat2 | 84.3 | 3,625 | -7.1 [-12.6, -1.9] | -867 | 0 | 0 |
| 60 | 150 | inside | 8.4 | 91 | +22.0 [+5.2, +33.8] | +359 | +1,226 [+555, +1,929] | +747 |
| 60 | 150 | inside_h0.005 | 7.7 | 77 | +22.0 [+4.5, +33.6] | +345 | +1,212 [+546, +1,890] | +736 |
| 5 | 50 | base_lat2 | 21.9 | 3,625 | -4.8 [-11.4, +1.7] | -49 | 0 | 0 |
| 5 | 50 | inside | 4.7 | 91 | **+15.3 [+5.2, +24.9]** | +34 | +83 [+19, +150] | +28 |
| 5 | 50 | inside_h0.005 | 4.0 | 77 | +19.6 [+3.9, +33.9] | +38 | +87 [+29, +153] | +30 |
| 5 | 100 | inside | 4.1 | 91 | +13.0 [+2.5, +23.6] | +27 | +136 [+63, +213] | +77 |
| 5 | 150 | inside | 4.3 | 91 | +17.0 [+5.4, +27.6] | +34 | +107 [+41, +174] | +62 |

By set (60 sh, L = 50, inside with haircut):
- **Dublin sealed (312 markets):** +17.1 c/$ [+5.9, +26.6], gain +$772 [+149, +1,479], drop-top-5 +$157. Passes alone.
- **Dry-run hours (48 markets):** +9.2 c/$ [-8.2, +28.9], gain +$585 [-398, +1,536], drop-top-5 -$205. Positive point, too small to decide alone.
- **Base on the dry hours:** -3.0 c/$ at 60 sh, -4.5 c/$ at 5 sh. This matches the same-market sim's +0.79 [-9.25, +11.16]: the frozen maker is about zero or worse at realistic latency.

Robustness and caveats:
- **Haircut barely bites on inside:** 95% of inside fills are prints through our price, which clear our whole level whatever the queue. Haircut off vs on: 14.6 vs 15.4 c/$. It costs the base 1-3 c/$.
- **Edge is concentrated:** dropping the inside arm's own 5 best markets leaves +8.8 c/$ at L = 50 but +0.8 c/$ at L = 100. The arm's own CI excludes 0 at L = 50 and 150, not at L = 100.
- **Sim inserts are target changes,** not the bot's coalesced orders: the bot made 79 inserts/h where the sim counts ~3,300/h for the same rule. Read ins/h as relative.
- **Fills are counterfactual.** The tape never contained our order, and the dry run proved the live mechanics only for the frozen rule. The live test measures exactly that gap.
- **5-share economics:** ~4.7 fill events/h and +$34/day. One hour gives about 5 fills, which checks the mechanics (accept / post-only reject rate, fill rate vs sim) but proves no edge. Edge needs about 20+ live hours.

Hysteresis (idea 3). The pre-registered swap rule (h = 0.005 replaces h = 0 only if it beats h = 0 at both L = 100 and 150) fails: +$1,513 vs +$1,503 at L = 100, +$1,212 vs +$1,226 at L = 150. It cuts inserts 15% at flat money. **Class: lost a comparison** (a tie with h = 0). The predicted latency benefit did not appear, because the inside gate already quotes rarely. Reopen with the local-hash cancel+replace manager (idea 2), where churn costs more.

Secondary criteria (verdict.json): all pass (L = 100 / 150 gain > 0, Dublin alone CI > 0, dry point > 0, 5-share markout > 0, h-arm gain > 0).

Live 1 h test (explicit approval needed; commands in btclat/trade/deploy/DEPLOY.md):

```
# dry 1 h (anywhere with the feeds; money caps logged as would-skip, not applied)
nice -n 10 python3 -m btclat.trade maker --dry --rule inside --hours 1 --ntp amazon --record --run dublin-makerdry-inside-<TAG>
# live 1 h on the Dublin box, after the rsync deploy step in DEPLOY.md (5 sh, $25 open, $10/market, $10 day loss cap)
sudo -u btclat env BTCLAT_CONFIG=/opt/btclat/.config/btclat bash -c 'cd /opt/btclat && \
  .venv/bin/python -m btclat.trade maker --i-approve --rule inside --hours 1 --ntp amazon --record --run dublin-maker-inside-<TAG>'
python3 -m btclat.trade.report --run dublin-maker-inside-<TAG>
```

Pass bar for the live hour: no post-only or band violations, inside inserts accepted at the dry-run rate, and fill events within 0.5-2x the sim's 4.7/h. The markout is reported but not judged on n ~ 5.

## Verdict (synthesis, 2026-10-14 11:30 UTC)

**The biggest lever is order mechanics, not the model.** Once the simulator uses realistic latency (the probe distribution with ack-wait), the frozen maker vm_fair0.03_p-0.03 falls from **+5.1 c/$ to about +1 to +2.8 c/$**. Three changes look able to win most of that back, and maybe more. All three can be tested offline at $0 within 24 h:

1. **Inside gate.** Rest a quote only where it becomes the new best price strictly inside the spread. Pull loosened to -0.02. Sim result: **+7.5 c/$ against +1.0 for base at the same latency**, with 8-13x fewer inserts. This is the strongest mechanism. Its evidence is in-sample and counterfactual, so it needs a rival-improver haircut on sealed hours.
2. **Cancel the moment a pull fires.** Compute the order ID locally (the EIP-712 order hash, a hash of the signed order) and send cancel and replacement together, without waiting for the insert ack. In the replay, today's manager sequencing gets **+2.6 c/$ ($155/day)** of the sim's +5.1 c/$ ($328/day). One unresolved conflict: a second engine found that cancel-before-ack did *worse*. Reconciling the two engines is the first test.
3. **Hysteresis on the quote flag.** Enter a side at p < pull - h. Exit at p >= pull, the same as now. The pull threshold itself must not move: loosening it to -0.01 loses -$564/day, CI below 0. This cuts churn 1.5-2.7x at flat $/day. The claimed benefit is robustness to cancel latency, and it has to be shown at L = 100/150 ms.

The taker paths stay closed. The anticipatory pre-send taker shrinks to **+0.13 c/$ cost-weighted** once low-price tokens are removed. Hedged sends already ship (`--fanout`). The maker rebate is real (**+0.55-0.6 c/$** on every maker fill) but should not drive arm selection.

## Ranked ideas (survived or weakened)

| # | Idea | Mechanism | Evidence | Expected gain | Cheapest test | Time |
|---|---|---|---|---|---|---|
| 1 | Inside gate + pull -0.02 | Quote only when fair -/+ 0.04 is strictly inside the spread. Our unheld post-only insert (45 ms) gets ahead of held sell flow (+170 ms) | 719 mkts, probe latency k=2: +7.58 c/$ [+4.0, +11.5], $573/day vs base +0.98, $128/day. Paired +$445 [-61, +973]. dev3 reverses (4.4 vs 7.8). 90% of fills are trade-throughs | ~+6 c/$, 3-4x $/day on 1/3 of the capital, 8-13x fewer inserts | Count how often fair -/+ 0.04 sat inside the live spread in the dry run's quotes-*.tsv.gz, then a sealed-hours replay with a rival-improver haircut | 2 min + 40 min |
| 2 | Local-hash cancel, cancel and replace together | Cancel without waiting for the insert ack. Fire the replacement with the cancel | 73% of dry-run pulls hit an in-flight insert (94/243 ms vs 52/80 ms). seqsim: current +2.63 c/$ vs +5.07 (= sim). Paired +$173 [-18, +362]. mk engine noack: worse (+0.07 vs +0.98) | Up to +$170/day at sim scale, ~2x markout $ | Reconcile seqsim and mk engine on the same 575 markets and the same latency draws. Check hash == orderID offline if any signed body was logged | 1 h |
| 3 | Insert hysteresis (enter at pull - h) | Quotes live long enough to matter. Fewer cancels in flight | h=0.005: +7.1 c/$, $380/day (local hash). Current manager: +5.85, $257. $/day CIs overlap the base. Exit-loosening to -0.01: -$564 [-923, -161] | Flat $/day, +2-5 c/$, 1.5-2.7x fewer changes. Real gain only if the advantage grows with L | Pre-register h=0.005, current manager, paired vs h=0 at L = 50/100/150 on sealed hours | 1 h |
| 4 | Wave clock as an OR latch | Side goes out on (model pull OR perp onset >= 1 bp against it) and stays out 500-600 ms. Asymmetric re-quote | Excess aligned taker volume ~0 at 0-250 ms after onset, 54% by 400 ms, 96% by 1 s (exchange clocks). Aligned prints <= 350 ms: -6.6 c/$ | Unknown, maybe +0.5-2 c/$. Mainly makes quotes live longer | Sim vs vm_fair0.03_p-0.03, L = 50/100. Pass: paired markout not worse and >= 3x fewer changes | 1 h |
| 5 | Count the maker rebate | Pool = 20% of taker fees per market, pro rata. Gives 0.014 p(1-p) per maker share | Gamma feeSchedule rebateRate 0.2. +0.55-0.59 c/$ on every vm arm. Gross vs net pool unverified | +0.6 c/$, +11% on the frozen arm. Tie-breaker only | Add as a separate column in fills.score. Reconcile pUSD after the first live day | 15 min |
| 6 | Deep rung, pull = distance | Rung at fair -/+ 5 c, pulled only on a predicted move > 5 c. Held takers' tight limits shield deep levels | deep5 +11.8 c/$, +$181/day [-4, +379]. Control deep5p3: +1.4. Tape: aligned-wave prints >= 5 c beyond: -0.4 [-4.2, +3.8] (no harm, no edge) | +$0-180/day, a fat tail from few moves | (a) Calibration: realized vs predicted moves in [-5, -3] c. Maybe base pull -4/-5 does the same with one rung. (b) Queue-aware tape count of back-of-queue reach | 45 min |
| 7 | Back-of-queue veto | No touch quote in a 1 c book unless ~25 shares or fewer are ahead | Level not cleared +0.97 vs cleared -4.75 c/$. Ahead <= 25: +0.49 [-0.01, +0.96]. Dublin joins behind 120-300 sh | <= +1 c/$ if queue fills are >= 20% of vm fills | Tag vm sim fills cross / through / queue and by ahead at join | 30 min |
| 8 | Final-minute maker cutoff | Book beats our fair in the last 10-30 s (TWAP study), so the maker is likely adverse there too | Brier mid vs ours: 0.062 vs 0.096 (10-30 s), 0.057 vs 0.294 (0-10 s) | Removes a likely leak | vm fills markout by secs_left 0-10 / 10-30 / 30-60 | 15 min |
| 9 | Fair-velocity width (from the time-left idea) | Half-spread scales with expected fair move over the cancel latency (dp1) | Time-left buckets not monotonic. Hard gate lost on 2 of 3 segments | Insert budget, not markout | Continuous fit of markout on dp1 with a block bootstrap. Keep if the slope > 0 in every segment | 30 min |
| 10 | Center band 0.30-0.70 | Narrower quoting band | +8.1 vs +5.1 c/$, $/day paired -27 [-209, +167]. Bucket shape not monotonic (noise) | Capital efficiency only | Fresh hours: does the 0.2-0.3 bucket stay negative on its own? | 25 min |
| 11 | Heartbeat + user ws | Dead-man switch replaces the 185 s GTD backstop. Fills pushed instead of REST lookups | Docs confirm both. 12x exposure cut does not hold (stale quotes get hit within seconds) | Crash safety. Latency gain unmeasured | Passive A/B timestamp log of user ws vs tape+REST in the next live session | live |

## Refuted or closed

| Idea | Reason | Class |
|---|---|---|
| Hedge inserts and cancels on 2-3 connections | Already shipped (ops/hedge.py, `--fanout`). The "n = 0 copies" premise came from DryOps. What remains useful: single-send latency drops the frozen arm to ~+2.8 c/$ | Already built, not new |
| Trigger-conditioned standing | Real leader flow earns +2-4 c/$ before fees, so makers on the other side lose that much. The rebate (~0.6 c/$) cannot close the gap | Proven closed under these premises: leader pre-fee markout >= +2 c/$, rebate <= 25% of fee. Reopen if a real-fill join shows the vetoed side >= +2 c/$ |
| Anticipatory pre-send taker | +5.5 c/$ is 74 fills at px <= 0.20 (+90.7 c/$). Cost-weighted +0.13 c/$. Sign flips 7 times in 12 h | Never tested (the evidence was an artifact). Reopen with a trained still-perp timing model, cost-weighted, 0.3-0.7 band |
| Synthetic cancel via balance starvation | Docs: a delayed order likely reserves its balance at acceptance, so the dummy order would be rejected. Also no held strategy left to protect | Never tested. Likely proven closed. Premise: balance is reserved at acceptance |
| Final-minute TWAP taker | Book mid beats our Chainlink proxy on Brier in every bucket. -9 to -87 c/$ | Lost a comparison. Reopen only with exact settlement replication |
| Let missed takers rest (GTC fallback) | Fills on reversal: -9.7 c/$ [-13.8, -5.4] at 30 s | Lost a comparison (FAK and post-only already guard against it) |
| Move the taker to 15m for staleness | 15m is smaller, not staler. 12 quiet hours, fat tails | Lost a comparison on this sample. Recheck on a volatile day, cost-weighted |

## Test order, next 24 h, $0

1. **Inside-gate incidence** (2 min). Count from the running dry run's quotes-*.tsv.gz how often fair -/+ 0.04 sat strictly inside the spread. Well below ~130/h means the arm is capacity-starved, so stop there.
2. **Engine reconciliation** (1 h). seqsim says local-hash cancel+replace recovers the sim's +5.07. The mk engine says noack is worse. Run both on dev3+test3 with identical latency draws (probe, k=2, insert/cancel corr 0.64). Decide which manager is right before any code change. The mk engine's noack may not fire the replacement together with the cancel, and that difference would explain the conflict.
3. **Fill tagging** (30 min). Tag vm fills by rule (cross / through / queue), ahead at join, and secs_left. This settles idea 7's ceiling and idea 8's cutoff in one pass.
4. **Pull calibration** (20 min). Realized vs predicted 10 s move for p in [-5, -3] c. If the model over-predicts, test base pull -4/-5 before building a second rung.
5. **Freeze and score on sealed hours** (1-2 h). Pre-register inside half 0.04 pull -0.02, h = 0.005, wave latch 600 ms, and the rebate column. Score on the Dublin paper hours after 2026-10-12 22:03 that no selection has touched, at L = 50/100/150 with probe latency. Use base_lat2 as the baseline arm, a market bootstrap, paired $/day, and drop-top-5. Apply the rival-improver haircut to inside: we sit behind any new level at our price that appears within our insert latency.
6. **Wave-clock latch replay** (15 min). Replay the localdry decisions through the latch plus hysteresis state machine and count inserts/h.

**Needs a small live test (explicit approval, 5-share clips):**
- One insert to verify orderID == build_order_hash, if no logged signed body allows an offline check.
- Live maker with `--fanout 2`. Check "every copy" ack rows and first-copy cancel p90 <= 60 ms over hundreds of cancels.
- User-channel vs REST fill timestamps, logged passively.
- Heartbeat: one resting order at 0.01, which should vanish 10-15 s after heartbeats stop.
- Rebate reconciliation after the first live maker day (also settles gross vs net).

## Novel contributions

| Claim | Beats | Falsifiable test |
|---|---|---|
| **Taker-hold arbitrage by the inside quote.** On a venue that holds only marketable orders, a fast post-only quote at a new inside price captures held flow that was aimed at the old touch. This is the asymmetric-delay prediction (Baldauf and Mollner 2020; Brolley and Cimon 2020) put into practice as a quote gate | Join or peg at the touch, and the frozen value maker (+1.0 c/$ at realistic latency) | Sealed hours with the rival-improver haircut: paired $/day CI > 0 against base_lat2 |
| **The venue hold as a clock.** Toxic taker flow arrives as a wave 250-1000 ms after a Binance onset, on exchange timestamps. Makers therefore have a hard deadline (onset + 250 ms), not a "cancel as fast as possible" target | Per-tick model pull alone | Latch arm: markout not worse with >= 3x fewer changes. Weekly profile.py re-measurement tracks hold changes |
| **Cancel latency is a manager property, not a network one.** Ack-wait sequencing roughly doubles effective cancel latency when quotes flicker, which halves the realised edge | Sims that model network latency only | Live: decision-to-cancel-ack for in-flight pulls vs live pulls, before and after the manager change |
| **Pull threshold = rung distance.** Each resting rung gets a pull threshold equal to its distance from fair (deep5 +11.8 vs deep5p3 +1.4 c/$) | Single-rung maker | Joint 2-rung sim on fresh hours, paired over base |

**Publication assessment.** The inside-gate and wave-clock results are a credible empirical microstructure note on a speed-bumped prediction market, if they replicate on sealed hours with the haircut. Today they are in-sample, and the strongest result's paired CI includes 0. Do not claim novelty for the speed-bump theory itself; the contribution is the measured venue and the gate.
