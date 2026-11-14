"""Match-cost anchor for the identity projection (C3 round 2).

The identity holds on the book at the MATCH: v_up + v_dn = -c_m, c_m = spread + both fees at
t + L + 150 ms. Round 1 anchored on the seen book (c_seen). diag_e showed that at firing rows
the spread widens during the hold (c_seen - c_m = -1 to -3 c at L = 0), so the c_seen anchor
credits every fired row with half that widening and the true common-mode error (pred_up +
pred_dn + c_m, +0.6 to +2.5 c at the frozen taker's rows) stays hidden. Fix: anchor on
c_hat = E[c_m | x], a small regression fitted on run 2 train only (never evaluated, before
both folds, the v1 model's own training window), so the arm stays fold-invariant:

    v_side = (pred_side - pred_other) / 2 - c_hat / 2

Training rows come through the harness Fold.load_rows (train window) of a private Fold object,
so the harness's own folds are untouched. The fit is cached on disk."""
from __future__ import annotations

import pickle

import numpy as np
import pandas as pd

from research.predict import CACHE
from research.predict.improve.harness import windows as W
from research.predict.improve.harness.fold import Fold
from research.predict.improve.harness.guard import SEALED
from research.predict.model.learners import clean, gbdt_reg

from .score import costs, fee

DIR = CACHE / "improve" / "c3"
SIGNED = ["p_dmic0.025", "p_dmic0.05", "p_dmic0.1", "p_dmic0.25", "p_dmic1", "p_dmid0.1", "p_dmid1",
          "p_dmid5", "p_micoff", "p_ofi0.1", "p_ofi0.4", "s_dmic0.1", "s_dmic0.25", "s_dmic1",
          "s_dmid1", "s_micoff", "st_sv0.2", "st_sv1", "basis_dev", "mic_dev", "pm_stale", "fair_dz"]
PLAIN = ["p_spr", "p_lam", "p_tsm", "p_ttd_min", "s_spr", "s_lam", "s_tsm", "st_tn", "st_big", "pm_mid",
         "pm_spr", "secs_left", "sigma", "pm_tsc", "bk0", "bk1", "bk2", "gap", "zs"]
_FIT: dict[int, object] = {}


def xcost(tab: pd.DataFrame) -> np.ndarray:
    """Cost-model inputs: magnitudes of the signed moves, plain state, the seen cost."""
    cols = [np.abs(tab[c].to_numpy(float)) if c in tab else np.zeros(len(tab)) for c in SIGNED]
    cols += [tab[c].to_numpy(float) if c in tab else np.zeros(len(tab)) for c in PLAIN]
    mid = tab["pm_mid"].to_numpy(float)
    cols += [costs(tab), np.abs(mid - 0.5)]
    return clean(np.column_stack(cols))


def _fit(L: int):
    need = ["t", "pm_bb", "pm_ba", "pm_mid", "secs_left", f"x_ba{L}", f"x_bb{L}", f"x_bad{L}"] + SIGNED + PLAIN
    d = Fold("A").load_rows(windows=("train",), cols=list(dict.fromkeys(need)))
    assert d["m"].map(W._markets().start).max() < SEALED
    ba, bb = d[f"x_ba{L}"].to_numpy(float) / 100, d[f"x_bb{L}"].to_numpy(float) / 100
    ok = ((d["pm_bb"] > 0) & (d["pm_ba"] < 100) & d["pm_mid"].between(0.05, 0.95) & (d["secs_left"] >= 20)).to_numpy().copy()
    ok &= (ba > 0.005) & (ba < 0.995) & (bb > 0.005) & (bb < 0.995) & (d[f"x_bad{L}"].to_numpy() == 0)
    act = (np.abs(d["p_dmic0.1"].to_numpy(float)) >= 0.001) | (np.abs(d["s_dmic0.1"].to_numpy(float)) >= 0.001)
    keep = ok & (act | (np.random.default_rng(3).random(len(d)) < 0.25))
    y = np.clip((ba - bb) + fee(ba) + fee(1 - bb), 0, 0.3)[keep]
    X = xcost(d.loc[keep])
    m = gbdt_reg(max_iter=300, leaves=31, lr=0.06, min_leaf=200).fit(X, y)
    print(f"cost model L={L}: {keep.sum():,} rows, mean c_m {y.mean():.4f}", flush=True)
    return m


def cost_model(L: int):
    if L not in _FIT:
        p = DIR / f"cost_L{L}.pkl"
        if p.exists():
            _FIT[L] = pickle.loads(p.read_bytes())
        else:
            _FIT[L] = _fit(L)
            DIR.mkdir(parents=True, exist_ok=True)
            p.write_bytes(pickle.dumps(_FIT[L]))
    return _FIT[L]


def chat(tab: pd.DataFrame, L: int) -> np.ndarray:
    """E[c_m | x] per row ($ per share pair), never below the seen spread + fees floor of 0."""
    return np.maximum(cost_model(L).predict(xcost(tab)), 0.0)
