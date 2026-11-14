"""Does the touch survive the hold more often when its level is old? Level age = time since the
best ask's size last changed before our send (the tape is level-aggregated, not per order).

    PYTHONPATH=. python3 -m latency.livehold.age"""
from __future__ import annotations

import pickle

import numpy as np
import pandas as pd

from . import TAPE
from .orders import load


def main():
    o = load()
    st = pickle.loads((TAPE / "streams.pkl").read_bytes())
    rows = []
    for x in o.itertuples():
        last = {}
        for t, k, p in st.get(x.token, []):
            if t > x.t_send:
                break
            if k == "book":
                last = {px: t for px in p[1]}
            elif k == "pc" and p[0] == "SELL":
                last[p[1]] = t
        lv = [px for px in last if px <= x.seen + 1e-9]
        age = x.t_send - last[max(lv)] if lv else np.nan
        rows.append({"filled": x.filled, "age_s": age})
    d = pd.DataFrame(rows).dropna()
    d["band"] = pd.qcut(d["age_s"], 4, duplicates="drop")
    print(d.groupby("band", observed=True)["filled"].agg(["mean", "count"]).round(2))
    print("median age s: filled", d[d.filled]["age_s"].median().round(2), "missed", d[~d.filled]["age_s"].median().round(2))


if __name__ == "__main__":
    main()
