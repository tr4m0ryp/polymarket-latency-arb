"""Backrun: does the latency taker's order still fill after the venue's taker delay?

Replays the simplest documented trigger of the old paper bot (`theirs_spot`, bot/python/
research/strategy/eval/arms/sweep1.py: side = sign of the last 3 s Binance spot move, any
move, at most one order per 2 s, favourite <= 0.90, >= 30 s left) on the 48 h Dublin paper
recording. Order = FAK buy of a $12 clip on the favoured side, limit = the ask we saw at the
decision. It fills against whatever still rests at prices <= the limit on the venue-clock
book at decision + d (d = 0 / 165 / 250 / 330 ms), fully or partially, and is held to
resolution. Read-only: no orders, no network.

    export BACKRUN_DATA=/path/to/private/data      # holds paper/ and trade/
    python -m backrun.replay.run                   # per-order rows (BACKRUN_OUT, default backrun/out)
    python -m backrun.report.run                   # backrun/results.json
    python figures/make_bounds.py                  # figures/bounds.png"""
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DATA = Path(os.environ.get("BACKRUN_DATA", REPO / "data"))
RUN = DATA / "paper" / "dublin-20261012"          # 48 h Dublin paper recording
LIVE_RUNS = ("dublin-micro-20261013", "dublin-micro-20261013b")
OUT = Path(os.environ.get("BACKRUN_OUT", REPO / "backrun" / "out"))
RESULTS = REPO / "backrun" / "results.json"

# the archived simulator (book grid, feeds, market store) reads its inputs from these
os.environ.setdefault("BTCLAT_LIVE", str(RUN / "raw"))
os.environ.setdefault("BTCLAT_STRATEGY_CACHE", str(RUN / "cache" / "strategy"))
sys.path.insert(0, str(REPO / "bot" / "python"))
sys.path.insert(0, str(REPO))

CLIP = 12.0                       # dollars per order at the seen ask
DELAYS = (0, 165, 250, 330)       # decision -> match, ms (0 = venue book at the decision)
LONDON, DUBLIN = 165, 330
GATE = dict(band=(0.01, 0.99), tleft=30.0, fav_max=0.9)
# name -> (source, window s, threshold bp, refractory s); the first is the primary arm
ARMS = {"theirs_spot": ("spot", 3.0, 1e-4, 2.0),     # documented baseline, nothing tuned
        "spot_1bp": ("spot", 3.0, 1.0, 2.0)}         # sensitivity: moves >= 1 bp only
PRIMARY = "theirs_spot"

# README economics (the "every order fills" case)
G_README = 2.44                   # cents per dollar, incumbents' measured gross edge
P_TYP = 0.57
FEE_CPD = 100 * 0.07 * (1 - P_TYP)   # 3.01 c per dollar traded
VOLUME = 5.76e6                   # dollars per 30 days
TIERS = (0.0, 0.03, 0.08, 0.18, 0.32, 0.44, 0.50)
