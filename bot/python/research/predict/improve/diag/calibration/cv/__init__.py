"""Two-fold window cross-validation of recalibration families on the harness simulator.

The earlier regime-margin pick (recal/choose.py) was made on select only, after the family had
been proposed from the margin sweep on the unseen windows. Here every variant of a family is
simulated once on all 395 allowed markets (harness worker, unchanged fill logic), the variant
is chosen per L on one fold's choose windows and scored on the other fold's windows (fold A:
choose select + dev3, score test3 run 1 + ext; fold B the reverse), so every market is scored
by a variant chosen without it.

    OMP_NUM_THREADS=1 nice -n 10 python3 -m research.predict.improve.diag.calibration.cv.driver --family taker_margin
    python3 -m research.predict.improve.diag.calibration.cv.score --family taker_margin"""
from .. import OUT as _OUT

OUT = _OUT / "cv"
