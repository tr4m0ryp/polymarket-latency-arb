"""C1: conviction-keyed order size on the identity-projected value v*, with a low-delta busy cap.

The deployed arms fire unchanged; the size of each order follows the model's conviction
(K x value, clipped), keyed on v* = (pred_side - pred_other) / 2 - (spread + both fees) / 2,
which strips the symmetric (volatility) error the 1 s model adds in busy hours.

value.py  fee, costs, v*, symmetric residual, settlement delta
arms.py   _Size decision rule and the harness families (size_taker, size_veto, sweeps)
run.py    harness run that also keeps every variant's per-market aggregates
score.py  offline tables: every variant, fold choice, gain vs the frozen veto"""
from .arms import size_taker, size_veto  # noqa: F401
