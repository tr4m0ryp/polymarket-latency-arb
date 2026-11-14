"""Save / load fitted value models (data/out/predict/models/, gitignored) and score both
sides of a decision table with one."""
from __future__ import annotations

import pickle

import numpy as np
import pandas as pd

from .. import OUT
from .data import features
from .derive import add_derived
from .learners import clean
from .orient import orient

MODELS = OUT / "models"


def save(name: str, model, vf: list[str], meta: dict) -> None:
    MODELS.mkdir(parents=True, exist_ok=True)
    with open(MODELS / f"{name}.pkl", "wb") as fh:
        pickle.dump({"model": model, "vf": vf, "meta": meta}, fh)


def load_model(name: str) -> dict:
    with open(MODELS / f"{name}.pkl", "rb") as fh:
        return pickle.load(fh)


def predict_sides(df: pd.DataFrame, mdl: dict, perp_trades: bool = False) -> tuple[np.ndarray, np.ndarray]:
    d = add_derived(df.copy())
    feats = features(d, perp_trades)
    out = []
    for side in (1, -1):
        o = orient(d, feats, side)
        for c in mdl["vf"]:
            if c not in o:
                o[c] = 0.0
        out.append(mdl["model"].predict(clean(o[mdl["vf"]].to_numpy())))
    return out[0], out[1]
