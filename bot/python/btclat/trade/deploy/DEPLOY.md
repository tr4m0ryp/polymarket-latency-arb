# Live test on the Dublin host (not run; needs the user's approval and keys)

Real orders. Nothing here runs by itself: `setup-trade.sh` installs and starts nothing, and
`python3 -m btclat.trade` refuses to start without `--i-approve`, the credentials file
(mode 600), an unlocked UTC day and a non-geoblocked IP.

## Venue facts (verified 2026-10-12)

- **Region:** IE and JP are close-only on the website only, the API is not restricted; GB, US,
  FR, DE and others are close-only on the API too (docs `api-reference/geoblock`). Check
  `curl https://polymarket.com/api/geoblock` on the box: it must say `"blocked":false`. The
  research host here says `{"blocked":true,"country":"FR"}`, so the bot refuses to start here.
- **Market (GET /clob-markets, btc-updown-5m):** min size 5 shares, tick 0.01, `itode: true`
  (taker hold), fee r 0.07 exponent 1 taker-only (= 0.07 p (1 - p) per share), neg-risk false.
- **CLOB:** `GET /version` = 2 (CTF Exchange V2), collateral pUSD
  (0xC011a7E12a19f7B1f670d46F03B03f3342E82DFB, 1:1 USDC.e wrap).
- **Taker order types:** FAK (fill what is there, kill the rest) and FOK (all or nothing);
  post-only only for GTC/GTD. FAK with no match is a 400 "no orders found to match with FAK".
- **$1 minimum for a marketable BUY:** third-party report only, not in Polymarket's docs; the
  bot skips such orders (`skip:below_venue_min_notional`), so micro trades prices 0.20-0.60.

## Wallet, funding, credentials (user)

1. Create a Polymarket account on polymarket.com (Deposit Wallet, the default since
   2026-05-04). Note the wallet address from the profile menu (`POLY_FUNDER`) and export
   the signer's private key (`POLY_PRIVATE_KEY`). Use a fresh account that holds only the
   test money.
2. Deposit **$40** (bridge deposits arrive as pUSD): $15 max exposure + $10 day loss cap +
   $15 for winnings not yet redeemed. Approvals for a Deposit Wallet are gasless.
3. On the box: `sudo -u btclat install -m 600 /dev/stdin /opt/btclat/.config/btclat/polymarket.env`

   ```
   POLY_PRIVATE_KEY=0x<64 hex>
   POLY_FUNDER=0x<deposit wallet address>
   POLY_SIGNATURE_TYPE=3
   # optional; derived from the key at start when absent (all three or none)
   POLY_API_KEY=
   POLY_API_SECRET=
   POLY_API_PASSPHRASE=
   ```
   Type 3 = POLY_1271 (Deposit Wallet). A legacy Magic/email proxy wallet is 1, a legacy
   Safe is 2, an allowlisted EOA is 0 (then POLY_FUNDER = the EOA address and it needs POL).

## Install and run

```
bash btclat/paper/deploy/package.sh                    # here: kit now includes btclat/trade
scp dist/btclat-paper.tgz ubuntu@<ip>:~ && ssh ubuntu@<ip> \
  'rm -rf kit && mkdir kit && tar xzf btclat-paper.tgz -C kit && sudo bash kit/btclat/trade/deploy/setup-trade.sh'
# credentials file (above), then edit /opt/btclat/.config/btclat/run.env: HOURS=1 TAG=<yyyymmdd>
sudo systemctl start btclat-trade@probe                # stage 1, ~1 h, zero fill risk
python3 -m btclat.trade.report --run dublin-probe-<TAG>   # after rsync of data/trade/
sudo systemctl start btclat-trade@micro                # stage 2, after reading the probe report
```

Stop at once: `sudo -u btclat touch /opt/btclat/.config/btclat/KILL` (cancel-all, blocks
restarts until removed). The loss cap writes `state/lock-<day>`; that UTC day cannot restart.

