"""Load a frozen value model, refusing to run on a hash mismatch, and score both sides of a
decision with the C tree scorer (research/predict/infer/ctree.py).

The expected hashes are the pre-registration's (data/out/predict/prereg2.json
`models_sha256_16`: first 16 hex of the file's sha256). The pickle is never written."""
from __future__ import annotations

import hashlib
import json
import pickle
import time

from research.predict import OUT as POUT
from research.predict.infer.ctree import CTree

from .vector import Vectorizer

MODELS = POUT / "models"
PREREG = POUT / "prereg2.json"


class ModelMismatch(SystemExit):
    pass


def sha16(path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:16]


class ValueModel:
    """name e.g. 'v1_L0'. `__call__(row)` -> (pred_up, pred_down) in $ per share."""

    def __init__(self, name: str = "v1_L0"):
        path = MODELS / f"{name}.pkl"
        want = json.loads(PREREG.read_text())["models_sha256_16"].get(path.name)
        got = sha16(path)
        if want is None or got != want:
            raise ModelMismatch(f"model {path.name}: sha256[:16] {got} != pre-registered {want}; refusing to run")
        with open(path, "rb") as fh:
            d = pickle.load(fh)
        self.name, self.sha16, self.meta = name, got, d["meta"]
        self.vec = Vectorizer(d["vf"])
        t0 = time.perf_counter()
        self.tree = CTree(d["model"])
        self.compile_s = time.perf_counter() - t0
        self.sk = d["model"]   # kept only for the parity test; never refit

    def __call__(self, row: dict) -> tuple[float, float]:
        xu, xd = self.vec.sides(row)
        return self.tree(xu), self.tree(xd)
