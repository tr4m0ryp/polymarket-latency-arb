"""Inference latency of the value model per decision, in microseconds.

    python3 -m research.predict.infer.bench [--model v1_L0]

Timed: (1) sklearn predict on one row (what the research code calls), (2) the same trees
compiled to C (infer/ctree.py) called through ctypes (includes ~1 us of ctypes overhead),
(3) the C tree loop alone over 100k rows in one call (per-row cost), (4) a linear model in C, (5) the
incremental feature update per Binance message in pure Python (infer/state.py). Checks that
the C scorer reproduces sklearn's predictions."""
from __future__ import annotations

import argparse
import ctypes
import time

import numpy as np

from .. import OUT
from ..model.data import load
from ..model.learners import clean
from ..model.stack import stacked
from ..model.store import load_model
from .ctree import CTree
from .state import bench_state


def _t(fn, n):
    t0 = time.perf_counter_ns()
    for _ in range(n):
        fn()
    return (time.perf_counter_ns() - t0) / n / 1e3


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="v1_L0")
    a = ap.parse_args()
    md = load_model(a.model)
    m, vf = md["model"], md["vf"]
    st, _ = stacked(load("select", frac=0.01, seed=5))
    X = clean(st[vf].to_numpy()).astype(np.float64)[:2000]
    ct = CTree(m)
    ref = m.predict(X)
    got = np.array([ct(np.ascontiguousarray(x)) for x in X])
    err = float(np.abs(ref - got).max())
    row = X[:1]
    res = {"trees": ct.n_trees, "nodes": ct.n_nodes, "features": len(vf), "max_abs_err": err}
    res["sklearn_1row_us"] = _t(lambda: m.predict(row), 300)
    x0 = np.ascontiguousarray(X[0])
    res["c_ctypes_us"] = _t(lambda: ct(x0), 20000)
    w = np.ascontiguousarray(np.random.default_rng(0).normal(size=len(vf)))
    lin = lambda: ct.lib.linear(x0.ctypes.data_as(ctypes.c_void_p), w.ctypes.data_as(ctypes.c_void_p),  # noqa: E731
                                ctypes.c_int(len(vf)), ctypes.c_double(0.0))
    res["c_linear_ctypes_us"] = _t(lin, 20000)
    res["ctypes_call_floor_us"] = res["c_linear_ctypes_us"]
    big = np.tile(X, (50, 1))
    t0 = time.perf_counter_ns()
    ct.many(big)
    res["c_tree_per_row_us"] = (time.perf_counter_ns() - t0) / len(big) / 1e3
    res.update(bench_state())
    lines = [f"- {k}: {v:.3f}" if isinstance(v, float) else f"- {k}: {v}" for k, v in res.items()]
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "inference.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
