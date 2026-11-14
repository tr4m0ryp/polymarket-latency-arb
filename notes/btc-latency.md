# BTC latency strategy: goal and state

## Goal
Run the BTC up/down latency strategy ourselves and make it pay after fees at our own fee tier.

## The two wallets
| wallet | market | net / day | gross / $ | net / $ | speed rank | note |
|---|---|---|---|---|---|---|
| 0xc53375ff94e96100f2b30a4b5775db35218d69a9 | BTC 5m | +$7,588 | 4.54% | 3.30% | 4 of 267 | best taker bot; wins on post-2 s hold PnL and low solo fee drag |
| 0x3048d65321be3497164cdfc2996f94f98a2e7537 | BTC 5m | +$6,037 | 2.80% | 1.63% | 2 of 267 | faster, larger 2 s markout; earns ~45% of gross from Up+Down pairs bought below $1 |
Both: 571 of 575 5-minute markets in 2 days, about 85% taker, 50% taker-rebate tier. Before the study
window: 1.48% vs 0.37% gross ROI over about 2,200 markets each (corrected pull; the older
closed-positions pull, which omits unredeemed losers, showed +$62k / +$54k and overstates).

## What the bot does (reconstructed from fills; reports/latency-bot.md section 2)
1. Watches Binance BTCUSDT every second.
2. Buys the side of the latest 1-3 s Binance move with a fixed clip (60 shares, median fill ~$12),
   one fill per transaction, mostly at prices 0.30-0.70.
3. Fills land 2-3 s after the move (block time), about 1 s before the Polymarket book catches up.
4. Never sells; flips side on reversals (5-27 times per 5m market); holds both sides to resolution.
5. Edge: 2.44 c per $ gross in 5m (10.7 c per $ right after an aligned >1 bp move).

## Why it is hard (difficulty 7/10)
- Fee: ~3% of notional at p = 0.57; incumbents get 50% back. At a 0% tier the best bot's
  2-day net falls from $15.2k to $9.2k and the runner-up's from $12.1k to $2.7k.
- Crowding: a median of 4 rival bots per Binance burst; only 35-65% first-block share for the leaders.
- Capacity per block inferred at tens of dollars (not measured; no historical books).
- Latency budget: Binance tick to signed CLOB order accepted in under ~1 s.

## Open questions (reports/latency-bot.md section 6)
1. Does Binance lead the Chainlink TWAP that settles 5m/15m, and by how much?
2. True reaction time: off-chain match time instead of block time.
3. Model-edge disagreement between the trigger and profit studies.
4. Is the 15m trio's maker quoting (+$12.8k/day, mostly maker) spot-aware or adversely selected?
5. Same-owner checks (funding traces) for the trio and pairs.
6. Short windows: 2 days of 5m data; why every big 5m bot earns more buying Up.
7. Fee assumption; 8. unreconciled lifetime numbers; 9. 0x06dc51826bc524d9a83770e7de9dd7e005b04524's wider operation.

## Next steps (proposed)
1. DONE (run 1, reports/live-lead-run1.md); run 2 (24 h, + perp feed) recording since 2026-10-09 22:03 UTC.
2. Paper bot with the decision rule above; measure would-be fills against the live book.
3. Fee-tier economics: model the path from 0% to the 50% rebate tier.
4. Maker variant: quote around spot-implied fair value instead of taking (no taker fee).

## Vision Updates
- 2026-10-09: project created from the copy-trade research's latency workflow.
- 2026-10-09 (orientation, new session): **Understanding.** The target is one mechanism: take the
  side of the latest 1-3 s Binance BTCUSDT move on the Polymarket 5m book before it reprices, in
  small fixed clips, hold to resolution. Only 5m is cleanly latency (markout $55.3k of $64.0k
  gross); 15m/4h/daily profit is mostly hold and is not the target. We must win at a 0% rebate
  tier, where the runner-up's 2-day net falls from $12.1k to $2.7k, so per-fill edge after the
  full taker fee (0.07 p(1-p), ~1.75 c/share at p = 0.5) is the number that decides everything.
- **Biggest risks, ranked.** (1) Fee at 0% tier: the 2.44 c/$ average gross barely clears a
  ~1.7 c/$ fee; only the aligned >1 bp bursts (10.7 c/$) clearly pay, so the bot must be
  selective, not continuous. (2) Speed vs 4 incumbents per burst: our host is Scaleway Paris,
  Binance ws RTT ~260 ms (Tokyo), so we may arrive after the stale depth is gone; colocation
  choice is a first-order design decision. (3) Stale depth per burst is unmeasured (inferred tens
  of $), so capacity may be too small to matter. (4) 2-day sample; edge may be regime-dependent.
  (5) Host clock was 8.3 s slow (chrony has no servers); every live timestamp is SNTP-corrected.
- **Live recorder built** (`python3 -m btclat.live`): Binance trade+bookTicker, Chainlink BTC/USD
  via Polymarket RTDS (answers open question 1), CLOB market feed per 5m/15m market from 90 s
  before open. First run: 4 h from 2026-10-09 17:37 UTC.
- 2026-10-09 (live run 1, `reports/live-lead-run1.md`): **the window is ~200 ms, not 1-2 s.** The
  5m book first reprices a median 0.20 s after the Binance trade (venue clocks), 92% caught up
  1 s after our receipt; in 64% of bursts it moves before our Paris spot tick arrives (Binance
  receipt lag 125 ms). Takers collect ~$445/h of 0%-tier edge after >= 1 bp bursts in 5m, but
  1-2 bp bursts are net negative: fire only on >= 2 bp. Chainlink lags Binance by ~1.5 s in
  actionable data (open question 1 closed). **Revised risk #2 is now #1: signal latency.**
  Next: run 2 (24 h, + Binance perp feed), then a replay paper bot on the recorded books with
  latency L in {25, 50, 100, 200} ms and a host comparison (Paris vs Tokyo vs London).
- 2026-10-09 (from the copy-trade session's live integration test,
  ~/projects/polymarket-copy-trade/reports/2026-10-09-live-integration.md): **order placement is
  region-blocked from this host** (POST /order -> 403 "Trading restricted in your region", FR /
  Scaleway Paris); feeds and books work. Where the user may trade is the user's decision: flagged,
  not designed around. Order path when allowed: py-clob-client-v2 1.2.0 (2026 contracts, server
  time); tick 0.01, min 5 shares/order; read the fee per market (BTC 5m/15m all show Gamma
  takerBaseFee 1000 and tick 0.01 in run 1, consistent with the 0.07 crypto schedule; other
  families differ, e.g. weather 0.05). Any real deployment needs a permitted jurisdiction AND a
  host near Binance / the CLOB, which the sub-second window makes binding.
