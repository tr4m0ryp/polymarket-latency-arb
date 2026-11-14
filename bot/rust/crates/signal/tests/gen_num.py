"""Fixture for tests/num.rs: scipy ndtri/ndtr, numpy pairwise sums, Python round(x, 3).
    python3 rust/crates/signal/tests/gen_num.py"""
import json
from pathlib import Path

import numpy as np
from scipy.special import ndtr, ndtri

rng = np.random.default_rng(7)
ys = np.concatenate([rng.uniform(0.02, 0.98, 3000), np.linspace(0.02, 0.98, 97), [0.135335283236612691, 0.5, 0.864]])
xs = np.concatenate([rng.normal(0, 2, 3000), rng.uniform(-9, 9, 1000), [0.0, 0.7071067811865476, -1.0, 1.0]])
sums = []
for n in (1, 5, 8, 9, 64, 129, 240, 241, 300, 1000):
    a = rng.normal(size=n) * 10 ** rng.uniform(-4, 4, size=n)
    sums.append({"a": [float(x) for x in a], "sum": float(a.sum()), "mean": float(np.mean(a))})
ts = rng.uniform(1.79e9, 1.80e9, 2000)
out = {"ndtri": [[float(y), float(ndtri(y))] for y in ys], "ndtr": [[float(x), float(ndtr(x))] for x in xs],
       "sums": sums, "round3": [[float(t), round(float(t), 3)] for t in ts]}
Path(__file__).with_name("fixtures").joinpath("num.json").write_text(json.dumps(out))
