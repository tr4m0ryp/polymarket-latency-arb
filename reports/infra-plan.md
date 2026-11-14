# Infra plan: reacting to a Binance move at Polymarket's matching engine

Date 2026-10-10. Read-only research: no orders, no credentials, no servers rented. Tags on every
number: **[M]** measured this session (file under `data/out/infra/`), **[S]** sourced (URL in
Sources), **[E]** estimated (arithmetic or judgement, stated). Code: `research/infra/`.

## Verdict

**An order can reach the CLOB 69-78 ms after a Binance event, but a taker order cannot match
there in under ~219 ms.** BTC up/down markets hold every marketable order for **150 ms** before
matching (the "taker delay"; `itode: true` on the live 5m and 15m markets [M]). The "50-100 ms"
target is reachable for one thing only, order **arrival**, and only with a private Tokyo-Europe
route; it is meaningful for **cancels and requotes** (which are not held) and for takers only by
**anticipation** (firing 69-113 ms before the spot onset trade to fill within 150 ms of it).

- **Arrival floor, one way:** AWS-only builds 108-123 ms; split build on a McKay/BSO-class link
  69 ms (London co-location) or 78 ms (Dublin); fiber great-circle floor ~50 ms; under 50 ms is
  physically impossible from a Binance event.
- **Earliest taker fill after the Binance trade:** cheap Dublin build ~263 ms, fast build ~219 ms,
  physical floor ~200 ms. The incumbents' first reprice lands a median 201 ms after it, so
  even the physical floor only ties their median; it wins **31% (cheap) / 43% (fast)** of 1 bp bursts.
- **Edge at those fill times** (real fills, 0% fee tier): about **+2-3 c per $ (cheap)** and
  **+2-5 c per $ (fast)**, against 12-20 c for fills within 150 ms of the onset. The big edge
  belongs to whoever fires earlier, which is a trigger problem, not a wire problem.
- **Build now:** the cheap path (one AWS Dublin VM, **~$18/month**, ~113 ms arrival). Do **not**
  buy a link at $200 capital: it moves fills ~44 ms earlier for a quote-only price.
- **Free wins found today** (bigger than most infra choices): 1-4 of every 5 Binance websocket
  connections run **~95-107 ms late** (perp up to ~350 ms) from the same gateway IP [M]; the
  shipped order client signs in **11.6 ms** on a pure-Python backend vs **0.27 ms** on a
  hand-rolled path [M]; an idle CLOB connection costs **+20-40 ms** after 5 s of silence [M].

## 1. Physical floor, Binance event to order at the CLOB (one way)

Great-circle Tokyo-London 9,559 km, Tokyo-Dublin 9,585 km [E: haversine]. Light in fiber
(n ~1.47) needs **46.8 ms**, in vacuum 31.9 ms. Real routes are longer: 66 ms one way equals
13,477 km of fiber, so the sub-140 ms RTT routes cross Eurasia overland; anything via the US or
Suez is 17,000 km+ [E]. AWS's own backbone runs ~2.2x the fiber floor.

| architecture | signal leg | order leg | **arrival** | + 150 ms hold = taker fill | status |
|---|---|---|---|---|---|
| A Tokyo single host | 0.3-1.2 [M] | ~122 via Cloudflare NRT [M] | **~123** | ~273 | API allowed (JP) |
| B Dublin single host | 100-101.5 [M] | ~11 via Cloudflare DUB [M] | **~113** | ~263 | API allowed (IE) |
| C London host via Cloudflare | 104-107 [M] | ~9.5 [M] | ~116 | ~266 | UK IP: only via co-location form |
| D London co-location, no Cloudflare | 104-107 [M] | ~2 [E] | ~108 | ~258 | KYC/KYB form |
| E Tokyo box + AWS backbone + Dublin box | 0.6 + 100-101.5 [M] | ~11 [M] | ~113 | ~263 | no gain over B |
| F Tokyo box + McKay/BSO + Dublin box | 0.6 + <=66 [S] | ~11 [M] | **~78** | ~228 | quote needed |
| G Tokyo box + McKay/BSO + London co-location | 0.6 + <=66 [S] | ~2 [E] | **~69** | ~219 | quote + KYC/KYB |
| F' same with Avelacom | 0.6 + 69.8 [S] | 2-11 | 73-82 | 223-232 | quote needed |
| H fiber great-circle + co-location | 0.6 + 46.8 [E] | ~2 [E] | ~50 | ~200 | not buildable today |