## Cost

- **Probe:** $0 in trading (post-only BUY 5 @ 0.01, >= 5 ticks under the bid, cancelled at
  once; $0.05 reserved per order for ~50 ms). Needs >= $0.25 pUSD. 120 orders per hour.
- **Micro:** fee <= $0.0875 per order (5 sh at p = 0.5); notional $1-3 per order. Hard stop
  at -$10 realised + marked per UTC day; positions open at the trip can still lose up to
  their cost (<= $15), so the worst day is about -$25, a normal day a few dollars either way.
- **Host:** the Dublin t4g.small already running the paper bot (~$0.65/day); no extra.

## Hold test and duplicate send (manual, one-shot; not deployed)

Question: is the ~250 ms taker hold (FAK ack 270-296 ms p50 vs 56 ms for a resting insert)
applied to marketable GTC / GTD too, and does the venue dedupe one signed order sent on 2-3
connections? Never run next to `btclat-trade@micro`: either run's cancel-all on exit would
cancel the other's orders. Copy the code first (the box runs the kit in /opt/btclat):

```
rsync -a btclat/trade/ ubuntu@<ip>:/tmp/trade/ && ssh ubuntu@<ip> \
  'sudo rsync -a --chown=btclat:btclat /tmp/trade/ /opt/btclat/btclat/trade/'
# 1) duplicate send: unfillable post-only GTC BUY 5 @ 0.01, k = 1, 2, 3 copies x 5 reps (~2 min)
sudo -u btclat env BTCLAT_CONFIG=/opt/btclat/.config/btclat bash -c 'cd /opt/btclat && \
  .venv/bin/python -m btclat.trade holdtest --i-approve --dup --run dublin-dup-<TAG> --every 5'
# 2) hold test: 24 cycles, each 1 marketable BUY at the cheap side's ask (0.02-0.08), sized
#    max(5, ceil(1.05 / ask)) shares (just over the $1 marketable minimum), + 1 control
sudo -u btclat env BTCLAT_CONFIG=/opt/btclat/.config/btclat bash -c 'cd /opt/btclat && \
  .venv/bin/python -m btclat.trade holdtest --i-approve --run dublin-hold-<TAG> --n 24 --every 20'
```

Micro logged 87 signals under the $1 marketable minimum, so the hold test sizes each
marketable order to about $1.05-1.12 (0.05 -> 21 sh; cap $1.60 per order). Money at risk: the
hold test spends at most $5 (fills + fees, checked against the next order's worst case before
it is sent, so about 4 fills); the
duplicate test $0 (post-only far under the bid, cancelled at once; if copies were not deduped,
each extra order is cancelled and the run stops). Report: `python3 -m btclat.trade.report --run <run>`.

## Maker (value maker `vm_fair0.03_p-0.03`, post-only quotes)

Why: taker orders are held ~170-250 ms and adversely selected live; resting post-only quotes
ack in ~45 ms and are not held. The frozen maker sims at +5.1 c/$ [+0.5, +9.8] at L = 50 ms and a
0.27 s hold (reports/predict.md), but its edge decays with cancel latency. Code: btclat/trade/maker/.

- **Rule:** Up bid = min(floor((fair - 0.03) 100), ask - 1), Up ask = max(ceil((fair + 0.03) 100),
  bid + 1) on the pzm fair value; only mid in [0.10, 0.90], >= 30 s left; the bid is dropped
  when the v1_L50 model's Down prediction >= -0.03, the ask when its Up prediction >= -0.03.
  The ask is a BUY of Down at 1 - ask. Same decision instants and model as the simulator.
