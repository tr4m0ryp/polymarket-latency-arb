"""Score both sides of every decision-table row with a refit variant (the analogue of
model.store.predict_sides with the adaptive-gain inputs), for the simulator arms."""
from __future__ import annotations

import numpy as np
import pandas as pd

from ......predict.model.data import features
from ......predict.model.derive import add_derived
from ......predict.model.orient import orient
from ......strategy import fee
from .feats import add_gain, orient_gain
from .train import predict_rows


def predict_sides(tab: pd.DataFrame, c: dict, mdl: dict) -> tuple[np.ndarray, np.ndarray]:
    d = add_derived(tab.copy())
    gain = add_gain(d, c)
    feats = [f for f in features(d) if f not in gain]
    out = []
    for side in (1, -1):
        o = orient(d, feats, side)
        o = pd.concat([o, orient_gain(d, gain, side)], axis=1)
        o["fee_seen"] = fee(o["seen"].to_numpy(float))
        out.append(predict_rows(mdl, o))
    return out[0], out[1]
