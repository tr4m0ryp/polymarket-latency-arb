"""Hypothesis 1 of the competition diagnostic: a race-aware value label. Same learner, rows and
features as the frozen v1_L0 (train hours, frac 0.5, seed 1, k = 1, 200 x 15 leaves, min leaf
200), but the target is the per-share value if our match lands anywhere in [+0, +50 ms]:
  rmin = min(v1 at L = 0, v1 at L = 50)   (we lose every race inside 50 ms)
  ravg = mean of the two                  (a coin flip on those races)
Control: the same code fitted on the frozen target (v1 at L = 0, the frozen row set) must
reproduce the frozen v1_L0 predictions, so the label is the only change.
Models go to data/out/predict/improve/models/ (the frozen models are never touched).

    OMP_NUM_THREADS=2 nice -n 10 python3 -m research.predict.improve.diag.competition.race.label"""
from __future__ import annotations

import os
import pickle
import time

import numpy as np
import pandas as pd

from ...... import predict
from .....model.data import TAB
from .....model.learners import clean, gbdt_reg
from .....model.stack import stacked
from .....model.store import load_model
from .. import OUT, SEALED
from ..data.safe import SafeStore

MODELS = OUT / "models"


def train_frame(frac: float = 0.5, seed: int = 1) -> pd.DataFrame:
    """predict.model.data.load('train') without globbing the table directory."""
    st = SafeStore()
    mk = st.mk
    ids = [int(i) for i in mk.index[(mk.start >= predict.RUN2) & (mk.start < predict.SPLIT)]
           if (TAB / f"{int(i)}.npz").exists()]
    assert max(mk.start[ids]) < SEALED
    rng, parts = np.random.default_rng(seed), []
    for i in sorted(ids):
        with np.load(TAB / f"{i}.npz") as z:
            d = {k: z[k] for k in z.files}
        n = len(next(iter(d.values())))
        w = rng.random(n) < frac
        df = pd.DataFrame({k: v[w] for k, v in d.items()})
        df["m"] = i
        parts.append(df)
    return pd.concat(parts, ignore_index=True)


def _fit(X, y):
    return gbdt_reg(max_iter=200, leaves=15, lr=0.05, min_leaf=200).fit(X, np.clip(y, -0.3, 0.3))


def main() -> None:
    os.environ.setdefault("OMP_NUM_THREADS", "2")
    tr, vf = stacked(train_frame())
    v0, v50 = tr["v1_0"].to_numpy(float), tr["v1_50"].to_numpy(float)
    b0, b50 = (tr["bad0"] == 0).to_numpy(), (tr["bad50"] == 0).to_numpy()
    X = clean(tr[vf].to_numpy())
    MODELS.mkdir(parents=True, exist_ok=True)
    w0 = np.isfinite(v0) & b0
    t0 = time.time()
    ctl = _fit(X[w0], v0[w0])
    ref = load_model("v1_L0")
    assert ref["vf"] == vf, "feature list differs from the frozen v1_L0"
    k = np.random.default_rng(0).choice(len(X), 200_000, replace=False)
    dmax = float(np.abs(ctl.predict(X[k]) - ref["model"].predict(X[k])).max())
    print(f"control v1_L0 refit: rows {int(w0.sum())} (frozen {ref['meta'].get('rows')}), "
          f"max |pred - frozen| = {dmax:.2e}, {time.time() - t0:.0f}s", flush=True)
    ok = np.isfinite(v0) & np.isfinite(v50) & b0 & b50
    for name, y in (("v1rmin", np.minimum(v0, v50)), ("v1ravg", 0.5 * (v0 + v50))):
        t0 = time.time()
        m = _fit(X[ok], y[ok])
        with open(MODELS / f"{name}_L0.pkl", "wb") as fh:
            pickle.dump({"model": m, "vf": vf, "meta": {"name": name, "rows": int(ok.sum()),
                                                        "target": name, "base": "v1_L0 config",
                                                        "control_max_diff": dmax}}, fh)
        print(name, int(ok.sum()), f"{time.time() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