- 2026-10-09 (routing, relayed from the user via the copy-trade session): keep the BTC latency
  work entirely in this project and session; report to the user directly (reports/ here), never
  through polymarket-copy-trade. Its integration facts above remain ours to use.
- 2026-10-09 (user redirect: "find the exact server and network path that minimizes latency";
  `reports/colocation.md`): Binance = AWS ap-northeast-1, Polymarket CLOB = AWS eu-west-2 behind
  Cloudflare (official docs). The total is signal leg + order leg, so a Tokyo host alone gains ~0;
  the lever is the Tokyo-London route (AWS ~215 ms RTT vs McKay Brothers <132 ms, ~40 ms one-way),
  then Cloudflare (~12 ms), then AZ (<1 ms). API allowed from JP/IE IPs per docs; jurisdiction is
  the user's decision. Next: EC2 probes in Tokyo and Dublin (needs AWS credentials).
- 2026-10-09 (user question: start capital for bets): capital cycles every 5 min. The two leaders
  spend a median $645 / $1,090 per 5m market (p99 $2.7k / $3.9k, max $3.4k / $4.6k), never sell,
  and redeem a median 66 s after close (p90 100 s, max ~3 min), so at most ~2 markets are locked at
  once. Working capital at their scale: ~$5-10k; for our >= 2 bp-only rule about $2-5k. More
  capital does not raise profit: the edge is depth- and speed-limited, turnover ~40x/day.
- 2026-10-09 (user: budget ~$200, grow by compounding): $200 supports half-Kelly bets of ~$6
  (3%), near the leaders' $12 clip. Growth depends entirely on our realized net edge per $:
  6% (average-taker speed) ~ x1.5/day at run-1 burst rates, 2% ~ x25 in ~2 months, 0% loses the
  fee (~$1.5/h at $84/h volume). The bankroll stops being the limit near $2-5k (depth-limited).
  Plan: replay paper bot measures our edge vs latency first; $50-200 live pilot only after
  explicit approval and a permitted jurisdiction.
- 2026-10-09 (jurisdiction, relayed from the user via the copy-trade session, not stated in this
  session): the user trades as a resident of a non-restricted country with full access to the international
  exchange; that country is not on Polymarket's restricted list (checked 2026-10-09). The bot must run from
  a permitted host region: not FR/DE/UK/US. Candidates: AWS Dublin (IE) or Tokyo (JP), both
  API-unrestricted; London only via Polymarket's co-location form. Do not stall planning on this.
- 2026-10-10 (run 2 lead-lag, `research/live/leadlag.py`, 3 h): **the 5m book follows the Binance
  USD-M perp ~3x more than spot** (joint standardized betas 12.3 vs 4.2, peak 100-300 ms after our
  perp receipt; perp leads spot by ~50-100 ms). The forensic "spot 1 s move" rule was a proxy;
  our trigger should be the perp. Run 2 got no futures trades (aggTrade sent nothing): only the
  perp book was recorded; fix the stream before run 3.
  **Research focus, ranked:** (1) replay paper bot on runs 1-2: edge vs reaction latency, perp vs
  spot trigger, threshold; (2) earliest predictive trigger (perp book imbalance / trade flow),
  since 9% of reprices beat any Tokyo-London route; (3) AWS probes Tokyo/Dublin; (4) maker variant
  that quotes off the perp and cancels faster than takers can hit (no taker fee); (5) why
  0xc53375 earns more hold PnL than 0x3048 (selection, not speed).
- 2026-10-10 (user asked: trades per market, size, win rate, why losers lose, fastest reprice,
  is faster better; `reports/trade-anatomy.md`): leaders do 49 / 92 buys per 5m market of 60
  shares (~$8-11); win 51-52% at settlement, 64% positive 2 s markout. Losers: no-move and
  against-move buys, 0.70-0.90 tokens, side flips, late fills. Live: taker fills within 150 ms
  of the move net ~11 c/$, after 500 ms ~0, after 1 s negative. Fastest reprices 4-16 ms after
  our onset trade, i.e. anticipation: the trigger must fire at the start of the move (perp).
- 2026-10-10 (user: why do A and B trade different counts if both trade every Binance update; how
  many updates does Binance send): Binance streams continuously (spot ~24 book msgs/s, perp ~85/s,
  best price changes ~0.2-0.4/s in quiet hours). A and B fire on their own triggers: 24 vs 39
  taker blocks per market, only 0.3 correlated with Binance >= 0.5 bp seconds, ~half on < 0.2 bp
  moves. B = looser trigger. Open: what triggers the no-move blocks (perp? stale-quote scan?).
  10 ms speed buckets (0-150 ms) running over runs 1+2 (`research/live/speed.py`).
- 2026-10-10 (user: reverse-engineer the triggers; explain the resting orders; what if we join):
  trigger read: fire in 1-4 s bursts while the market is undecided and > 30-60 s remain, more
  after bigger Binance moves, side = last ~3 s move (69% / 65%); the no-move half is unexplained
  by 1 s spot (perp?). A and B do not trade with each other (< 1%). Resting bids earn +2-3 c/$
  with no fee. 10 ms buckets: flat ~12-20 c/$ within 150 ms, cliff at 150-300 ms. Next: refit
  the trigger on live sub-second data with the perp once run 2 ends.
- 2026-10-10 (user: launch three background agents): (1) hidden half of the trigger: ms
  attribution of live fills to A/B via transaction_hash + Data API, test perp / stale-quote /
  other venues / copying / block-timing; fix perp aggTrade, start run 3 (48 h) after run 2
  -> reports/hidden-trigger.md. (2) beat their rule: replay paper simulator on runs 1-2, their
  rule as baseline arm, held-out hours, L = 25-200 ms -> reports/strategy-search.md. (3) reach
  50-100 ms: physical floor, transport, order path, cheap vs fast build, costs, no spending
  -> reports/infra-plan.md. User goal restated: be faster than the incumbents and take the
  stale orders they would take.
