"""C5: busy-inclusive, regime-balanced retrain of the 1 s value model (L = 0).

The frozen v1_L0 was fitted on run 2 train only (quiet weekend hours); in the busy ext hours
its inputs sit outside train (domain AUC 0.855, busy calibration slope 0.75) and its
predictions inflate. Here the same model (features, target, 200 x 15 GBDT) is refitted per
fold on train + the fold's choose windows, so fold B sees the only busy hours available
(test3 run 1 + ext), optionally with regime-balanced weights (busy tertiles of train carry
equal weight) and the identity projection of C3. The trading rule stays the frozen one.

    fit/busy.py    busy index per training row (calibration ctx) and tertile weights
    fit/model.py   per-fold refit, cached on disk by (fold, scheme, frac, seed)
    arms.py        decision rule: refit predictions (+ projection) -> frozen 1 s taker rule
    candidates.py  harness CLI plug-ins (busy_refit, rf_plain, rf_bal, rf_bal_coh)
    plan.py        arm sets and views for the multi-view driver
    eval/          one simulation pass -> every view in harness format, memoised, + summary"""
