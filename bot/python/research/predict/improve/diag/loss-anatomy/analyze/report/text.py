"""Static prose of the loss-anatomy result: header, method, idea ledger, hypotheses."""

HEAD = """# Loss anatomy of the deployed predictive arms (diagnostic)

Date 2026-10-12. Code `research/predict/improve/diag/loss-anatomy/`, tables
`data/out/predict/improve/loss-anatomy/*.csv`. Arms: 1 s taker `vt_v1_m0.03_any` (taker1s), trigger
veto `vt_v1_m0.02_trigger` (veto), micf for contrast; L = 0 and -40; frozen fills of the select
(sel1), dev3 (dev1), test3 run 1 (final) and extension (ext) runs, {n:,} fills on {mk} markets. No
re-simulation; edge = 10 s markout. Sealed prereg2 segment (start >= 1791744900) never opened: market
lists come from frozen market files, every script asserts max(start) < 1791744900, and Polymarket
events are read only from hour files ending by 18:00 UTC (the eleven 18:00-18:50 ext markets have no
venue-depth columns). Diagnostic only: no arm, model or threshold of the frozen arms changes.
"""

METHOD = """## Method

Each fill is joined to its decision-table row (exact for the value-model arms, as-of for micf) for
Binance vol and message rate, Polymarket spread / staleness / recent repricing, the venue book
replayed at the decision (top size, depth to the limit, liquidity within 5 c), price level, time
to expiry, strike distance (|z| of the fair price, settlement delta), own history (burst
position, fills in the last 5 s, fills so far) and the 1 s model's prediction for both sides.
Loss = 10 s markout < 0. AUC with a 400-draw market bootstrap; $/day over all markets of the
windows read; gate effects = minus the markout of the fills a rule would have dropped, market
bootstrap (an approximation: a dropped order frees the 0.2 s refractory and the depth memory).
"""

IDEAS = """## 6. Ideas tested here and their status

| idea | status | evidence / premises |
|---|---|---|
| delta floor (no order below 3-6 c/bp) | **open, positive** (screen, not re-simulated) | picked on select + dev3, positive on test3 run 1 + ext in 4 of 4 arm x L, CI above 0 in 1 (taker1s L-40); zero cost in quiet windows |
| Binance vol gate (rv60 > 4 bp) | **lost a comparison** to the delta floor | helps ext (+$121 to +$1,150/day) but costs $18-196/day in select and dev3 |
| require Polymarket staleness (pm_stale > 0) | **lost a comparison** | removes the 1 s taker's early entries: -$300 to -$920/day in every window |
| drop expensive tokens (seen > 0.80) | **lost a comparison** | negative in 11 of 16 window reads |
| two-side gap cut (pred - pred_other < select q20) | **lost a comparison** as a cut; **never tested** as a model constraint | ranks losers better than pred in 6 of 6 arm x L (AUC) but the cut loses money in 11 of 16 reads |
| burst / own-history cap, no adding to a losing fill | **lost a comparison** | AUC 0.42-0.60 with sign flips by window; adding to a loser is +6 to +20 c/$ outside ext (agrees with the report's cap round) |
| select-chosen gate on any of 52 state variables | **lost a comparison** | the best select cut never had an unseen CI above 0: select has no busy hours |
"""

HYPOTHESES = """## 7. Testable hypotheses (for the improvement round)

1. **Delta-aware value model.** Recalibrate the 1 s model's output on (pred, settlement delta,
   busy-state) with a monotone fit on train + select + dev3 rows (dev3 brings the low-delta states),
   or retrain with delta-interacted targets. Predicted: removes the low-delta busy fills (the
   floor screen alone: +$61 to +$328/day on test3 run 1 + ext) and raises the value of high-delta
   quiet rows (realized 1 s exceeds pred by 2-4 c there). Test: re-simulate on test3 run 1 + ext, paired vs the frozen arm;
   then on fresh hours after prereg2.
2. **Delta floor (cheapest form of 1).** No order when delta < 3 c/bp (pick 3-6 on select + dev3).
   Predicted: zero effect in quiet hours, positive in busy hours. Test: re-simulation on all allowed
   windows with paired CI vs the frozen arms; falsified if the busy-hour gain does not survive the
   knock-on fills.
3. **Busy-window selection rule.** Any regime-dependent margin must be selected on a window that
   contains busy hours. Test: the same gate family picked on select alone vs on select + dev3, read
   on ext: the select pick should keep failing.
4. **The ext shift is more than delta.** In ext the model over-predicts in every delta bin; the
   candidate cause is faster rival repricing (competition lens). Test: add the Polymarket top-change
   rate or rival taker flow as a calibration input and check the ext residual.
5. **High-value compression -> conditional size.** At pred >= 6 c and delta >= 12 c/bp (quiet hours)
   realized value exceeds pred; size up there (e.g. 150 sh) and keep 60 elsewhere. Test: re-sim; the
   50 ms competition table says the high-delta fills of the taker are the ones rivals take first,
   so test under J = 0.05 too.
6. **Two-side coherence as a model constraint.** value_up + value_dn = -(spread + both fees) at the
   match, whatever the mark; pred + pred_other drifts from it. Train or post-process the two sides
   jointly (antisymmetric part as the score). Test: AUC and re-sim vs pred alone.
"""