- 2026-10-10 (infra agent, verified): **crypto taker delay = 150 ms** (Polymarket changelog,
  2026-09-04; `itode: true` on live 5m markets); cancels are not delayed. Reactive taker fills
  cannot land before ~200 ms after a Binance trade (fiber floor ~50 ms + hold); cheap Dublin
  build fills ~263 ms (first in 31% of bursts, ~+2.6 c/$), fast link build ~219 ms (43%, ~+4.9
  c/$). The 12-20 c/$ fills were sent before the onset (anticipation). Makers can cancel in
  ~113 ms (cheap) before reactive takers match: the maker variant gets the structural edge.
  Free wins: 3-4 parallel Binance connections (1-4 of 5 run ~100 ms late), fast signing
  (0.27 ms vs 11.6 ms), keep the CLOB connection warm. Strategy and hidden-trigger agents told.
- 2026-10-10 (user: competitor timeframe, delay-reduction rumour, do they predict, faster build
  rumour): reactive wave of burst-side taker fills jumps at 250-300 ms and peaks at 300-350 ms after
  the Binance trade, i.e. competitor orders arrive ~100-200 ms after it (AWS-class); anticipation
  is a minority by count with the best edge. No documented delay bypass: makers and cancels skip
  it; the rumour likely refers to the Aug 17 cut to 50 ms (reverted to 150 ms on Sep 4). Faster
  than microwave: HF shortwave radio (Raft: Chicago-London < 25 ms; Asia links exist, no public
  Tokyo-London figure; air floor ~32 ms vs fiber ~47 ms one way).
- 2026-10-10 (user decision): build on **AWS's own network** first (cheap Dublin build). Link
  vendors (Raft HF, McKay, BSO/CryptoStruct) parked in `notes/link-vendors.md` with ready messages.
- 2026-10-10 (hidden-trigger agent, verified against data/out/hidden): the missing half is the
  **Binance top of book**, not its prices. A/B fire on sub-tick perp + spot microprice changes
  0.21-0.33 s before their CLOB print (= ~100-120 ms arrival + 150 ms hold) and buy the side the
  book leans. Held-out side AUC on no-move fills 0.930 / 0.914 (perp book alone) vs 0.556 / 0.542
  forensic; no-fit rule 84% / 81% at 82% coverage; timing AUC 0.94 / 0.92. Copying ruled out
  above 4% (proven by the hold), inventory 50%, Chainlink 0.50, stale-quote +0.02. Nobody in the
  top 25 takers peaks below 250 ms. Value at 0% tier, 2 s: book-agreeing fills +1.3 c/$, move
  fills against the book -4.1 / -5.0 c/$. 28% of no-move fills unexplained (perp/spot disagree or
  both opposite). Perp stream fixed (`/public/stream`, raw @trade); run 3 (48 h) live since
  22:03 UTC. Strategy agent given the rule as its baseline.
- 2026-10-10 (strategy agent, verified against reports/strategy-search.md tables): hold-aware
  replay simulator (150 ms taker hold, venue-stamp fills, survival-window competition). Winner
  **micf** = their perp microprice trigger gated by a settlement fair value (ask + fee >= 1 c
  below fair), 60 sh, limit ask + 2 c. Held out (11.9 quiet weekend hours, 143 markets), 10 s
  markout: micf +3.5 / +1.7 / +1.0 c/$ at L = 0 / 50 / 100 vs rebuilt rule -0.8 / -1.6 / -1.7;
  paired markout gain +$1.5-1.8k/day, CI > 0 at every L. Resolution $ (+11-13 c/$) is outcome
  tailwind, not edge. Per $ micf ~2x the real leaders (A/B +1.5/+1.6 c/$ markout); in markout $
  60 sh ~$0.8k/day < A ~$1.0k < B ~$2.2k. Rebuilt baseline is ~2.3 c/$ weaker than the real
  bots, so "beats their rule" is not yet "beats A/B". Makers pay only at L = -40 (private link).
  Lost held out: pure fair taker, depth sizing, perp imbalance model. Pre-registered test: micf
  on run 3 (fresh) must keep markout > 0 and paired gain CI > 0. Repo: 315 MB of simulator
  pickles stripped from the 221 unpushed commits (backup branch backup/pre-pkl-strip-2026-10-10).
- 2026-10-11 (user redirect): go beyond "side the book leans". Build an extremely fast order-book
  prediction model that forecasts the move far enough ahead (~150-250 ms) that a taker order,
  despite the 150 ms hold, matches before Polymarket makers cancel. Launched a background agent:
  literature + horizon decay curve on our data, invented signals (queue depletion, event
  intensity, multi-venue), inference latency in microseconds, predictive taker and maker arms in
  the hold-aware simulator vs micf / rebuilt leader rule / leader actuals; frozen model, final
  test on unused run 3 hours -> reports/predict.md. Clarified: the 2x-per-$ filter is ours
  (micf), not theirs; their rule has no value filter.
- 2026-10-11 (predict agent, `reports/predict.md`): **direction is solved, timing and the
  follower's residual are the frontier.** At a 1-tick spread the perp's next full tick is
  called with AUC 0.99 (imbalance alone 0.98) out to 1 s; timing decays 0.965 -> 0.852; the
  Polymarket move left after the 150 ms hold is AUC 0.71 / 0.69 / 0.66 at L = -40 / 0 / 50
  (leaders' rule 0.63 / 0.61 / 0.58). Perp imbalance lost because ~50% of its move lands
  inside the hold. Invention: predict the side's value after the match (side-oriented GBDT,
  3.6 us/decision in C). Frozen pre-registered primary (3 s target, 2 c margin) **failed**:
  +6.7 c/$ on test run 1 but CI over micf across 0, -1.6 c/$ in the busy 15-19 h extension.
  Survivor on all 251 unseen markets (21 h): 1 s target, 3 c margin, +15.9 c/$ markout, +$849
  /day over micf at L = 0 [-22, +1,926], +$1,360 [+391, +2,431] at L = -40; model as veto on
  their trigger +$875 [+426, +1,304] at L = -40. Perp trades and depth behind the touch
  (26 ms @depth@0ms side recording) add nothing. Next: pre-register the 1 s / 3 c taker and
  the trigger veto, paper-run >= 48 h from Dublin.
