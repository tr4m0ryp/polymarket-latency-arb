"""Strategy search for the BTC 5m latency trade: a replay paper simulator over the live
recordings (ingest/ -> sim/), signal rules (signals/) and held-out evaluation (eval/).

Run from the repo root as modules, e.g. `python3 -m research.strategy.ingest.run`."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
# BTCLAT_LIVE / BTCLAT_STRATEGY_CACHE let the paper bot's report replay its own recording
# (btclat/paper/report/sim.py); unset, the paths are the research defaults.
LIVE = Path(os.environ.get("BTCLAT_LIVE", ROOT / "data" / "live"))
CACHE = Path(os.environ.get("BTCLAT_STRATEGY_CACHE", ROOT / "data" / "cache" / "strategy"))
OUT = ROOT / "data" / "out" / "strategy"
DT = 0.005  # book grid step (s)


def fee(p):
    """Taker fee per share at our 0% rebate tier (crypto_fees_v2)."""
    return 0.07 * p * (1 - p)
