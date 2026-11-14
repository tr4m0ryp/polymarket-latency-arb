"""Where the frozen taker's dollars come from, by predicted race outcome (run 2 TRAIN markets
only: never evaluated, so variants designed from this table do not peek at any CV window).

Per fired order (frozen v1 3 c taker and the 2 c trigger veto, L = 0), at the venue book of
our match (strategy grid, same windows as taker.run: base J 10 ms full level, comp J 50 ms
half level): shares available at the seen price, at +1 c and at +2 c, and the 10 s markout
per share of a fill at each of those prices (mid 10 s after the match - price - fee). Rows
grouped by P_alive (clock fit E and R) and by v*.

    OMP_NUM_THREADS=1 nice -n 10 python3 -m research.predict.improve.cand.<c4 package>.diag"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .....strategy.sim.grid import Book
from ...harness import windows as W
from ...harness.guard import SafeStore
from ....report.md import md
from . import OUT, arms as A, clock

VARS = {"base": (0.010, 1.0), "comp": (0.050, 0.5)}


def orders(i: int, st: SafeStore, cl: dict) -> pd.DataFrame:
    m = st.market(i)
    meta = m["meta"]
    book = Book(m["ev"], meta["start"] - 2, meta["end"] + 2, m["gaps"])
    mk = clock.market(i)
    tab = mk.tab
    pu, pd_ = mk.pred("v1", 0)
    out = []
    for fam, margin, req in (("taker", 0.03, None), ("veto", 0.02, "trigger")):
        d = A.rules.vtaker(tab, pu, pd_, margin=margin, require=req)
        if not len(d["t"]):
            continue
        j = A.fired_rows(tab["t"].to_numpy(), d, pu, pd_)
        side = d["side"]
        vu, vd = A.vstar(tab, pu, pd_)
        pe, q, q2 = A.race(mk, j, side, "E", cl)
        pr, _, _ = A.race(mk, j, side, "R", cl)
        seen_t = np.where(side > 0, tab["pm_ba"].to_numpy()[j], 100 - tab["pm_bb"].to_numpy()[j]).astype(int)
        t = d["t"]
        g10 = book.g_ceil(t + 0.150 + 10)
        mid = book.mid(g10)
        mid = np.where(side > 0, mid, 1 - mid)
        r = {"m": i, "fam": fam, "edge": d["edge"], "vstar": np.where(side > 0, vu[j], vd[j]),
             "pE": pe, "pR": pr, "q": q, "q2": q2, "seen": seen_t / 100}
        for k in range(3):
            p = (seen_t + k) / 100
            r[f"mk_{k}"] = mid - p - 0.07 * p * (1 - p)
            col = np.where(side > 0, 100 + seen_t + k, 100 - seen_t - k)
            col = np.clip(col, 1, 199)
            for v, (J, cap) in VARS.items():
                q0, q1 = book.g_ceil(t + 0.150), book.g_ceil(t + 0.150 + J)
                r[f"a{k}_{v}"] = np.array([book.size[a:b + 1, c].min() * cap for a, b, c in zip(q0, q1, col)])
        out.append(pd.DataFrame(r))
    return pd.concat(out) if out else pd.DataFrame()


def summarize(df: pd.DataFrame, key: str, bins) -> pd.DataFrame:
    df = df.assign(b=pd.cut(df[key], bins))
    rows = []
    for (fam, b), g in df.groupby(["fam", "b"], observed=True):
        row = {"fam": fam, key: str(b), "orders": len(g), "q_seen med": g["q"].median()}
        for v in VARS:
            row[f"{v}: P(seen alive)"] = (g[f"a0_{v}"] > 0).mean()
            row[f"{v}: sh at seen"] = np.minimum(g[f"a0_{v}"], 60).mean()
            row[f"{v}: sh +1c"] = g[f"a1_{v}"].clip(0, 60).mean()
        for k in range(3):
            row[f"mk c/sh @+{k}"] = 100 * g[f"mk_{k}"].mean()
        rows.append(row)
    return pd.DataFrame(rows)


def main(reuse: bool = False) -> None:
    p = OUT / "diag-train-orders.pkl"
    if reuse and p.exists():
        df = pd.read_pickle(p)
    else:
        st, cl = SafeStore(), clock.load()
        df = pd.concat([orders(i, st, cl) for i in W.ids("train")], ignore_index=True)
        df.to_pickle(p)
    parts = []
    for key, bins in (("pE", [0, 0.3, 0.5, 0.7, 1]), ("pR", [0, 0.3, 0.5, 0.7, 1]),
                      ("vstar", [-1, 0.03, 0.05, 0.08, 1])):
        parts.append(f"## by {key}\n\n" + md(summarize(df, key, bins).round(3)))
    text = "# C4 diagnostic: train-market orders by race prediction\n\n" + "\n\n".join(parts)
    (OUT / "diag-train.md").write_text(text)
    print(text)


if __name__ == "__main__":
    import sys
    main("--reuse" in sys.argv)
