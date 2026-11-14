"""Order-book prediction for the BTC 5m latency trade (reports/predict.md).

Predict, from the Binance perp + spot top of book and trades on our receipt clock, the move
that Polymarket's 5m makers have not yet priced when a taker order matches after the 150 ms
hold. Layout: ingest/ (run-3 perp trades), feats/ (event-time features), targets/ (Binance
and Polymarket horizons), model/ (fit, decay curve, inference timing), sim/ (trading rules
in the strategy replay simulator), report/ (tables). Read-only research: no orders.

Run from the repo root as modules, e.g. `python3 -m research.predict.feats.build`."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CACHE = Path(os.environ.get("BTCLAT_PREDICT_CACHE", ROOT / "data" / "cache" / "predict"))  # paper report override
OUT = ROOT / "data" / "out" / "predict"

# Splits, fixed before any fitting (2026-10-11 14:10 UTC).
RUN2 = 1791583200       # 2026-10-09 22:00 UTC: first hour with the perp book
SPLIT = 1791626400      # 2026-10-10 10:00 UTC: run 2 train | run 2 select
RUN3 = 1791669600       # 2026-10-10 22:00 UTC: run 3 (perp trades from here)
RUN3_DEV_END = 1791705600  # 2026-10-11 08:00 UTC: run 3 dev | run 3 final test

H_MS = (50, 100, 150, 200, 300, 500, 1000)   # prediction horizons
L_MS = (-40, 0, 50)                          # receipt -> CLOB offsets evaluated
HOLD = 0.150
TICK_PERP = 0.1


def segment(start: float) -> str:
    """Split label of a 5m market by its start time."""
    if start < RUN2:
        return "run1"
    if start < SPLIT:
        return "train"
    if start < RUN3:
        return "select"
    if start < RUN3_DEV_END:
        return "dev3"
    return "test3"