Every row adds ~0.4 ms of parse, decide and sign on the fast Python path [M]. One-way order legs
are half the measured warm request round trip (TTFB), which slightly overstates them.

**What "50-100 ms" requires:** arrival <= 100 ms needs an intercontinental leg <= ~88 ms, which only
the private Eurasian routes offer (McKay sub-132 ms RTT, BSO microwave < 66 ms one way, Avelacom
139.6 ms RTT). Every cloud backbone and the public internet measure 196-232 ms RTT. Arrival
<= 50 ms is below the fiber floor. **Matching** within 50-100 ms of the Binance trade is impossible
for a reacting taker under the hold; it needs an order sent 50-100 ms *before* the trade, i.e.
anticipation. Cancels are not held, so a requoting maker can act inside 69-78 ms (fast) or
~113 ms (cheap).

## 2. The budget, component by component

| component | number | tag | note |
|---|---|---|---|
| Binance match to push, raw `@trade` and `@bookTicker`, spot and perp | E-T p50 0 ms, p99 1 ms | M | `binance_probe.json` |
| USD-M `@aggTrade` | E-T 150 ms, arrives 150 ms after raw `@trade` | M, S | batched every 100 ms: never a trigger |
| per-connection delivery lag, same gateway IP | in 3 runs, 1-4 of 5 spot and 1-2 of 4 perp connections ran p50 **95-107 ms** late (perp up to 254-358 ms, p90 ~700 ms, in the busiest run) | M | `binance_probe_replicates.json`; the recorder's connections were mostly fast (receipt lag p50 110-112 ms) |
| combined vs raw stream | no systematic difference; the lag is per connection | M | open 3-4, first arrival wins |
| `data-stream.binance.vision` vs `stream.binance.com` | within ~1 ms on fast connections | M | |
| spot SBE (`stream-sbe.binance.com`) | needs an Ed25519 API key: HTTP 400 "No X-MBX-APIKEY header" | M, S | "better latency than JSON", no figure; 65-66 B vs 135 B messages |
| spot FIX market data | Ed25519 key with FIX_API_READ_ONLY | S | |
| USD-M SBE / FIX | not offered | S | |
| `fstream-mm.binance.com` (market-maker endpoint) | HTTP 403 | M | whitelist only |
| perp vs spot trigger head start (venue clocks, 20 h, 510 bursts) | median **1 ms**, p75 57 ms, 1 bp rule; 0.75 bp: median 4.5 ms, 63% false alarms | M | `perp_lead.json` |
| Binance AZ | apne1-az1 / apne1-az4 | S | McKay venue page; AWS az4 outage of 2025-04 hit Binance |
| AWS Tokyo to Binance gateway | TCP RTT 0.4-2.3 ms by AZ | M | Globalping probes in ap-northeast-1 |
| AWS Tokyo-Dublin / Tokyo-London / Dublin-London | RTT 198.5-203.6 / 207.7-214.8 / 8.8-12.7 ms | M | cloudping p50: 203.7 / 214.7 / 11.3-12.0 [S] |
| Avelacom via Direct Connect, Tokyo-London | RTT 139.6 ms (vs 210.0 VPC peering) | S | AWS blog, test 2026-04-28 |
| McKay Brothers Tokyo to LD4 / AWS Dublin | RTT < 132 ms | S | press 2025-02; serves Polymarket in eu-west-2 and eu-west-1 |
| BSO + CryptoStruct microwave, Tokyo crypto data to London | < 66 ms one way | S | sponsored, Aug 2026, price unpublished |
| BSO Tokyo-London (Kraken route), Colt | < 140 ms RTT; < 159 ms (2017) | S | |
| Azure, GCP, Megaport, public internet | 204-232 ms RTT | S | none beats AWS |
| Far North Fiber (Arctic) | ~142 ms RTT claimed, not before 2027 | S | slower than today's best |
| Cloudflare edge from a same-city AWS host | TCP RTT 1.0-2.6 ms (DUB, LHR, NRT) | M | |
| Cloudflare + origin, `GET /time` | TTFB 19 ms (London), 22-23 ms (Dublin), 242-245 ms (Tokyo) | M | so ~15 ms of every round trip is Cloudflare + origin, not distance |
| co-location bypasses Cloudflare? | unknown; docs promise "lowest possible latency" | E | worth ~5-8 ms one way if it does |
| cold TLS handshake to Cloudflare | ~57 ms | M | never connect on the hot path |
| warm request, HTTP/2 vs HTTP/1.1 (Paris) | p50 26-28 vs 27-30 ms | M | no single-request gain; HTTP/3 not offered |
| idle penalty | +20-40 ms after >= 5 s idle; flat for gaps <= 2 s | M | send a keep-warm request every ~1 s |
| websocket order entry | none: REST `POST /order`, batch of 1-15 on `POST /orders` | S | user websocket is receive-only |
| rate limit | `POST /order` 200/s sustained | S | not binding |
| signing, shipped `py-clob-client-v2` 1.2.0 | 11.6 ms (pure-Python secp256k1), 1.4 ms with `coincurve` | M | `sign_bench.json` |
| signing, hand-rolled EIP-712 digest + libsecp256k1 | 0.27 ms total; raw sign 77 us | M | same signature bytes as the library (checked) |
| signing in Rust | ~0.05-0.1 ms | E | gain over fast Python: ~0.2 ms, i.e. noise |
| L2 HMAC header + JSON body | 24-45 us | M | must be fresh per request |
| pre-signed orders | allowed: V2 `timestamp` is "for uniqueness", no freshness rule documented | S | pre-sign each side x price level; ~3 ms per refresh of 10 orders |
| **taker hold, crypto up/down** | **150 ms** (changelog 2026-09-04); 250 ms on older pages | S, M | `POST /order` returns after the hold |
| cancel of a resting order | not held | S | the hold protects makers |
| match to public websocket | 13 ms to Paris | M | run 1 |

