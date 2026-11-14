"""Fit the fair-value models (signals/fair.py) on the training markets of run 2 only.

    nice -n 10 python3 -m research.strategy.eval.fit [--micro]

--micro fits on the v2 tables (microprice candidates): pz2 (same inputs as pz, refit) and
pzm (+ perp and spot microprice lag buckets). Writes data/out/strategy/fair-<name>.json and
prints in-sample / held-out calibration (mean realized vs predicted 3 s price change by
bucket of the prediction)."""
from __future__ import annotations

import sys

import numpy as np
import pandas as pd
from scipy.special import ndtr

from .. import OUT
from ..ingest.load import Store
from ..signals.fair import Fair
from ..signals.features import z
from .prep import FEAT, FEAT2, RUN2, split, usable

MODELS = {"pz": (("perp", "smid"), False, False), "pzx": (("perp", "smid"), True, False),
          "p": (("perp",), False, False), "s": (("smid",), False, False),
          "pzi": (("perp", "smid"), False, True), "pzxi": (("perp", "smid"), True, True)}
MODELS2 = {"pz2": (("perp", "smid"), False, False),
           "pzm": (("perp", "smid", "pmic", "smic"), False, False)}
EDGES = [-1, -0.08, -0.05, -0.03, -0.015, 0.015, 0.03, 0.05, 0.08, 1]


def frames(feat=FEAT):
    st = Store()
    sp = split(st.mk)
    tr, te = [], []
    for i in usable(st):
        p = feat / f"{i}.pkl"
        if not p.exists() or st.mk.start[i] < RUN2:
            continue
        d = pd.read_pickle(p)
        if len(d):
            d = d[np.isfinite(d["y"]) & d["mid"].between(0.05, 0.95)]
            (tr if sp[i] == "train" else te).append(d)
    return pd.concat(tr), pd.concat(te)


def calib(f: Fair, df: pd.DataFrame) -> pd.DataFrame:
    dp = ndtr(z(df["mid"].to_numpy(float)) + f.dz(df)) - df["mid"].to_numpy(float)
    real = (df["mid_h"] - df["mid"]).to_numpy(float)
    q = pd.cut(dp, EDGES)
    return (pd.DataFrame({"q": q, "pred": dp, "real": real}).groupby("q", observed=True)
            .agg(n=("pred", "size"), pred=("pred", "mean"), real=("real", "mean")).round(4))


def main() -> None:
    micro = "--micro" in sys.argv
    tr, te = frames(FEAT2 if micro else FEAT)
    print("rows train", len(tr), "test", len(te))
    OUT.mkdir(parents=True, exist_ok=True)
    lines = []
    for name, (srcs, extra, imb) in (MODELS2 if micro else MODELS).items():
        f = Fair(srcs, extra, imb=imb).fit(tr)
        f.save(OUT / f"fair-{name}.json")
        lines.append(f"## fair-{name} (srcs {srcs}, extra {extra}, imb {imb}), train r2 {f.r2:.3f}")
        lines.append("train calibration\n" + calib(f, tr).to_string())
        lines.append("held-out calibration (diagnostic only, not used for any choice)\n"
                     + calib(f, te).to_string())
    (OUT / f"fair-calibration{'-v2' if micro else ''}.txt").write_text("\n\n".join(lines) + "\n")
    print("\n\n".join(lines))


if __name__ == "__main__":
    main()
