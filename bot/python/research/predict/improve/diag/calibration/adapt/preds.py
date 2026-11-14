"""Predictions of the refit variants on every gated (decision, side) row of the allowed
windows, aligned with the calibration row caches (rows-<win>.pkl: m, row, side).

    OMP_NUM_THREADS=1 nice -n 10 python3 -m research.predict.improve.diag.calibration.adapt.preds [--workers 2]

Writes CACHE/adapt-preds-<win>.pkl: m, row, side, p_<var>_L<L> (float32) for every variant
model found under CACHE/models/."""
from __future__ import annotations

import argparse
import pickle
import time
from multiprocessing import Pool

import numpy as np
import pandas as pd

from .. import CACHE, WINDOWS
from ..safe import check, market_ids, start_of
from . import MODELS
from .data import market_frame
from .train import predict_rows

_M: dict = {}
_ONLY: list[str] | None = None


def _load() -> dict:
    out = {}
    for p in sorted(MODELS.glob("*_L*.pkl")):
        if _ONLY is None or p.stem.rsplit("_L", 1)[0] in _ONLY:
            with open(p, "rb") as fh:
                out[p.stem] = pickle.load(fh)
    return out


def one(i: int) -> pd.DataFrame:
    global _M
    _M = _M or _load()
    st, _, _ = market_frame(i, ks=(1,))
    out = st[["m", "row", "side"]].copy()
    for name, mdl in _M.items():
        out[f"p_{name}"] = predict_rows(mdl, st).astype(np.float32)
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--win", default=",".join(WINDOWS))
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--only", default=None, help="variants to (re)predict, merged into the existing file")
    a = ap.parse_args()
    global _ONLY
    _ONLY = a.only.split(",") if a.only else None
    for w in a.win.split(","):
        ids = market_ids(w)
        check(start_of(ids))
        t0 = time.time()
        with Pool(min(a.workers, 2)) as pool:
            parts = pool.map(one, ids, chunksize=4)
        new, dst = pd.concat(parts, ignore_index=True), CACHE / f"adapt-preds-{w}.pkl"
        if _ONLY and dst.exists():
            old = pd.read_pickle(dst)
            old = old.drop(columns=[c for c in new.columns if c.startswith("p_") and c in old])
            new = old.merge(new, on=["m", "row", "side"], how="left", validate="one_to_one")
        new.to_pickle(dst)
        print(w, len(ids), f"{time.time() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