## 3. Measured from here today (no spending)

- **`research/infra/sign_bench.py`:** order build + sign with a throwaway in-memory key, never
  sent. The shipped client is the slowest link on the host (11.6 ms); install `coincurve`
  (1.4 ms) or use the hand-rolled path (0.27 ms).
- **`research/infra/http_probe.py`:** warm `GET /time` and `GET /book` on HTTP/1.1 and HTTP/2,
  idle-gap sweep. POP is CDG from Paris; the `__cf_bm` cookie shows Cloudflare bot management
  is on.
- **`research/infra/binance_probe.py`:** 9-13 parallel public streams, matched by trade id. It
  found the slow-connection effect, aggTrade's 150 ms batching, SBE's key requirement and the
  403 on the market-maker endpoint.
- **`research/infra/globalping.py`:** free Globalping probes inside AWS ap-northeast-1, eu-west-1
  and eu-west-2. TCP RTT to Binance, across the AWS backbone (regional DynamoDB endpoints) and
  HTTPS TTFB to the CLOB.
- **`research/infra/perp_lead.py`:** perp vs spot onset on Binance's own clocks over 20 h of run 2.
  The perp's head start is small at the median. The earlier "perp leads by 50-100 ms" came from
  receipt clocks and holds for roughly the top quarter of bursts only.
- **`research/infra/budget.py`:** joins the arrival model with run-1 first reprices and runs 1+2
  burst-side taker fills (section 5).
- **Not measurable from here:** one-way Binance to a host inside AWS (needs a synced clock),
  Cloudflare behaviour under co-location, `POST /order` timing (needs credentials and the user's
  approval).

## 4. Two builds

### (a) Cheap: one VM in AWS Dublin, ~113 ms arrival, ~$18/month

1. **Region / AZ:** `eu-west-1`, any AZ (Cloudflare DUB is 1.0-1.5 ms from AWS Dublin [M]).
   API orders allowed from IE; check `GET https://polymarket.com/api/geoblock` on the host first.
2. **Instance:** `t4g.small` (2 vCPU burstable, 2 GB), $0.0184/h = **$13.43/month** [S]. Use
   `c7g.medium` ($0.0388/h = $28.32 [S]) if CPU credits run low; a Python bot at ~100 msg/s
   sits well under the t4g.small baseline [E].
3. **Fixed extras:** public IPv4 $0.005/h = $3.65; 8 GB gp3 ~$0.70; transfer ~$0.50 [S/E].
   **Total ~$18/month**; a new AWS account's $100-200 credits cover months of it [S].
4. **OS:** Ubuntu 24.04 arm64; chrony on the AWS Time Sync source (169.254.169.123); no other
   tuning. Kernel bypass saves microseconds on a 100+ ms path: skip it.