- 2026-10-11 (user: continue): remaining plan. (1) Pre-registered second test of the two
  surviving arms (predictive taker 1 s / 3 c, predictive veto) on run-3 markets from 18:55 UTC
  -> `data/out/predict/prereg2.json`, run after run 3 ends 2026-10-12 22:03 UTC. (2) Paper bot
  (read-only, logs would-be orders, C model, live feature state) built now; deploy to Dublin
  after the AWS probe. (3) AWS probe blocked on an IAM policy for user <IAM_USER> (profile
  btclat). (4) Tokyo-London link: user sends the vendor requests in notes/link-vendors.md; the
  only significant gain so far (L = -40) depends on it.
- 2026-10-11 (user: "start already with the tokyo london link ... asap", allowed to request
  anything): CryptoStruct (BSO microwave) request submitted via their form; Raft and McKay forms
  blocked by human captchas, BSO needs a phone number: user submits those. AWS probe blocked by an
  organization SCP (mgmt account <AWS_ACCOUNT>) denying EC2 in ap-northeast-1 / eu-west-1 /
  eu-west-2 on the fresh account <AWS_ACCOUNT>; user to open an AWS support case.
- 2026-10-11 (AWS probe done, account <AWS_ACCOUNT> via `aws login`, profile btclat-login):
  Dublin = Binance +101-104 ms, CLOB request 25.6 ms RTT, so ~114 ms event-to-CLOB (L = 0
  confirmed). Best Tokyo zone apne1-az4 (perp 1.9 ms). London CLOB 18.4 ms RTT. Geoblock flag
  true for JP/IE/GB; docs say JP/IE are website-only. `data/out/infra/aws/summary.md`.
- 2026-10-11 (fast-link search, `reports/fast-link.md`): nothing self-serve reaches ~70 ms one way;
  every self-serve NaaS/cloud is 203-228 ms RTT (Megaport 218/228 via the US). Only self-serve path
  that beats AWS: a $12/month Misaka KHV01 (Khabarovsk) relay, 25.6 + 149.1 ms RTT = ~87 ms one way
  to London, ~90 to Dublin [Globalping]; first leg varies 26-75 ms by AWS Tokyo host, so ping from
  apne1-az4 first, check sanctions, and race it beside the AWS path (first copy wins).
- 2026-10-11 (user: can our own Tokyo-London servers talk faster?): relay probe (Tokyo az4 ->
  Dublin/London UDP vs direct Binance stream): median identical (~100.5 / ~106.3 ms), relay
  only trims tails when combined (p99 309 -> 209 ms). No server-side setup beats the AWS fiber;
  below ~100 ms needs a third-party route. Fast-link research agent launched (self-serve
  options, Globalping measurements) -> reports/fast-link.md. Avelacom (sales@avelacom.com)
  added: Direct Connect Tokyo-London ~139 ms RTT, Stockholm PoP aimed at prediction markets.
- 2026-10-11 (fast-link agent + check): no self-serve route beats AWS. The only candidate
  (Misaka KHV01 relay, ~87 ms to London on Globalping) fails from our zone: apne1-az4 to KHV01
  is 150 ms RTT. Sub-100 ms needs a sales-led link (CryptoStruct sent; McKay, Raft, Avelacom
  pending the user).
- 2026-10-12 (paper bot, `btclat/paper/`, reports/infra-plan.md "Paper bot"): read-only bot
  runs both pre-registered arms + micf / theirs_micro live, logs would-be orders with paper fills
  on the venue book. Live features equal the offline tables (Binance exact, model p99 0.0 c on
  clean rows); found an offline quirk: 7.5% of rows (book-change triggers) read the book one 5 ms
  step early. Replay paper vs simulator: 3 of 4 arms within 25% on fills, prices within 3%; micf
  +35%. 33 min live smoke: 186-244 MB, value decision ~1 ms, fire rates in line with busy-hour
  simulator rates. Dublin kit ready (t4g.small, ~$20/month); not launched.
