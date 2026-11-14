"""Harness plug-ins of C5 (each refits per fold; run with --L=0, CRITERION lcb).

    busy_refit : the three pre-registered variants, chosen per fold on its choose windows
    rf_plain   : refit on train + choose windows, unweighted
    rf_bal     : the same rows, regime-balanced weights (each busy tertile equal weight)
    rf_bal_coh : rf_bal scored through the identity projection (C3)

    nice -n 10 python3 -m research.predict.improve.harness --L=0 \
        --arm research.predict.improve.cand.<this package>.candidates:busy_refit --out ..."""
from __future__ import annotations

from .arms import arm
from .fit.model import fit_fold

FRAC = 0.25


def _m(fold, names):
    return fit_fold(fold, names, frac=FRAC)


def busy_refit(fold):
    m = _m(fold, ("plain", "bal"))
    return [arm("rf_plain_m3", m["plain"]), arm("rf_bal_m3", m["bal"]),
            arm("rf_bal_coh_m3", m["bal"], coh=True)]


def rf_plain(fold):
    return arm("rf_plain_m3", _m(fold, ("plain",))["plain"])


def rf_bal(fold):
    return arm("rf_bal_m3", _m(fold, ("bal",))["bal"])


def rf_bal_coh(fold):
    return arm("rf_bal_coh_m3", _m(fold, ("bal",))["bal"], coh=True)


for _f in (busy_refit, rf_plain, rf_bal, rf_bal_coh):
    _f.CRITERION = "lcb"
    _f.SELECT_L = 0