5. **Hot path, Python 3.12** (network dominates): asyncio + uvloop, orjson, `coincurve`.
   - Signal: 3-4 connections each to perp `/public` `@trade`+`@bookTicker` and spot `@trade`,
     no compression; dedupe by trade id, first arrival wins. Recycle a connection that runs
     > 20 ms behind its peers for a minute.
   - Orders: one HTTP/2 connection to `clob.polymarket.com`, kept warm with a `GET /time` every
     1 s. Orders pre-signed per side and price level, HMAC computed at send, FAK.
   - Trigger and order code in one process; recording and logging in another, never on the
     hot path (the recorder showed 260-637 ms receipt tails in busy hours [M]).
6. **Expected:** arrival ~113 ms, taker fill ~263 ms after the Binance trade; cancels land
   ~113 ms after it.

### (b) Fast: Tokyo signal box + private link + order box, ~69-78 ms arrival

1. **Tokyo box:** `ap-northeast-1`, AZ chosen by probe among apne1-az1/az4 (Binance [S]).
   `c7g.medium` $0.0455/h = $33.22 [S]. Rust: tokio-tungstenite, simd-json, the same
   multi-connection fan-in. It sends a ~100-byte trigger message, not raw data.
2. **Link** (quote only, no public prices [S]):
   - McKay Brothers (< 132 ms RTT, AWS Tokyo to AWS Dublin and London)
   - BSO Crypto Connect Plus / BSO + CryptoStruct microwave (< 66 ms one way to London)
   - Avelacom (139.6 ms RTT via Direct Connect)
   If the vendor hands off over AWS Direct Connect: hosted 50 Mbps port $0.029-0.03/h, about
   **$21-22/month per end**, plus $0.041/GB out of Tokyo [S]. Vendor fee **[E]: hundreds to low
   thousands of $ per month**. Public anchors are Beeks crypto from £258/month on other routes,
   and wavelengths at $9-80k/month [S].
3. **Order box:**
   - F: `eu-west-1`, c7g.medium $28.32 [S], API allowed, ~78 ms arrival.
   - G: `eu-west-2` via Polymarket's KYC/KYB co-location form, ~69 ms arrival if Cloudflare is
     bypassed [E].
   Rust, using Polymarket's `rs-clob-client-v2` or hand-rolled signing, keep-warm and pre-signed
   orders as in (a).
4. **Monthly:**
   - Known: 2 x c7g.medium ~$62 + 2 IPv4 $7.30 + EBS $1.50 + DX ports ~$43 = **~$114 known**
   - Unknown: the vendor fee
5. **Expected:** arrival 69-78 ms, taker fill 219-228 ms, cancel 69-78 ms after the trade.

### Measure each hop once machines exist (`research/infra/aws_probe.sh`)

The script launches five self-terminating `t4g.micro` probes: Tokyo az1/az2/az4, Dublin and
London. Each runs the Binance and CLOB probes plus the geoblock check, prints results to its
serial console and terminates itself within 30 min. Cost **~$0.05 total** [E from S prices].

1. `aws login`: refresh the expired session. Free.
2. `bash research/infra/aws_probe.sh launch --yes`: about $0.05 for five instances x 0.5 h.
3. About 15 min later, `bash research/infra/aws_probe.sh collect`: free. Writes
   `data/out/infra/aws/<az>.txt`.
4. `bash research/infra/aws_probe.sh cleanup`: free. Terminates anything still running.

What to read from the results:
- **Tokyo AZs:** the AZ with the lowest receipt minus E, which is valid there because of
  chrony; that sets the Tokyo box's AZ.
- **Dublin:** one-way Binance receipt lag (expect ~100 ms) and warm CLOB request time (expect
  ~22 ms). If both hold, build (a) runs at ~113 ms.
- **Every region:** the geoblock answer from that AWS region's IP.
- **Later, needs the user's explicit approval and API credentials:** time `POST /order` with a
  post-only buy of 5 shares at 0.01 and cancel it; it cannot fill. This gives the true
  accept-and-ack time.

## 5. Can we beat the incumbents?

**Not on wire speed alone; at best we tie their median with the fast link.** Run 1's first
in-direction reprice of the 5m book lands a median **201 ms** after the Binance onset trade
(p25 128, p10 70; n = 150 [M]). 78% are trades (median 218 ms), which under the 150 ms hold
means the first filled order **arrived** a median **~68 ms** after the trade: exactly a McKay/BSO-class reactive bot
(66 ms + co-location). A quarter arrived **before** the trade (anticipation). The incumbents
already sit at the physical edge of reaction or ahead of it.