- 2026-10-12 00:04 UTC (user authorised "anything"): paper bot deployed to AWS Dublin euw1-az1
  (t4g.small <AWS_INSTANCE>, <HOST>, profile btclat-login, SSH key
  ~/.config/btclat/btclat-dublin.pem, SG <AWS_SG>). 48 h run `dublin-20261012`, arms
  vt_v1_m0.03_any, vt_v1_m0.02_trigger, micf, theirs_micro, L = 0, read-only (guard blocks any
  order client). Ends ~2026-10-14 00:04 UTC; then rsync, `python3 -m btclat.paper.report --run
  dublin-20261012 --raw`, terminate. Misaka key (user's account) stored in ~/.config/btclat;
  Misaka sites probed from AWS: NRT04 1.9 ms from az4, LON05/DUB02 1-3 ms from AWS London/Dublin,
  but AWS Tokyo to Misaka Europe 213-225 ms RTT (via US). Inside-Misaka route untested.

### 2026-10-12: Misaka inside route measured, closed
Rented Misaka NRT04 (Equinix TY8, S3P-1C1G Premium Plus, $11.30 to 2026-11-01, renewal disabled).
From it: LON05 205.7 ms RTT min, DUB02 214.2, AMS02 209.1, FRA13 215.6; mtr shows Misaka's own
backbone (206.148.x / 64.130.60.x) crossing the Pacific (+82 ms) and the US (+122, +138 ms)
before Europe (+204 ms). Same as AWS Tokyo-Dublin (198.5-203.6 ms). **Proven closed** for every
Misaka path under its current routing (premise: Misaka routes Tokyo-Europe via the US; reopen
if it adds a Eurasian route). Fastest route we hold stays AWS Tokyo -> Dublin direct (~101 ms one
way, ~114 ms event to CLOB). Sub-100 ms needs a private Eurasian link (McKay quoted GBP 20K/month).
Raw: data/out/infra/misaka/nrt04_route.txt.

### 2026-10-12 11:20 UTC: redirect, improve the model on its bad cases before going live
User: "is there a way to enhance our model at the bad cases?" Correction on record: the -1.6 c/$
busy-hour loss was the retired 3 s / 2 c primary; the deployed 1 s / 3 c arm made +7.7 c/$ in the
same hours. The deployed arms' real weak spots: L = 0 gain CI over micf touching 0, fat per-market
tails, veto weakening in busy hours, edge shrinking under competition during the 150 ms hold.
Improvement workflow launched: 4 diagnostic lenses + shared harness (two-fold window CV on seen
data), 5 invented candidates, adversarial verification, survivors frozen as prereg3.json before
21:45 UTC and judged on the still-sealed prereg2 segment (start >= 1791744900). Parallel track:
btclat/trade/ micro-live module (probe + 5-share micro mode, hard $10/day loss cap), not run.

### 2026-10-12: live test kit built, not run
`btclat/trade/` (probe + micro, hard caps in code, kill file, cancel-all on exit, day lock),
tests/trade 85 passing offline (tests/paper 7 still passing, guard intact), deploy note btclat/trade/deploy/DEPLOY.md. Nothing sent: the user
must create and fund the wallet ($40 pUSD), write the credentials file, and approve each stage.

### 2026-10-12 19:45 UTC: sealed-segment evaluation postponed
Usage limits stopped the candidate tests twice. Decision: the prereg2 segment (start >= 1791744900)
stays sealed until the improvement round commits prereg3.json (target 00:45 UTC 2026-10-13), so the
frozen arms and any improved arm are judged once, on the same unseen hours. Delaying the opening
changes nothing about prereg2's validity. Fallback evaluation cron: 2026-10-13 06:23 UTC.
Candidates under test: C1 conviction-keyed size, C2 settlement-delta margin + delta floor,
C3 two-side coherent firing score, C4 race-clock taker (predict the stale maker's cancel; the
inversion), C5 busy-inclusive regime-balanced retrain.

### 2026-10-12 21:40 UTC: improvement round closed, nothing survived
C1-C5 were scored on allowed data, and all five failed verification, so no prereg3.json was written.
The prereg2 segment is now opened with the frozen arms only, as registered.

C1 (conviction-keyed size) has a strong pooled result that is weak in fold A. It carries forward as the lead for
the next pre-registration, together with C2's veto delta floor. The next registration must be frozen
before the hours it is tested on are recorded or opened, with drop-top-5 and comp gates.

Summary: data/out/predict/improve/summary.md.

### 2026-10-12 22:45 UTC: prereg2 passes on the sealed segment
Both registered arms pass on 324 unseen markets (27 h): taker L=0 +5.7 c/$, gain vs micf +$848/day
[+281, +1,411]; veto L=-40 +$928 [+5, +1,806]. Resolution PnL not significant. Next: the $0 probe,
then 5-share micro trading (btclat/trade), alongside the Dublin paper run (results 2026-10-14).

### 2026-10-13 14:30 UTC: optimise Polymarket's order confirmation (user redirect)
Funded probe (90 orders): POST ack p50 56 ms, p90 118-294 ms; the network to Cloudflare is 1.3 ms and a
warm GET /time is 30 ms from Dublin, 37 ms from London (public LHR edge), so moving region without
private access gains nothing. Order work adds ~18 ms median over a GET; slow POSTs come with slow
cancels (corr 0.64): venue-side busy spells. Levers to test: co-location with direct (non-Cloudflare)
origin access, hedged identical-order sends on parallel connections, EOA vs POLY_1271 signature cost.

### 2026-10-13 14:34 UTC: first micro run stopped for analysis (user request)
30 min live (14:03-14:34), 40 FAK orders, 14 fills, balance $40.00 -> $72.60 (+$32.60, 4 markets,
3 resolved our way: luck-dominated, n far too small). 10 s markout -9.4 c/$ [-30, +15] vs paper -0.2
on the same signals; live fill rate 35% vs paper 62.5%. Key finding: every FAK ack takes ~270 ms p50
(matched 267, no-match 276) vs 56 ms for a resting GTC insert, so the venue holds taker orders ~210 ms
(the sim assumed 150 ms). The order-confirmation bottleneck is this taker hold, not the network.
Caps bound the run: 40 orders/h used in 30 min, 42 signals blocked by the $15 exposure cap.

### 2026-10-13 19:45 UTC: 4 h live run: the signal is right, the taker hold fills us only when wrong
dublin-micro-20261013b (15:39-19:39): 155 FAK orders, 22 fills (14% live vs 61% paper on the same
orders), ack p50 296 ms, p90 646 ms. Balance $72.60 -> $73.38; both runs together $40 -> $73.38, mostly
resolution luck. Live 10 s markout -4.1 c/$ [-13, +8]; paper on all sent +11.6 [+5.7, +16.9].
Adverse selection, both runs pooled: orders that missed live would have earned +16.8 c/$ (research
reference +15.9), orders that filled -5.2. The venue's ~250 ms taker hold lets makers pull the quotes
our correct signals target; we only fill when the move did not come. Taker route is closed while the
hold applies to it. Next: test whether a crossing GTC/GTD order is held too, and simulate a maker arm
with the measured hold (the hold protects makers: our cancel is ~45 ms, well inside it).

### 2026-10-13 21:00 UTC: co-location KYC form submitted (user)
Asked Polymarket whether co-located traders are exempt from the ~250 ms taker hold, whether the hold
covers marketable GTC/GTD orders, and whether co-location bypasses Cloudflare. Awaiting the answer.

### 2026-10-13 23:00 UTC: no limit width rescues the taker; only an earlier match does (reports/live-hold.md)
Tape replay of the 195 live orders: held orders match at send + 246 ms; makers pull 94% of the depth
at our limit first (ask +6 c median). Wider limits fill more at -2 to -7.5 c/$; matching 200-230 ms
earlier gives +8.6 to +10.2 c/$ (CI > 0), 30 ms earlier nothing. Leaders A/B today: 98% taker, 10 s
markout ~0 c/$ at our 0% tier (positive only via the 50% rebate). Next: unheld order path or maker.

### 2026-10-13 23:00 UTC: sim at the measured 270 ms hold (A1)
Primary taker L = 0: fill 34% -> 24%, +9.5 -> +6.6 c/$ [+2.3, +11.1]; live 14% at -4.1, so the replay
misses the live adverse selection. Value makers ignore the hold but need cancels <= ~50 ms: frozen
maker +5.1 c/$ [+0.5, +9.8] at L = 50, nothing significant at 150 ms. Next: live maker test.

### 2026-10-14 00:45 UTC: 48 h Dublin paper run done
575 markets: taker +14.9 c/$ 10 s markout, gain vs micf +$689/day [+72, +1,318]; veto +$1,520
[+927, +2,161]. The signal holds on 48 new hours, but paper fills 1.35-1.76x the simulator on the value
arms and shares its no-maker-reaction blind spot (live: 14% fills, -4.1 c/$). Next stays the maker route.

### 2026-10-14 07:50 UTC: live hold + duplicate-send tests (user: "do whatever you need")
Hold applies to FAK, FOK and marketable GTC alike (+165-176 ms vs resting 45 ms); GTD needs a
>= 180 s expiry. One signed order on 2-3 connections is deduped and cuts ack p90 334 -> 45 ms.
Taker route closed; maker route's cancel condition met with hedged cancels. Maker bot build started.

### 2026-10-14 UTC: fill-improvement synthesis (reports/fill-improve.md; user: "reason a potential improved approach of our order fillment")
At realistic latency the frozen maker is ~+1 to +2.8 c/$, not +5.1. Top levers, all $0 offline: inside
gate (quote only strictly inside the spread, pull -0.02: +7.5 c/$, in-sample, needs rival-improver
haircut), local-hash cancel+replace without ack-wait (+2.6 -> +5.1 c/$ in seqsim; mk engine disagrees,
reconcile first), insert hysteresis (flat $/day, test growth with L). Refuted: anticipatory taker
(low-price artifact), trigger standing, balance-starvation abort. Next: sealed-hours scoring.

### 2026-10-14 12:45 UTC: inside gate passes its sealed test; go for a live 1 h at 5 sh (reports/fill-improve.md)
User task: incidence, pre-register, score on sealed hours, wire `--rule inside` into the maker, dry caps
non-blocking. The 4 h dry run gave 5 fills only because the dry run applied the real loss cap (13,523
quotes skipped); dry now logs money caps as would-skip. Incidence on the dry run ~166 inside inserts/h
(sealed Dublin hours 80/h). Pre-registered (data/out/predict/inside-prereg.json, frozen before scoring),
scored on 360 sealed markets (Dublin after 2026-10-12 22:05 + the 4 dry hours) with probe latency and the
rival-improver haircut: inside +15.4 c/$ [+5.3, +23.8] vs frozen maker -8.1 [-17.0, +0.4] at L = 50;
paired +$747/day [+201, +1,386], drop-top-5 +$215; gain holds at L = 100 / 150. At 5 sh: +15.3 c/$,
+$34/day, ~4.7 fills/h. Hysteresis h = 0.005 ties h = 0 (lost a comparison). Next: live 1 h
`--rule inside` at 5 sh (approval needed), mechanics check; the edge needs ~20 live hours.
- 2026-10-14 14:45 UTC (live inside hour reconciled): the $1.65 balance drop is one real fill the bot
  missed (m34, BUY 5 Down @ 0.33, market resolved Up): a cancel race (the insert sat 325 ms in the
  venue's queue, the cancel had to wait for its ack) plus "not found" lookups read as 0 matched. Fixed:
  not found = unknown, "gone" cancels stay unsettled and count as exposure, fills settle from GET
  /data/trades + the user websocket + delayed lookups, and every live run ends with a reconcile line.
  The ~100 ms extra ack latency is the venue's write path (cancel answers come back at one-way speed
  on the same client; lookups 34 ms in the same moments; no load correlation); our client adds 3-5 ms.
  Built a sender process (`--sender proc|ab`) and `--far` (0.01 inserts) for a no-fill-risk A/B on
  the box. Biggest fill lever now: cancel before the ack via the locally computed order hash.


### 2026-10-14 15:30 UTC: focus redirect (user)
User: keep the focus on the **taker + model veto** arm (+$1,520/day in the 48 h paper run) and analyse
why it fails live, rather than designing new maker approaches. Note: the veto arm itself was never
run live; the live taker runs used `vt_v1_m0.03_any`. Next: replay the veto arm's own decisions
through the measured hold on the live tape, and test a hold-survival veto.

### 2026-10-14 15:45 UTC: one strategy, Rust bot (user)
Only taker + model veto (`vt_v1_m0.02_trigger`) is pursued; all other strategies are reference only
and are not run live. Rewrite the live bot in Rust with a full event logger. Analyse the limit offset
i (seen ask + i, i = 0..10 c, and buying at the predicted price): which i fills, at what markout, and
whether the needed i (slippage during the hold) can be predicted from data known at send.

### 2026-10-14 16:00 UTC: i = 0 rule, model for the real hold (user)
Live orders stay at i = 0 (seen ask); paying up voids the approach. Improvement goes into the model:
train the veto for the measured 250-300 ms hold (it was built for 150 ms) so it selects signals whose
ask survives the hold and still pays. Objective: maximise fills x value at i = 0.

### 2026-10-14 17:00 UTC: veto arm under the measured hold (reports/veto-hold.md; user focus + i = 0 rule + retrain)
Replayed the veto arm's own 9,890 paper orders (48 h Dublin) on the venue-clock book with each order's
hold drawn from the 195 live orders. Paper +$5,006/day -> same orders at 150 ms on the venue clock
+$1,208 (the paper bot filled on its lagging feed) -> measured hold at +2 c +$81 [-299, +463]; at i = 0
+$467 [+205, +716], +4.6 c/$, 27 fills/h. Every i > 0 is worse. Makers pull 91% of the targeted depth;
fills earn +3.1 vs +16.4 c/$ for misses; the veto picks the pulled signals (survival 20% -> 8% as v1's
value rises) and i* grows 1.9 c per c of edge, so a predicted-i* limit loses (-$683 [-1,113, -307]).
Family fixes (survival veto, EV, fresh feed, sizing) tie or lose. Retrained veto for the i = 0 hold label:
v1 + hold-aware gate `v1h_G_h250x_L0` wins on test hours, +$864 [+505, +1,272] vs v1 +$628, paired
+$236 [+84, +393]; exported (trees.json) but needs v1_value + 7 book features in the Rust bot.
Next: implement the 7 x_* features + gate in the bot, confirm the gain on new paper hours at i = 0.

### 2026-10-14 17:00 UTC: no caps, run as designed (user)
Caps (40 orders/h, 5 sh, $1-3 notional, $15 exposure, $10 loss) hid the real pipeline: the Rust dry
run wanted 112 orders in 29 min and the caps blocked 72. Removed; 60 sh as in the simulator. Live
Rust run dublin-bot-20261014b started 16:59 UTC with v1 at i = 0; the held-out winner v1h_G_h250x_L0
(+$864/day vs v1 +$628 at i = 0, paired +$236 [+84, +393]) follows once its 7 book features are in Rust.

### 2026-10-14 17:40 UTC: v1h_G_h250x_L0 runs in the Rust bot
The 7 book extras (state/hist.rs: research's 5 ms receipt-clock grid book read at t, t - 0.25, t - 1,
column touch times, last-50-row feed lag cumsum; features/extras.rs with numpy's float32 pairwise sum)
and the gate (engine/gate.rs: float32 inputs, tau from the model JSON, before the refractory) are in.
Parity on hours 497750-497753 against research's own `extras()` + sklearn: 974 / 974 orders, 7,106 /
7,106 gated rows with all 7 extras and the gate prediction bit-identical. Flag: `--model v1h_G_h250x_L0
--model-sha256 6761315ea71372322df0eb3e798612baa0d31151478a8cd8cfd0469d94b9c16e`; v1_L0 still loads.

### 2026-10-14 17:45 UTC: wallet funded, $100 bankroll with a reserve (user)
Wallet balance $143.04. The bot may use $100; the remaining $43.04 is an untouchable reserve
(bot bankroll = venue balance - 43.04, compounding on its own results). Live trading resumes only
once the $100 cap backtest (reports/bankroll-caps.md) lands and its caps are in the Rust bot.

### 2026-10-14 18:30 UTC: REDIRECT, pair profit is the goal (user)
User: "optimise for both-side buying and profit from a combined cost lower than $1; that is our
profit." Directional markout / win-loss returns were not requested and are not the objective. Re-do the
methodology: veto model, offset i and other approaches are re-judged by pair cost < $1 after fees.
Must work with a $100 bankroll even in peak markets, like A and B. Directional cap search stopped.

### 2026-10-14 18:15 UTC: bankroll caps search stopped at the pair-strategy redirect (reports/bankroll-caps.md)
User: find caps for a $100 bankroll (later: $143.04 wallet, $43.04 untouchable reserve), compounding
sizing, fractional caps, peak drawdown stop; then redirected the project to the pair strategy, so the
search stopped unfinished. Kept: the taker hold is unchanged (the 48 ms first ack is the duplicate copies'
pre-engine rejects; engine answer p50 294 ms, decision to match p50 280 ms), the bankroll simulator, and
the Rust `--reserve` (RESERVE=43.04) with balance-scaled sizing and fractional caps (provisional defaults,
selection hours only). The bot still needs auto-redeem before anything can compound.


### 2026-10-14 19:00 UTC: how A and B build pairs (reports/pairs-leaders.md; user task: forensic pair breakdown)
They run no pair rule: their latency taker trigger on both sides, inventory blind (P(buy short side) ~0.5 at any
imbalance), 17-22 side runs per market, no sells, no MERGE/SPLIT, all held to resolution (redeem +66 s). Pair cost
0.9886 / 0.9814 is timing (-3.4 c: switch legs buy a side right after it was sold down, at the turn) minus execution
(+1.4 to +2.4 c). Locked +1.1 / +1.9 c/pair pre-fee, -1.45 / -0.63 at our 0% tier; residual is 71% / 42% of their
pre-fee PnL. Mirrored book: ask_up + ask_dn = 1.01, < 1 for 0.03 s in 48 h. Pair rules on uninformed legs complete
78-86% but lose -4.3 to -6.9 c per leg-1 share (hold leg 1: -1.8). $100 = 5 sh clips + merge + residual cap 10 sh:
their own fills replayed fit (max $75-84 in play), locked - fee +$68 / +$225/day only with their maker legs and their
timing; taker-only -$71 / +$14. Next: put the residual cap + merge into the pair engine and judge our own triggers
(v1h veto) as both-side leg sources on held-out hours.

### 2026-10-14 19:45 UTC: pair strategies backtested (reports/pairs-strategy.md; user pair redirect + coordinator asks)
Best pair strategy on held-out (339 markets, 28 h): v1 >= 3 c taker leg 1 at i = 0, taker leg 2 when
the opposite ask + both fees <= 1 - avg - 2 c, residual cap 20 sh, clip 10, merge every pair, residual
held: +$91/day [+40, +143], locked 8.9 c/pair net, ~8 pairs/h, completion 85%, peak max $38. The
selection day gave only +$6, so all 52 h pooled: $100 +$54/day [+20, +89], $300 +$131/day, ruin 0%.
Pairs on a mirrored book are round trips: completion keeps the legs that won, the residual loses
(-$87/day); the hold hurts leg 1 but helps a taker leg 2 (maker leg 2 -$63). Lost: retrained pair
model (-$50), anticipatory resting leg (fills 3-4 c adverse at any shade; -$23 as leg 2), leaders-style
both-sides rule without completion (14-28% paired). Without auto merge/redeem the $100 stalls (~$2.5/day).
Next: merge + redeem + the pair engine in the Rust bot, then a live test of leg-2 FAK fills.

### 2026-10-14 19:50 UTC: live plan approved (user)
After the Rust pair bot passes its dry run: run it live for 2-3 days on the $100 bankroll ($43.04
reserve untouched), with a progress update to the user every 5 hours (pairs, pair cost, net c per pair,
unpaired residual, $/day, bankroll). Stop early only on a technical fault (fills/merges not reconciling
with the venue, merge or redeem failing, bot crash loop) or if the bankroll falls below $50.

### 2026-10-14 19:55 UTC: Up/Down inventory rules for the pair bot (user, via coordinator)
Inventory from venue-confirmed fills only (POST answer, lookup, trade poll, user ws; dedup by trade id);
leg 2 sized to the actual imbalance; heavy-side leg 1 refused past the 20 sh cap; merge only
min(Up, Down) re-read from the venue; reconcile against the venue every 30 s and at each market end
(> 1 sh mismatch stops leg 1 there, logged); residual logged per market. Built into `--strategy pairs`.

- 2026-10-14 22:30 UTC: pairs dry run (dublin-pairsdry-20261014b, 2 h) passed: 40 pairs, 8.1 c net/pair,
  completion 0.88, residual -$16.11, net +$12.99, peak capital $27.10. Live 72 h run started as
  dublin-pairs-20261014live ($100 bankroll, $43.04 reserve, relayer merge/redeem). The first real relayer
  tx (startup sweep) redeemed 14 old leftover positions in one mined tx (all losers, $0). Updates every 5 h.
- 2026-10-15 02:00 UTC, live 3.5 h: balance 143.04 -> 139.80 (-$3.24; book agrees to the cent); 14 pairs
  locked +$10.28, 6 residual markets -$13.51. Live hold is longer than modelled: matched FAK ack p50
  323 ms, p90 ~1.0 s (backtest sensitivity: 250 ms +$34/day, 400 ms -$22/day). Leg-1 FAK fills 20 of 479
  (4%, killed = price moved during the hold); leg 2 13 of 18. Residual study (reports/pairs-residual.md):
  no fix; the late scratch (relax_n 120, relax_pc 1.00) is +9.8 [+0, +25] held-out but -8 on the dry set,
  not deployed. False recon mismatch after resolution (venue auto-pays winners) fixed in code, deploy at
  next restart.
- 2026-10-15 03:37 UTC, live 5 h update: balance 121.72 (-$21.32); 35 pairs locked +$17.61 (median cost 0.957),
  14 residual markets -$38.94, 0 of 14 won (0 of 30 incl. dry; backtest 15%), completion 0.69 vs 0.85.
  31 relayer merges/redeems mined, no technical fault. Stop rules not met; run continues. Replay of the live
  hours (sim fill model vs live) started -> reports/pairs-live-gap.md.
- 2026-10-15 05:00 UTC, live gap (reports/pairs-live-gap.md): **model error, not variance.** On the 654 live
  leg-1 FAKs the backtest's independent hold draw fills 33% vs 7.3% live; each order's own measured hold
  reproduces 643/654 (0 false fills): the hold outlasts the ask exactly when the move is real. Live fills
  +0.2 c mid 5 s later vs kills +6.1 c (sim fills +5.4 c). Corrected fill model (`corr`: live holds + leg-1
  survival 0.54/0.19/0.08 by 5 s mid move) matches live fill rate, markout and completion; current rule
  held out **-$9.0/day [-39, +19]** (was +$91). Live hours were also a bad regime (old model -$19.6 on the
  same 46 markets). Best under `corr` (52 arms, picked on selection): v1 >= 5 c, leg-1 limit + 3 c, leg-1
  stop 120 s: held +7.4 [-7, +22], 7.8 paired sh/h: near flat, not an edge. Lever that reopens it: an
  earlier match (fills not conditioned on failed moves).
- 2026-10-15 04:35 UTC: live pairs bot PAUSED by me at a market boundary (no open positions) after
  reports/pairs-live-gap.md: model error, not variance. Live leg-1 FAK fills only when the move failed
  (adverse selection under the hold); corrected fill model puts the current rule at -$9/day [-39, +19]
  held-out, best variant (v1 >= 5 c, leg-1 limit seen + 3 c, no leg 1 in last 120 s) +$7.4 [-7, +22]:
  no edge. Reopens only with ~200 ms faster matching.
- 2026-10-15 04:39 UTC: Polymarket approved co-location (certs@polymarket.com): our wallets are whitelisted
  for the primary servers; host in AWS eu-west-2 (London), AZs a/b/c (2a=euw2-az2, 2b=euw2-az3,
  2c=euw2-az1); Cloudflare cannot be bypassed. Next: measure the taker hold from Dublin and from London.
- 2026-10-15 07:00 UTC, beat the hold (reports/beat-the-hold.md; coordinator task + co-location fact 04:39: wallets
  whitelisted for eu-west-2, Cloudflare stays). Hold = documented 150 ms crypto taker delay (changelog 09-04) on every
  FAK/FOK/marketable GTC (even ones not crossing on arrival), not on cancels (33-88 ms) or post-only (crossing reject 50 ms);
  the rest is queueing that ends after the ask leaves (endogenous at every lead). Leaders are matched ~250-270 ms after the
  Binance step at the pre-move ask, ~110-170 ms before us: the gap is their shorter hold, not their signal. Lead models
  (4 variants) lose to v1 under every fill model: predictable moves survive the hold 1% of the time. Chainlink push gives
  no lead. Best route: 0.5 s post-only bid one tick inside on v1 >= 3 c signals with a 0.1 bp Binance cancel guard, taker
  leg 2: held +29.5 [+10, +54] $/day, paired +38.5 [+8, +71] vs current; needs L <= 150 ms and a live maker-fill check.
  Hold what-if: at 150 ms decision-to-match the current rule is -3.9 (corr) to +95.9 (bn) $/day.

- **2026-10-15 07:50 UTC (user):** build the co-location setup (Tokyo Binance relay -> London eu-west-2
  trader, all three AZs) and measure every ms of gain; test the resting leg-1 route. AWS account
  <AWS_ACCOUNT> refuses every RunInstances with "Blocked ... not recognized as a valid account"
  (all regions, Dublin too; London on-demand quota 0). The leaked key is another account
  (<AWS_ACCOUNT>), not the cause. Needs an AWS account-verification case by the user. Resting leg-1
  mode being built in the Rust bot meanwhile (no deploy, no orders).

- **2026-10-15 (user):** "every ms counts", beat leaders A/B on speed; try every open gap and server
  optimisation once AWS is unblocked (blocked for suspicious activity, approval pending). Full list in
  notes/colo-todo.md; a watcher probes London launches every 30 min.
- **2026-10-15 08:30 UTC, London on AWS account 2 (<AWS_ACCOUNT>):** c7g.large btclat-lon-trade in
  eu-west-2c (euw2-az1, <HOST>), kit + keys cloned from Dublin, nothing enabled; Tokyo
  c7g.large relay <HOST> (apne1-az2). Kept-alive GET /time p50: London 2c 14.7 ms, 2a 15.4,
  2b 18.2, Dublin 26.4 (~12 ms saved). Tokyo -> Binance TCP ~2.1 ms; Tokyo <-> London RTT 209.7 ms.
  **Orders from London are refused:** a zero-fill post-only probe got HTTP 403 "Trading restricted
  in your region" (GB close-only) despite the whitelist email. Needs Polymarket to confirm which
  wallet/IP is whitelisted. Preflight now allows GB only with BTCLAT_COLO=1.
- **2026-10-15 09:00 UTC, Tokyo relay:** lost a comparison. Binance trades reach London directly
  ~106 ms after trade time; the Tokyo relay over AWS adds +3.8 ms (UDP) and worse on TCP
  (retransmit tail ~200 ms). Direct is already at the AWS floor (Tokyo-London RTT 209.7 / 2).
  Reopens only on a faster non-AWS line. Therefore the leaders' 60-80 ms signal lead is not
  transport: test venues near London/US (Deribit LD4, Bitstamp, Kraken, Coinbase, CME) as the
  earlier source (user question 09:00).
