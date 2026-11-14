"""Veto arm under the measured venue hold (reports/veto-hold.md).

Replays the 48 h Dublin paper run's own would-be orders (data/paper/dublin-20261012) of the
taker + model veto arm `vt_v1_m0.02_trigger` (and micf / vt_v1_m0.03_any for comparison)
through the ~270 ms taker hold measured on the 195 live FAK orders of 2026-10-13: each order
matches at decision + h, h drawn from the live decision -> match distribution, against the
venue-clock book (research/strategy/sim/grid.py, 5 ms grid, venue stamps). Then decomposes
the loss and scores pre-registered fixes on hours not used to select them. Read-only.

    PYTHONPATH=. nice -n 10 python3 -m research.vetohold.replay.run      # rows.pkl
    PYTHONPATH=. nice -n 10 python3 -m research.vetohold.tables.headline
    PYTHONPATH=. nice -n 10 python3 -m research.vetohold.tables.decompose
    PYTHONPATH=. nice -n 10 python3 -m research.vetohold.fixes.prereg     # frozen before test
    PYTHONPATH=. nice -n 10 python3 -m research.vetohold.fixes.score"""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUN = ROOT / "data" / "paper" / "dublin-20261012"
# the research store / predict tables read the paper run's own recording (btclat/paper/report/sim.py)
os.environ.setdefault("BTCLAT_LIVE", str(RUN / "raw"))
os.environ.setdefault("BTCLAT_STRATEGY_CACHE", str(RUN / "cache" / "strategy"))
os.environ.setdefault("BTCLAT_PREDICT_CACHE", str(RUN / "cache" / "predict"))

OUT = ROOT / "data" / "out" / "vetohold"
VETO, ANY, MICF = "vt_v1_m0.02_trigger", "vt_v1_m0.03_any", "micf"
ARMS = (VETO, ANY, MICF)
KS = range(0, 11)                # limit = seen + i cents, i = 0..10
PV = (0, 1, 2, 3)                # limit = model value price (seen + edge + fee) minus j cents
FP = (0, 2)                      # limit = settlement fair value (fair_p) minus j cents
LIMS = [f"k{i}" for i in KS] + [f"pv{j}" for j in PV] + [f"fp{j}" for j in FP]
SPAN = 30                        # ladder reaches seen + 30 c (for i*, the needed offset)
SIZES = (5.0, 15.0, 30.0, 60.0)  # shares (paper arm: 60)
SPLIT = 1791849600.0             # 2026-10-13 00:00 UTC: selection hours before, test hours after
DAY_MARKETS = 288
