"""Fill censoring: is the busy-hour over-prediction of the frozen 1 s model carried by orders
that never fill?

The row-level target (best venue ask at the match, marked 1 s later) is defined on every row;
money only on the rows where our limit order (seen ask + 2 c) still finds depth after the
150 ms hold. If the rows the model over-predicts are the ones where the venue repriced during
the hold, the limit misses them and the fills stay calibrated, so correcting the row-level
calibration removes trades that were not losing.

    python3 -m research.predict.improve.diag.calibration.censor.table"""