Spot-onset trigger, 150 ms hold, 5m. Rows come from `data/out/infra/budget.csv`:
- **first:** share of 1 bp bursts with no in-direction reprice before our fill.
- **edge:** net c per $ at the 0% tier of the real taker fills within +-50 ms of our fill time.
- **shield:** share of takers' winning edge that fills after our cancel would land.

| build | arrival | fill after trade | first | edge | maker shield |
|---|---|---|---|---|---|
| A Tokyo single host | 123 ms | 273 ms | 29% | +2.2 c | 59% |
| **B Dublin (cheap)** | 113 ms | 263 ms | **31%** | **+2.6 c** | 59% |
| D London co-location | 108 ms | 258 ms | 33% | +2.5 c | 60% |
| F link + Dublin | 78 ms | 228 ms | 42% | +2.0 c | 62% |
| **G link + London co-location (fast)** | 69 ms | 219 ms | **43%** | **+4.9 c** | 63% |
| H fiber floor | 50 ms | 200 ms | 51% | +3.4 c | 65% |

What the table means for profit:
- **The hold sets the bar.** At 250 ms instead of 150, first drops to 21-24% and edge to
  +0.4-1.8 c for every build.
- **A perp trigger helps only when the perp truly leads.** At its median head start (1 ms)
  nothing changes. In the top quarter of bursts (lead >= 57 ms) the fast build fills at
  ~162 ms, first 61%; the cheap build at ~205 ms, first 49%.
- **Edge per $ is the same scale for both builds** (+2-5 c, noisy windows). The pooled speed
  buckets agree: +4.1 c at 150-200 ms and +2.3 c at 200-300 ms, against +12-20 c inside 150 ms.
  The link buys priority (first in 31% to 43% of bursts), not a different edge regime.
- **Market-wide pool in each build's window** (all takers, runs 1+2): ~$24/h (cheap window,
  $19k of fills at 2.6 c) and ~$21/h (fast window, $9k at 4.9 c). Over 21 quiet-to-normal
  hours this is shared by a median of 4 rival bots per burst.
- **Our $6 clips cap our share.** Upper bound if every burst filled one clip: $0.16 per fill x
  24-58 bursts/h = $4-9/h. The probability of filling at 263 ms is unmeasured; the paper bot must
  measure it before any money moves.
- **Makers:** cancels are not held, so even the cheap build pulls a stale quote before ~59% of
  the takers' winning edge can fill. The fast link adds only ~4 points. The remaining ~40% comes
  from anticipating takers that no infrastructure stops. This makes the maker variant
  (research focus 4) the cheapest route to the speed advantage the hold creates.
- **Decision rule for the link:** buy it only after the cheap build's live fills show (1) positive
  net edge and (2) a measurable loss to faster takers worth more than the quote. With $6 clips
  that is unlikely before the bankroll reaches the $2-5k depth limit.

**Implication for the research, not for infra:** the 10 ms speed buckets in
`reports/trade-anatomy.md` measure fill time, so the order behind a fill at +X ms arrived at
+X - 150 ms. The flat 12-20 c zone (fills within 150 ms of the onset) consists of orders sent
before the onset trade existed. That edge is won by an earlier trigger, not by a faster wire.

## Caveats

- **Hold value:** 150 ms comes from the latest dated changelog entry. The order-lifecycle page
  and the OpenAPI still say 250 ms, and only a real order can settle it.
- **Probe sample:** Globalping probes are single machines (1-2 per region), sampled once on
  2026-10-10 ~18:45 UTC. Cloudping p50 agrees within 1-2 ms.
- **One-way legs:** taken as half of a round trip. The Tokyo order leg includes Cloudflare's
  long-haul to the London origin, which is unknown in detail.
- **Run-1 sample:** first reprices come from 4 quiet hours (n = 150). Fill edges come from 21 h
  in ±50 ms windows of a few hundred trades; single windows swing by several cents.
- **Vendor figures:** McKay, BSO and Avelacom latencies are vendor claims (AWS's Avelacom test
  is the only third-party-hosted one), and no vendor publishes a price.

## Sources

