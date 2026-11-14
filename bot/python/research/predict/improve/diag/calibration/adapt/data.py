"""Side-stacked frames with the frozen v1 inputs plus the adaptive-gain inputs.

`frame(df, c)`: one market's (or several markets') decision rows -> model.stack.stacked output
(v1 inputs, targets, side) with the oriented gain columns appended in the same row order.
`load_train()`: run 2 train rows sampled exactly as the frozen v1 fit (model.data.load:
sorted market ids, frac 0.5, seed 1, one draw per row), with their ctx rows."""
from __future__ import annotations

import numpy as np
import pandas as pd

from ......predict.model.data import TAB
from ......predict.model.stack import gate, stacked
from ......strategy import fee
from ..ctx.load import ctx
from ..safe import check, market_ids, start_of
from .feats import add_gain, orient_gain


def frame(df: pd.DataFrame, c: dict, ks=(1, 3, 10)) -> tuple[pd.DataFrame, list[str], list[str]]:
    g = gate(df).to_numpy()
    st, vf = stacked(df, ks=ks)
    dg = df.loc[g].copy()
    gain = add_gain(dg, {k: v[g] for k, v in c.items()})
    o = pd.concat([orient_gain(dg, gain, 1), orient_gain(dg, gain, -1)], ignore_index=True)
    st = pd.concat([st, o.set_index(st.index)], axis=1)
    st["fee_seen"] = fee(st["seen"].to_numpy(float)).astype(np.float32)
    return st, vf, gain


def load_train(frac: float = 0.5, seed: int = 1, ks=(1,)) -> tuple[pd.DataFrame, list[str], list[str]]:
    """Concatenate first, then stack once: the same row order as the frozen v1 fit, so the
    v1r control reproduces v1 (early-stopping split and binning depend on row order)."""
    ids = sorted(market_ids("train"))
    check(start_of(ids))
    rng = np.random.default_rng(seed)
    dfs, cs = [], []
    for i in ids:
        with np.load(TAB / f"{i}.npz") as z:
            d = {k: z[k] for k in z.files}
        n = len(next(iter(d.values())))
        w = rng.random(n) < frac if frac < 1 else np.ones(n, bool)
        df = pd.DataFrame({k: v[w] for k, v in d.items()})
        df["m"] = i
        dfs.append(df)
        cs.append({k: v[w] for k, v in ctx(i, n).items()})
    df = pd.concat(dfs, ignore_index=True)
    del dfs
    c = {k: np.concatenate([x[k] for x in cs]) for k in cs[0]}
    st, vf, gain = frame(df, c, ks)
    keep = [x for x in st.columns if not x.startswith(("v3_", "v10_", "post1_"))]
    return st[keep], vf, gain


def market_frame(i: int, ks=(1, 3, 10)) -> tuple[pd.DataFrame, list[str], list[str]]:
    with np.load(TAB / f"{i}.npz") as z:
        df = pd.DataFrame({k: z[k] for k in z.files})
    df["m"] = i
    return frame(df, ctx(i, len(df)), ks)