- **Inside gate (`--rule inside [--hyst H]`, default `--rule frozen`):** the pre-registered
  `vi_fair0.04_p-0.02` (research/predict/sim/rules.py `vinside`): the same gates at fair -/+ 0.04,
  pull -0.02, a side kept only when its tick is strictly inside the spread. `--hyst H` (H > 0)
  adds per-market insert hysteresis: a side enters at pred < -0.02 - H, leaves at pred >= -0.02
  (arm `vi_fair0.04_p-0.02_h<H>`). `--hyst` with `--rule frozen` is refused. Quote causes add
  `outside` (rule price not inside the spread) and `hyst` (held back by the hysteresis).
- **Orders:** 5 shares, post-only GTD (expiry server now + 185 s: the venue rejects < 180 s) or
  `--order-type GTC`; a quote crossing our book view is not sent; one order per side per market,
  replaced only after the cancel is confirmed. Every insert and cancel goes out on 3 warm
  connections at once (first ack wins; `--fanout 1..3`).
- **Caps (hard, lower only):** $25 open (fills + all resting notional, `--max-open`), $10 per
  market (`--market-cap`), 3600 inserts per hour, the shared $10 day loss cap and lock, KILL file.
  Wallet ~$73: enough for $25 open plus the loss cap and unredeemed winnings.
  `--dry` applies no money caps (loss headroom, market cap, max open, balance, day lock, loss-cap
  stop): the quote still goes out and a `would_skip` (`would_stop`) is logged instead.
- **Stops:** fatal rejects (region, auth, balance), an insert no copy answered, a cancel not
  confirmed after 3 tries (with order lookups in between), 20 rejects in a row. Cancel-all on exit.
- **Fills:** live, GET /data/order on each tape trade at or through the quote, every 3 s, and after
  the cancel; the simulator's inferred fills are logged next to them (`infer`) to check the rule.

Dry first (no orders, no keys, no signing library: the paper guard is installed), anywhere with
the feeds; `--record` keeps the raw feeds for the same-market simulator comparison:

```
nice -n 10 python3 -m btclat.trade maker --dry --hours 4 --ntp amazon --record --run dublin-makerdry-<TAG>
python3 -m btclat.trade.report --run dublin-makerdry-<TAG>          # after rsync of data/trade/
nice -n 10 python3 -m btclat.trade.report.maker.sim --run dublin-makerdry-<TAG>   # same-market sim, 5 sh
python3 -m btclat.trade.report --run dublin-makerdry-<TAG>          # now with the sim row
```