- Polymarket taker delay, changelog (150 ms from 2026-09-04): https://docs.polymarket.com/changelog/predictions.md
- Polymarket order lifecycle (hold, `itode`, cancels): https://docs.polymarket.com/concepts/order-lifecycle.md
- Polymarket CLOB OpenAPI (`itode`, order `timestamp` "for uniqueness"): https://docs.polymarket.com/api-spec/clob-openapi.yaml
- Polymarket place orders (batch 1-15, statuses): https://docs.polymarket.com/trading/place-orders.md
- Polymarket geoblock, eu-west-2, co-location form: https://docs.polymarket.com/api-reference/geoblock.md
- Binance SBE market data: https://developers.binance.com/docs/binance-spot-api-docs/sbe-market-data-streams
- Binance FIX API: https://developers.binance.com/docs/binance-spot-api-docs/fix-api
- Binance USD-M routed websocket notice: https://developers.binance.com/docs/derivatives/usds-margined-futures/websocket-market-streams/Important-WebSocket-Change-Notice
- McKay Brothers crypto venues (Binance apne1-az1/az4; Polymarket eu-west-2 and eu-west-1): https://www.mckay-brothers.com/services/crypto
- McKay Tokyo-Europe < 132 ms RTT (2025-02): https://www.marketsmedia.com/mckay-brothers-launches-fastest-connectivity-between-tokyo-and-europe
- AWS + Avelacom Tokyo-London 139.6 vs 210.0 ms: https://aws.amazon.com/blogs/industries/ultra-low-latency-cross-region-crypto-trading-with-avelacom-and-aws/
- BSO + CryptoStruct microwave < 66 ms one way: https://www.thetradenews.com/thought-leadership/bso-and-cryptostruct-partner-on-ultra-low-latency-tokyo-to-london-microwave-route-for-crypto-data/
- Avelacom 2021 STAC deck (AWS London-Tokyo 216 vs 139 ms): https://stacresearch.com/system/files/resource/files/GSL-Spring2021-Avelacom.pdf
- AWS inter-region latency: https://www.cloudping.co/ ; Azure: https://learn.microsoft.com/azure/networking/azure-network-latency
- AWS Binance az4 outage (2025-04): https://www.datacenterdynamics.com/en/news/network-issue-at-aws-data-center-brings-down-crypto-exchanges
- AWS EC2 on-demand price maps (fetched 2026-10-10): https://b0.p.awsstatic.com/pricing/2.0/meteredUnitMaps/ec2/USD/current/ec2-ondemand-without-sec-sel/EU%20(Ireland)/Linux/index.json
- AWS Direct Connect pricing: https://aws.amazon.com/directconnect/pricing/ ; Free Tier credits: https://aws.amazon.com/free/
- Globalping probe API: https://api.globalping.io/v1/probes

## Paper bot (2026-10-12)

Code `btclat/paper/`, tests `tests/paper/`, logs `data/paper/<run>/` (gitignored). Read-only:
it logs every order it would send and measures a paper fill on the live venue book; it imports
no signing library or order client (`guard.py` blocks them, a test scans the source).

**How to run:**
- Live: `nice -n 10 python3 -m btclat.paper --hours 48 [--latency-ms 0] [--conns 4] [--ntp amazon]`.
- Replay of recorded hours (same engine): `python3 -m btclat.paper.replay.run --hours H0,H1` (H0 is warm-up).
- Feature parity: `python3 -m btclat.paper.replay.parity`; tests: `python3 -m pytest tests/paper`.
- Report: `python3 -m btclat.paper.report --run <run> [--raw]` (per arm summary, paired gain vs
  micf, and the replay simulator on the same markets; `--raw` converts the run's own recording
  first, for a Dublin run).
- Dublin kit: `bash btclat/paper/deploy/package.sh` builds `dist/btclat-paper.tgz` and prints
  the launch commands (profile `btclat-login`, eu-west-1, AZ id euw1-az1); `setup.sh` on the
  box installs chrony on 169.254.169.123, a pinned venv, and a systemd unit (MemoryMax 1G).
  Cost: t4g.small + IPv4 + 30 GB gp3 ~$20/month, ~$1.30 per 48 h run.

**What runs:** the two pre-registered arms (`vt_v1_m0.03_any`, `vt_v1_m0.02_trigger`) and the
micf / theirs_micro baselines, taken from the research arm modules and evaluated with the
research rule functions on one row (60 sh, limit seen ask + 2 c, 0.2 s refractory). Frozen
`v1_L0` model, sha256 checked against `prereg2.json` at start (refuses on mismatch), scored by
the C trees. Binance spot and perp on 4 connections each, first arrival per update id wins;
one CLOB connection per 5m market; SNTP-corrected clock.

