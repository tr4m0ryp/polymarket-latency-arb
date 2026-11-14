"""Calibration and regime-drift diagnostic of the frozen value models (post-freeze).

Question: do the 1 s value models (v1_L0, v1_L-40; v3p_L0 of the retired primary for
contrast) over-predict when activity jumps (Binance message rate, realised volatility,
Polymarket book update rate), how far do the feature distributions move between run 2 train
and the later windows, which features carry the over-prediction, and which recalibration form
(regime-scaled margin, isotonic per regime, lower-bound prediction) the numbers support.

Reads only allowed markets: train (run 2 first 12 h), select, dev3, test3 run 1 (final) and
ext; every entry point asserts max(market start) < SEALED (prereg2 test segment).

    nice -n 10 python3 -m research.predict.improve.diag.calibration.rows.build
    python3 -m research.predict.improve.diag.calibration.analyze.calib
    python3 -m research.predict.improve.diag.calibration.analyze.shift
    python3 -m research.predict.improve.diag.calibration.analyze.attrib
    python3 -m research.predict.improve.diag.calibration.recal.rows
    nice -n 10 python3 -m research.predict.improve.diag.calibration.recal.sim
    python3 -m research.predict.improve.diag.calibration.recal.score"""
from ..... import predict

SEALED = 1791744900          # 2026-10-11 18:55 UTC: prereg2 test segment starts here
OUT = predict.OUT / "improve" / "calibration"
CACHE = predict.CACHE / "improve" / "calibration"

WINDOWS = ("train", "select", "dev3", "final", "ext")
MODELS = ("v1_L0", "v1_L-40", "v3p_L0")
