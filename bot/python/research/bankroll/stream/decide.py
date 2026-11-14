"""The two arms' orders on all 48 h of label rows (research/vetohold/label).

v1_frozen: trigger + gates, v1's trigger-side value >= 2 c and >= the other side, 0.2 s
refractory per market. G_h250+x: rows v1 keeps, frozen gate prediction >= -0.005, refractory.
On selection hours (before SPLIT) the gate model is in-sample (it was fit there)."""
from __future__ import annotations

import hashlib
import json
import pickle

import numpy as np
import pandas as pd

from research.vetohold.label.data import design, load, refractory, v1_pred
from research.vetohold.label.train import VM

TAU_V1 = 0.02


def orders() -> pd.DataFrame:
    from research.strategy.ingest.load import Store
    d, X = load()
    meta = json.loads((VM / "prereg.json").read_text())
    v1 = v1_pred(d)
    name = "G_h250+x"
    blob = (VM / f"{name}.pkl").read_bytes()
    assert hashlib.sha256(blob).hexdigest() == meta["variants"][name]["sha256"], name
    M, reg = design(name, X, d)
    g = np.full(len(d), -np.inf)
    g[reg] = pickle.loads(blob).predict(M[reg])
    tau_g = meta["variants"][name]["tau"]
    parts = []
    for arm, score, tau in (("v1_frozen", v1, TAU_V1), (name, g, tau_g)):
        k = refractory(d, score >= tau)
        o = d.loc[k, ["m", "t", "side", "seen", "won", "test"]].copy()
        o["arm"], o["score"], o["tau"] = arm, score[k], tau
        o["v1val"] = v1[k]
        parts.append(o)
    o = pd.concat(parts, ignore_index=True)
    o["end"] = Store().mk["end"].to_numpy()[o["m"]]
    return o.sort_values(["arm", "m", "t"]).reset_index(drop=True)