**What it logs per would-be order:** decision time on the receipt and venue clocks, trigger
source, arm, side, token, seen ask and its depth, model values, fair value, limit; the venue
book (levels up to the limit, rebuilt from venue stamps on the simulator's 5 ms grid) at
decision + L + 150 ms with the 10 ms race window; the paper fill from the research taker
simulator (walk to the limit, fee 0.07 p (1 - p), own takes remembered 3 s); 3 s and 10 s
venue-mid markouts; a gap flag (CLOB socket errors, as the simulator); settlement from Gamma.
The raw messages are recorded in the recorder's format so the simulator can replay the same hours.

**Parity (hour 2026-10-11 09:00 UTC, 12 markets, 59,650 decision rows):**
- Binance book features: equal to float32 noise (max 0.06 sd).
- Value-model port (vectorizer + C trees vs the research sklearn path): exact (0.0 c).
- Settlement-scale features (sigma, zs, fair_dz, gap) differ on 0.6% of rows by up to 1 sd: the
  offline arrays read trades stamped before q but received after it (in flight ~100 ms).
- Model score live vs offline: identical at p99, > 0.1 c on 0.2% of rows, max 1.4 c.
- **Offline quirk found:** on 7.5% of rows (decisions triggered by a Polymarket top change) the
  research tables read the book one 5 ms step before the change that triggered the row:
  `floor((q - t0) / 0.005 + 1e-9)` falls one step short when float error at epoch scale
  (~2e-7 s) beats the 1e-9 guard. Live reads the change; scores differ there by p99 4 c.
- Value-arm orders reproduced: veto 50 of 50, taker 60 of 64.

**Replay paper run vs simulator (2026-10-11 08:00-10:00 UTC, 22 markets, L = 0):** fills
paper / sim micf 27 / 20, theirs_micro 107 / 99, veto 23 / 20, taker 42 / 37; mean fill price
within 3% for every arm; 168 of 176 simulator fills reproduced one to one, matched prices equal
(mean |diff| <= 0.24 c). Three arms are within 25%; micf is 35% over. The extra paper fills come
from evaluating at the event itself where the simulator's micro tables evaluate at ms-rounded
times (sub-ms microprice states are skipped there) and from the grid quirk above. The raw
pipeline (`report --raw`) rebuilt the simulator's fills exactly on a copied recording.

**Latency:** value decision (features, two tree scores, rules) p50 0.32 ms, p99 0.86 ms in
replay; receipt to logged order p50 1.1 ms. Tree compile at start ~1 s.

**Smoke test (live, 2026-10-11 23:12-23:45 UTC, this host, 4 + 4 Binance connections):**
- Memory: RSS 186-244 MB; CPU 26% of one core (shared host, nice 10).
- Decisions: value decision p50 0.95 ms (before the vectorizer speed-up), receipt to order
  p50 1.5 ms, p99 2-7 ms. Host clock was 16.2 s off; SNTP corrected it.
- First arrival: best perp connection won 58% of updates, best spot connection 36%.
- Fills per hour (4 settled markets, a busy hour: theirs_micro 450/h): micf 27, theirs_micro
  450, veto 39, taker 24. Simulator per-hour fills: quiet test hours median 15 / 86 / 10 / 14,
  busy extension hours median 34 / 571 / 36 / 27 (max 55 / 1,280 / 120 / 74). As a share of
  theirs_micro: micf 0.060 (sim busy 0.060), veto 0.087 (0.063), taker 0.053 (0.047).
  Markouts not read: these hours are in the pre-registered test segment.
- One CLOB disconnect ("slow consumer", code 1013) on a loaded shared host: 29 orders flagged
  as gap. The bot now logs event-loop lag and CPU time per minute to watch this in Dublin.

**Dublin 48 h paper run `dublin-20261012` (2026-10-12 00:04 - 10-14 00:04 UTC, t4g.small eu-west-1,
575 markets, 114,917 would-be orders, 6,279 gap-skipped, 0 unresolved):**

| arm | fills/h | 10 s mk c/$ | mk $/day | gain vs micf $/day [95% CI] | paper / sim fills | px ratio |
|---|---|---|---|---|---|---|
| micf | 41 | +12.3 | +3,486 | | 1.76 | 0.994 |
| theirs_micro | 1,263 | -1.1 | -9,348 | -12,834 [-14,974, -10,635] | 1.10 | 0.998 |
| vt_v1_m0.02_trigger (veto) | 120 | +9.6 | +5,006 | +1,520 [+927, +2,161] | 1.35 | 1.028 |
| vt_v1_m0.03_any (taker) | 66 | +14.9 | +4,175 | +689 [+72, +1,318] | 1.53 | 1.012 |

- **Signal confirmed on 48 new hours:** both pre-registered arms beat micf with the CI above 0, as in prereg2.
- **Simulator fit:** fill prices within 3% and 94-98% of the simulator's fills matched one to one, but only
  theirs_micro is within the 25% count target; the paper bot fills 35-76% more on the value arms and micf
  (the event-time vs ms-rounded evaluation and grid quirk noted above, now at scale).
- **Not a live forecast:** paper and simulator share the 150 ms hold and no maker reaction to our own
  order. Live on the same arm (2026-10-13, 36 fills) filled 14% vs 61% paper and marked out -4.1 c/$
  vs +11.6 (`reports/live-hold.md`): makers pull 94% of the targeted depth inside the ~250 ms hold.
- Cost: the instance was shut down from inside at 00:28 UTC (AWS session expired); terminate it and
  delete <AWS_SG> after the next `aws login`.

## Live test kit (2026-10-12, built, not run)

Code `btclat/trade/`, tests `tests/trade/`, deploy note `btclat/trade/deploy/DEPLOY.md`, logs
`data/trade/<run>/` (gitignored). Sends real orders, so it starts only with `--i-approve`, the
credentials file `~/.config/btclat/polymarket.env` (mode 600, owner-only directory), an unlocked
UTC day and `GET polymarket.com/api/geoblock` saying `blocked: false` (this research host: FR,
blocked). Reuses btclat.paper's feeds, engine, frozen model and arms by import; the paper
package and its guard are unchanged and never import it.

**Two stages:**
- **probe** (zero fill risk): post-only GTC BUY 5 sh at 0.01, at least 5 ticks under the best
  bid (checked, then asserted before the send), cancelled at once, every 30 s (floor 5 s, cap
  120/h); alternating warm (1 GET /time per s) and idle cycles. Logs sign time, POST ack and
  cancel round trips (ns), HTTP code, error kind, POP, rate-limit headers, connection idle time.
  Any fill, unconfirmed cancel or region / auth rejection stops it.
- **micro**: real FAK taker orders of exactly 5 shares on `vt_v1_m0.03_any` (`--veto` adds
  `vt_v1_m0.02_trigger`), limit = seen ask + 2 c, one side per signal. The paper executor runs
  in shadow on the same 5-share order, and each signal's line joins the live result (decision,
  sign, send, ack times, status, fill, fee, our book 10 s after the ack) with the paper fill
  and its predicted 10 s markout.

