"""C1 live-parity probe: per-decision fills of the frozen arms and the C1 picks at L = 0, split
by the offline 5 ms grid quirk (btclat/paper/replay/compare.grid_quirk), under three fill models
(base, comp, harsh = 50 ms window, a quarter of each level), plus quirk-neutral C1 (60 sh on
quirk rows).  Allowed windows only; asserts max(start) < SEALED.

    OMP_NUM_THREADS=1 nice -n 10 python3 -m research.predict.improve.cand.c1_refute.probe"""
from __future__ import annotations

from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd

from ....sim import rules
from ....sim.fills import score
from .....strategy.sim import taker
from .....strategy.sim.grid import Book
from ...harness import windows as W
from ...harness.api import Market
from ...harness.guard import SEALED, SafeStore, assert_allowed
from ..c1_conviction_keyed_size_value_keyed_size_on_the_identity_projected_value_with_a_low_delta_busy_cap.arms import (
    taker_arm, veto_arm)
from btclat.paper.replay.compare import grid_quirk

OUT = Path("data/out/predict/improve/c1-size/refute")
FILLM = {"base": (0.010, 1.0), "comp": (0.050, 0.5), "harsh": (0.050, 0.25)}
ARMS = {"vt_any": ("t", None), "ek_pred_2000": ("t", taker_arm(2000, "pred").decide),
        "veto": ("v", None), "vk_vstar_4000_d6": ("v", veto_arm(4000, "vstar", cap=6).decide)}
_ST = None


def _one(i):
    global _ST
    _ST = _ST or SafeStore()
    m = _ST.market(i)
    meta = m["meta"]
    assert float(meta["start"]) < SEALED
    book = Book(m["ev"], meta["start"] - 2, meta["end"] + 2, m["gaps"])
    mk = Market(i, meta)
    pu, pd_ = mk.pred("v1", 0)
    out = []
    for name, (fam, fn) in ARMS.items():
        if fn is None:
            d = rules.vtaker(mk.tab, pu, pd_, margin=.03 if fam == "t" else .02,
                             require=None if fam == "t" else "trigger")
        else:
            d = fn(mk, 0)
        if not len(d["t"]):
            continue
        q = grid_quirk(np.asarray(d["t"], float), meta["start"])
        variants = {name: d["shares"]}
        if fn is not None:
            variants[name + "_qn"] = np.where(q, 60.0, d["shares"])
        for vn, sh in variants.items():
            for fm, (J, cap) in FILLM.items():
                fl, _ = taker.run(book, d["t"], d["side"], sh, d["limit"], 0.0, J, cap, 0.150)
                if not fl:
                    continue
                f = score(pd.DataFrame(fl), book, float(m["outcome"]))
                f["quirk"] = q[f["i"].to_numpy()]
                f["ordered"] = np.asarray(sh)[f["i"].to_numpy()]
                f["arm"], f["fm"], f["m"] = vn, fm, i
                out.append(f[["arm", "fm", "m", "i", "quirk", "ordered", "shares", "cost", "fee", "mk10v"]])
    return pd.concat(out, ignore_index=True) if out else pd.DataFrame()


def main():
    ids = W.all_eval_ids()
    st = pd.Series({i: s for w in W.WINDOWS for i, s in W.starts(w).items()})
    assert_allowed(st.values, "c1 refute")
    assert st.max() < SEALED
    with Pool(2) as p:
        parts = list(p.imap_unordered(_one, ids, chunksize=4))
    OUT.mkdir(parents=True, exist_ok=True)
    f = pd.concat([x for x in parts if len(x)], ignore_index=True)
    f.to_pickle(OUT / "fills.pkl")
    print("fills", len(f), "markets", f["m"].nunique(), "max start", st.max())


if __name__ == "__main__":
    main()
