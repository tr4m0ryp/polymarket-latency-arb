# Bankroll caps for the taker + veto arm (stopped unfinished)

**Stopped unfinished at the user's redirect to the pair strategy (2026-10-14 ~18:15 UTC): the directional markout objective is superseded; no cap set was validated on test hours.**

## What was measured before the stop

- **Taker hold unchanged (most important):** the 48 ms "send to ack" of run dublin-bot-20261014b is the
  first answer of 3 duplicate copies, and those fast answers are pre-engine rejects (duplicate /
  "balance", p50 52 ms, n = 50). The copy that reaches the matching engine answers at **p50 294 ms**;
  decision to match (engine ack - 14 ms) **p10 240 / p50 280 / p90 939 ms** (n = 25) vs 234 / 276 / 574
  on 2026-10-13. The replay hold assumption stands (`research/bankroll/stream/hold.py`).
- **"Balance" rejects were copy collisions:** the venue reserves the first copy's amount, so the other
  copies fail the balance check once the wallet is under 2x the order; every one of the 25 orders got
  an engine answer. The bot itself skipped 33 signals for balance.
- **Simulator validated:** replay at 60 sh, unlimited cash reproduces veto-hold test hours (v1 229
  orders/h, 32.2 fills/h vs 228 / 32.3). Resolution PnL at 60 sh unlimited: v1 +$693/day selection,
  +$335 test; v1h +$1,123 selection (in-sample), +$496 test.
- **Uncapped live config from $100 (60 sh, selection hours):** median $2.5 after 24 h, P(< $50) 73%.
- **Opposite-side fills:** with no side rule 27-41% of filled markets get fills on both sides
  (60 sh, no caps), from separate veto signals.
- **No grid point met P(ever < $25 in 7 d) <= 1% with only a daily drawdown pause** (stage 2, best
  5.4%). With fills <= 2, a 15% day pause and a +0.5 c minimum edge, 20 of 144 finalists met every
  constraint on selection hours: best `Kelly x0.1 | mkt 10% | open 25% | any side | fills 2 | dd 15% |
  edge +0.5c`, 24 h median $101 (p10 $84), 7 d median $213 (p10 $67), P(< $25 in 7 d) 0%, worst
  single market 10% of equity, ~3 fills/h. Never scored on test hours, v1h or the new hold.
- **Floor-halt amendment unfinished:** its first run was void (numba `cache=True` kept a stale
  kernel, floors were no-ops; fixed with `cache=False`); the rerun was killed at the redirect.

## What exists

- `research/bankroll/`: order streams (`stream/`, both models, 3 holds x 16 draws), the numba cash-flow
  kernel (`sim/kernel.py`: reservation until ack, fills on the held book with own-take memory, payout
  at end + redeem delay, side policies, day pause, floor halt), the pre-registration with two amendments
  (`data/out/bankroll/prereg.json`), stage-1/2 scripts and outputs (`final.csv`, `final2-floor-noop.csv`).
- **Rust bot** (`rust/crates/risk/src/bankroll/`, `book/bank.rs`, exec + cli): balance-scaled sizing
  (fixed / fraction / Kelly), per-market and open caps as fractions of equity, side policies (any / one /
  per-side / hedge), fills per market, day drawdown pause, all-time-peak floor halt, and **`--reserve`**
  (bankroll = balance - reserve for every size, cap, drawdown and affordability check; nothing is sent
  at <= 0). Deploy: `RESERVE=43.04` in `bot.env`, passed by both units; default model v1h_G_h250x_L0.
  CLI cap defaults are the provisional selection-hours point above (min edge not implemented).
  Tests: `crates/risk/tests/bankroll.rs` (10), `crates/bot/tests/sizing.rs` (reserve flag); `cargo test` green.
- **Not done:** test-hours scoring, v1h as primary, ablation, $26 line, the aarch64 kit rebuild.
- **Blocker for any compounding:** the bot never redeems; winnings return to cash only after a manual
  claim (equity counts resolved winnings as `claim` until a balance read rises).