**Hard caps in code** (risk/limits.py; the CLI can only lower them): 5 sh and $3 per order, $15
open (unresolved cost + fee + orders in flight), -$10 per UTC day realised + marked (then a
`lock-<day>` file; that day cannot restart), 40 orders per rolling hour, wallet balance, kill
file `~/.config/btclat/KILL` checked every 50 ms, cancel-all on every exit path (SIGTERM
included). The ledger of sends, fills and resolutions is replayed on restart. Venue skip rules:
5-share minimum, and a $1 minimum for marketable BUYs (third-party figure), so micro trades
prices 0.20-0.60 (about half of the arm's research fills).

**Signing:** the official `py-clob-client-v2==1.2.0` (pinned in `btclat/trade/deploy/
requirements.txt`, with `coincurve`) builds and signs; our own HTTP/2 session posts it (the
library's `post_order` blocks polling trade hashes after a match). Measured here 11.9 ms per
order on the pure-Python backend; coincurve 1.4 ms; a hand-rolled signer 0.27 ms would save
~1 ms over coincurve, noise next to ~113 ms arrival plus the 150 ms hold. Not built.

**Report:** `python3 -m btclat.trade.report --run <run>`: fill rate live vs paper on the same
signals, slippage vs paper / seen / limit, latency (decision to send, sign, send to ack, Binance
event to ack), realised 10 s markout c/$ with a market-bootstrap CI, paper's predicted c/$ on the
same signals, the paired difference, and the fills needed for the CI to exclude 0. From the
research fills in the 0.20-0.60 band (per-fill sd 35-69 c/$, mean +11 to +40 c/$), that is
~12-40 fills if the research edge holds and ~9x more if the live edge is a third of it.
