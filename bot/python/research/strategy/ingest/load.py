"""Per-market access to the converted hours (ingest/run.py): book events and trades of one
5m market plus the Binance spot and perp streams around it.

    from research.strategy.ingest.load import Store
    st = Store(); m = st.market(i)   # dict: meta, ev, tr, spot_tr, spot_bk, perp"""
from __future__ import annotations

import json
from collections import OrderedDict

import numpy as np
import pandas as pd

from .. import CACHE
from .markets import gaps


class Store:
    def __init__(self, keep: int = 4):
        self.mk = pd.read_csv(CACHE / "markets.csv", dtype={"up": str, "down": str})
        p = CACHE / "outcomes.json"
        self.outcome = json.loads(p.read_text()) if p.exists() else {}
        self.gaps = gaps()
        self.keep, self._hours = keep, OrderedDict()
        self.have = {int(p.stem.split("-")[1]) for p in CACHE.glob("hour-*.npz") if "tmp" not in p.name}

    def _hour(self, h: int) -> dict | None:
        if h not in self.have:
            return None
        if h not in self._hours:
            with np.load(CACHE / f"hour-{h}.npz") as z:
                self._hours[h] = {k: z[k] for k in z.files}
            while len(self._hours) > self.keep:
                self._hours.popitem(last=False)
        self._hours.move_to_end(h)
        return self._hours[h]

    def _cat(self, hs, prefix: str, sel=None) -> dict:
        parts = []
        for h in hs:
            d = self._hour(h)
            if d is None or f"{prefix}_t" not in d:
                continue
            cols = {k[len(prefix) + 1:]: v for k, v in d.items() if k.startswith(prefix + "_")}
            if sel is not None:
                w = sel(cols)
                cols = {k: v[w] for k, v in cols.items()}
            parts.append(cols)
        if not parts:
            return {}
        out = {k: np.concatenate([p[k] for p in parts]) for k in parts[0]}
        o = np.argsort(out["t"], kind="stable")
        return {k: v[o] for k, v in out.items()}

    def market(self, i: int, pre: float = 420.0) -> dict | None:
        m = self.mk.iloc[i].to_dict()
        hs = range(int(m["start"] - 95) // 3600, int(m["end"] + 35) // 3600 + 1)
        ev = self._cat(hs, "ev", lambda c: c["m"] == i)
        tr = self._cat(hs, "tr", lambda c: c["m"] == i)
        if not ev:
            return None
        bh = range(int(m["start"] - pre) // 3600, int(m["end"] + 35) // 3600 + 1)
        win = lambda c: (c["t"] > m["start"] - pre) & (c["t"] < m["end"] + 35)  # noqa: E731
        return {"meta": m, "outcome": self.outcome.get(m["slug"]), "ev": ev, "tr": tr,
                "gaps": self.gaps.get(m["slug"], []),
                "spot_tr": self._cat(bh, "st", win), "spot_bk": self._cat(bh, "sb", win),
                "perp": self._cat(bh, "fb", win)}
