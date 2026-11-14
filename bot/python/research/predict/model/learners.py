"""The learners compared on every target: literature baselines (queue imbalance, OFI, the
leaders' microprice-change rule), a linear logistic model on all features, and a small
gradient-boosted tree ensemble (sklearn HistGradientBoosting)."""
from __future__ import annotations

import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier, HistGradientBoostingRegressor
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

BASE_COLS = {"imb": ["p_imb", "s_imb"],                       # Gould & Bonart 2016
             "ofi": ["p_ofi0.025", "p_ofi0.1", "p_ofi0.4", "p_ofi1.6",
                     "s_ofi0.1", "s_ofi0.4"],                 # Cont, Kukanov & Stoikov 2014
             "micro": ["p_micoff", "s_micoff", "p_imb", "s_imb", "p_spr"]}  # Stoikov 2018


def clean(X: np.ndarray) -> np.ndarray:
    return np.nan_to_num(X.astype(np.float32), nan=0.0, posinf=0.0, neginf=0.0)


def logit(C: float = 1.0):
    return make_pipeline(StandardScaler(), LogisticRegression(C=C, max_iter=300))


def gbdt(max_iter: int = 300, leaves: int = 31, lr: float = 0.08, seed: int = 0):
    return HistGradientBoostingClassifier(max_iter=max_iter, max_leaf_nodes=leaves, learning_rate=lr,
                                          l2_regularization=0.1, early_stopping=True,
                                          validation_fraction=0.1, n_iter_no_change=20,
                                          random_state=seed)


def gbdt_reg(max_iter: int = 300, leaves: int = 31, lr: float = 0.06, seed: int = 0, loss="squared_error",
             min_leaf: int = 20):
    return HistGradientBoostingRegressor(max_iter=max_iter, max_leaf_nodes=leaves, learning_rate=lr,
                                         min_samples_leaf=min_leaf,
                                         l2_regularization=0.1, early_stopping=True, loss=loss,
                                         validation_fraction=0.1, n_iter_no_change=20,
                                         random_state=seed)


def ridge(alpha: float = 10.0):
    return make_pipeline(StandardScaler(), Ridge(alpha=alpha))


def leader_score(df) -> np.ndarray:
    """The leaders' side signal: perp + spot microprice change over the last 100 ms."""
    return np.nan_to_num(df["p_dmic0.1"].to_numpy(float) + df["s_dmic0.1"].to_numpy(float))