Inside gate, dry 1 h (same conventions; the report shows the would-skips under "would-skip
(caps, dry only)"):

```
nice -n 10 python3 -m btclat.trade maker --dry --rule inside --hours 1 --ntp amazon --record --run dublin-makerdry-inside-<TAG>
python3 -m btclat.trade.report --run dublin-makerdry-inside-<TAG>   # after rsync of data/trade/
```

Live (user approval; never next to micro or a hold test, whose cancel-all would cancel ours):

```
rsync -a btclat/trade/ ubuntu@<ip>:/tmp/trade/ && ssh ubuntu@<ip> \
  'sudo rsync -a --chown=btclat:btclat /tmp/trade/ /opt/btclat/btclat/trade/'
sudo -u btclat env BTCLAT_CONFIG=/opt/btclat/.config/btclat bash -c 'cd /opt/btclat && \
  .venv/bin/python -m btclat.trade maker --i-approve --hours 1 --ntp amazon --run dublin-maker-<TAG>'
# or, with HOURS / TAG in run.env: sudo systemctl start btclat-trade@maker
```

Inside gate, live 1 h (5 shares per quote, fixed; the hard caps above apply unchanged). h = 0: the
pre-registered swap to `--hyst 0.005` failed (ties h = 0, reports/fill-improve.md 2026-10-14 12:45).
`--record` keeps the feeds so the same hour can be replayed through research/predict/inside:

```
sudo -u btclat env BTCLAT_CONFIG=/opt/btclat/.config/btclat bash -c 'cd /opt/btclat && \
  .venv/bin/python -m btclat.trade maker --i-approve --rule inside --hours 1 --ntp amazon --record --run dublin-maker-inside-<TAG>'
```

Latency A/B under live load, no fill risk (reports/fill-improve.md 2026-10-14 14:45). The same
process, feeds and decision instants as the live hour, but every insert is a post-only BUY at 0.01
(`--far`: it cannot fill above 0.01, $0.05 per order at most) and each insert / cancel goes at
random through the in-process pool or the sender process (`--sender ab`, `via` on every ack).
`--record` keeps the CLOB feed so the venue's book stamps split each round trip:

```
sudo -u btclat env BTCLAT_CONFIG=/opt/btclat/.config/btclat bash -c 'cd /opt/btclat && \
  .venv/bin/python -m btclat.trade maker --i-approve --rule inside --far --sender ab --hours 1 --ntp amazon --record --run dublin-maker-far-ab-<TAG>'
python3 -m btclat.trade.report --run dublin-maker-far-ab-<TAG>                 # ack p50/p90 per via
python3 -m latency.infra.maker_latency.run --run dublin-maker-far-ab-<TAG>    # send/venue/ack split per via
```

`--sender proc` sends every insert / cancel from the sender process (maker/send/); `thread` (the
default) keeps the in-process pool. Locally: `taskset -c 0,1 python3 -m btclat.trade.maker.send.bench.run`.
Every live maker run now ends with a `reconcile` line (booked fills vs GET /data/trades and the
public Data API); the report prints it.

Report (`python3 -m btclat.trade.report --run <run>`): quoting activity and reject kinds, fills per
hour, 10 s and resolution markouts in c/$ (market bootstrap CI), adverse selection (10 s markout
split by whether the filled side's pull fired within 1 s after the fill), insert / cancel ack
p50 / p90 for the first copy and per copy, real vs inferred fills, and the run vs the simulator.
Money at risk: at most the $10 day loss cap plus open positions (<= $25) on a bad day.

## Rust bot `btclat-bot` (the live taker + model veto; replaces micro for `vt_v1_m0.02_trigger`)

Code: `rust/` (cargo workspace: `signal` state/features/veto engine, `model` tree evaluator, `venue`
signing/auth/HTTP2/hedged sends/user ws, `risk` hard limits + shared ledger, `tlog` JSONL logger,
`bot` binary). Orders: one BUY per veto order, 5 shares, FAK, **limit = seen ask + i with i = 0**
(binding; `--i X --allow-i-positive` for i > 0, logged loudly; randomized-i experiment only with
`--i-mode random --i-set 0,0.01 --i-random-experiment`), sent as k = 3 identical copies on 3 warm
HTTP/2 connections (venue dedupes; `--k 1..3`). Hard caps as Python micro (5 sh, $3 notional, $15
exposure, $10 day loss + lock file, 40 orders/h) plus 1 order in flight and >= 0.2 s per market;
the CLI can only lower them. Same ledger/lock/KILL files as `btclat.trade` (`~/.config/btclat`).
Stops: SIGTERM/SIGINT, KILL file, loss cap, fatal venue error, `--hours`; every stop sends
cancel-all (3 tries, k copies) and flushes + gzips the log before exit. Live refuses unless the
host clock is within 2 s of the CLOB server clock (chrony).

Model swap needs no code change: export the new pickle and pass its JSON + hash.

```
python3 -m research.predict.infer.export --model v1_L0                       # pre-registered v1 (hash from prereg2.json)
python3 -m research.predict.infer.export --path data/out/predict/models/<new>.pkl --sha256 <pkl sha256>
# -> data/out/predict/models/<name>.trees.json and .trees.json.sha256; the bot takes
#    --model <name> --model-sha256 <json sha256> (live refuses without the hash); the feature list
#    comes from the model's own vf (unknown columns are refused at start).
```

Hold-aware gate (reports/veto-hold.md section 5): `--model v1h_G_h250x_L0 --model-sha256
6761315ea71372322df0eb3e798612baa0d31151478a8cd8cfd0469d94b9c16e`. A gate model (inputs end in
`v1_value` + the 7 `x_*` book extras) loads its base `v1_L0.trees.json` pinned by hash in
`rust/crates/bot/src/setup.rs` (`BASES`) and its tau (-0.005) from its own JSON; v1 still decides
first, the gate vetoes v1 orders whose prediction is < tau, then the 0.2 s refractory. Parity:
`python3 -m btclat.paper.replay.gated` (reference from research's own `extras()`) and
`cargo test --release -p btl_bot --test decisions` (orders, the 7 extras and the gate bit-identical).

Build (here, cross via cargo-zigbuild + zig, or natively on the box) and install:

```
bash rust/deploy/build.sh                      # -> dist/btclat-bot-aarch64 (+ .sha256), Graviton3 tuned
bash rust/deploy/package.sh                    # -> dist/btclat-bot-kit.tgz (binary, deploy files, model JSONs, fair weights)
scp dist/btclat-bot-kit.tgz ubuntu@<ip>:~ && ssh ubuntu@<ip> \
  'rm -rf botkit && mkdir botkit && tar xzf btclat-bot-kit.tgz -C botkit && sudo bash botkit/rust/deploy/setup-bot.sh'
# edit /opt/btclat/.config/btclat/bot.env: HOURS, TAG, MODEL, MODEL_SHA256, EXTRA (e.g. --max-orders-hour 20)
```

Dry (no keys, no orders; signs with an ephemeral key to time it, logs every would-be order):

```
sudo systemctl start btclat-bot-dry            # or by hand:
sudo -u btclat env BTCLAT_HOME=/opt/btclat BTCLAT_CONFIG=/opt/btclat/.config/btclat \
  /opt/btclat/bin/btclat-bot run --dry --hours 1 --run dublin-botdry-<TAG>
```

Live (user approval; never next to `btclat-trade@micro/maker`, whose cancel-all would cancel ours):

```
sudo systemctl start btclat-bot-live           # = btclat-bot run --i-approve --hours $HOURS --model $MODEL --model-sha256 $MODEL_SHA256 $EXTRA
sudo -u btclat touch /opt/btclat/.config/btclat/KILL     # stop at once (cancel-all), blocks restarts
```

Logs: `data/trade/<run>/bot-<hour>.jsonl` (gzip'd on the hour and at exit), one JSON object per
event with `run`, `seq`, `mono_ns`, `wall_ns`: every feed receipt, every trigger signal with all 82
row features, both model outputs and the veto reason, every order (i, limit, sign / build ns, amounts),
each copy's send and ack (status, order id, latency, cf-ray / POP), book top-5 at send / ack / ack+3 s
/ ack+10 s, fills (POST answer, order lookup, trade poll, user websocket), cancels, risk skips,
errors, 60 s stats (feed lags, latency percentiles, risk state). About 1.7 GB/h plain while the
hour is open, ~0.3 GB/h gzip'd; `EXTRA=--log-feeds none` drops the feed lines (most of the volume).

Report (after rsync of data/trade/<run>): `python3 -m btclat.trade.report.rust --run <run>`
(micro-style sections, per-order hold table: seen ask, ask at the ack, depth survival, markout).

Parity (no network): the Rust engine replays recorded tape and must match the Python paper bot.

```
nice python3 -m btclat.paper.replay.decisions --root data/paper/dublin-20261012/raw --hours 497750,497751,497752,497753
rust/target/release/btclat-bot replay --root data/paper/dublin-20261012/raw --hours 497750,497751,497752,497753 \
  --i 0.02 --expect data/cache/rust/dec-497750-497753/decisions.jsonl
cd rust && BTL_REQUIRE_PARITY=1 cargo test --release            # incl. sklearn parity on the recorded model rows
```
