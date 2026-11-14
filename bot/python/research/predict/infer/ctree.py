"""Export a fitted HistGradientBoostingRegressor to flat C arrays, compile a scorer with gcc
-O2 and call it through ctypes: the inference cost a production bot would pay per decision.

Node layout per tree (sklearn `_predictors[i][0].nodes`): feature_idx, num_threshold,
left, right, is_leaf, value, missing_go_to_left. Thresholds are raw feature values."""
from __future__ import annotations

import ctypes
import subprocess
import tempfile
from pathlib import Path

import numpy as np

C_SRC = r"""
#include <stdint.h>
double score(const double *x, const int32_t *feat, const double *thr, const int32_t *left,
             const int32_t *right, const uint8_t *leaf, const double *val, const int32_t *root,
             int n_trees, double base) {
    double s = base;
    for (int t = 0; t < n_trees; t++) {
        int i = root[t];
        while (!leaf[i]) i = (x[feat[i]] <= thr[i]) ? left[i] : right[i];
        s += val[i];
    }
    return s;
}
void score_many(const double *X, int n_rows, int n_feat, const int32_t *feat, const double *thr,
                const int32_t *left, const int32_t *right, const uint8_t *leaf, const double *val,
                const int32_t *root, int n_trees, double base, double *out) {
    for (int r = 0; r < n_rows; r++)
        out[r] = score(X + (long)r * n_feat, feat, thr, left, right, leaf, val, root, n_trees, base);
}
double linear(const double *x, const double *w, int n, double b) {
    double s = b;
    for (int i = 0; i < n; i++) s += w[i] * x[i];
    return s;
}
"""


class CTree:
    def __init__(self, model):
        feat, thr, left, right, leaf, val, root = [], [], [], [], [], [], []
        off = 0
        for pred in model._predictors:
            nd = pred[0].nodes
            root.append(off)
            feat += list(nd["feature_idx"])
            thr += list(nd["num_threshold"])
            left += list(nd["left"] + off)
            right += list(nd["right"] + off)
            leaf += list(nd["is_leaf"])
            val += list(nd["value"])
            off += len(nd)
        self.arr = [np.ascontiguousarray(np.array(a, dtype=d)) for a, d in (
            (feat, np.int32), (thr, np.float64), (left, np.int32), (right, np.int32),
            (leaf, np.uint8), (val, np.float64), (root, np.int32))]
        self.n_trees, self.base = len(root), float(model._baseline_prediction.ravel()[0])
        self.n_nodes = off
        d = Path(tempfile.mkdtemp())
        (d / "s.c").write_text(C_SRC)
        subprocess.run(["gcc", "-O2", "-shared", "-fPIC", "-o", str(d / "s.so"), str(d / "s.c")], check=True)
        self.lib = ctypes.CDLL(str(d / "s.so"))
        self.lib.score.restype = ctypes.c_double
        self.lib.linear.restype = ctypes.c_double
        self._ptrs = [a.ctypes.data_as(ctypes.c_void_p) for a in self.arr]

    def many(self, X: np.ndarray) -> np.ndarray:
        X = np.ascontiguousarray(X, dtype=np.float64)
        out = np.empty(len(X))
        self.lib.score_many(X.ctypes.data_as(ctypes.c_void_p), ctypes.c_int(len(X)), ctypes.c_int(X.shape[1]),
                            *self._ptrs, ctypes.c_int(self.n_trees), ctypes.c_double(self.base),
                            out.ctypes.data_as(ctypes.c_void_p))
        return out

    def __call__(self, x: np.ndarray) -> float:
        return self.lib.score(x.ctypes.data_as(ctypes.c_void_p), *self._ptrs,
                              ctypes.c_int(self.n_trees), ctypes.c_double(self.base))
