"""Timing structure of rival takers: venue print stamps modulo 100 ms (a cadence would mean a
rival population keyed to a 100 ms clock, or batched matching), and our simulated orders'
outcomes by the phase of their match time in that cycle (does landing just before / after
the cluster change fills, rival prints or markout?).

    python3 -m research.predict.improve.diag.competition.report.cadence"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .....report.md import md
from .. import OUT, SEALED
from ..data.safe import SafeStore, market_ids
from .boot import load, markets


def print_phase(wins=("dev3", "final", "ext"), every: int = 3) -> pd.DataFrame:
    st, ids, rows = SafeStore(), market_ids(wins), []
    for w in wins:
        ts = []
        for i in ids[w][::every]:
            assert st.mk.start[i] < SEALED
            m = st.market(i)
            if m and len(m["tr"].get("ts", [])):
                ts.append(np.unique(np.round(m["tr"]["ts"] * 1000).astype(np.int64)))
        ts = np.concatenate(ts)
        h = np.bincount(ts % 100, minlength=100).reshape(10, 10).sum(1)
        rows.append({"window": w, "distinct print ms": len(ts),
                     **{f"{10 * k}-{10 * k + 9}": round(h[k] / h.mean(), 2) for k in range(10)}})
    return pd.DataFrame(rows)


def order_phase(o: pd.DataFrame, ids: dict, group: str = "unseen") -> pd.DataFrame:
    a = o[o["m"].isin(markets(ids, group))].copy()
    a["ph"] = ((a["t"] + a["L"] / 1000 + 0.150) * 1000 % 100 // 10 * 10).astype(int)
    a["fill"] = a["base_got"] > 0
    r = a.groupby("ph").agg(orders=("fill", "size"), fill_rate=("fill", "mean"),
                            rival_after25=("aft25", lambda x: (x > 0).mean()), got=("base_got", "sum"),
                            mk=("base_mk10v", "sum"), cost=("base_cost", "sum"), tr50=("tr50", "sum"),
                            e25=("e+25_mk10v", "sum"))
    r["mk10 c/$"] = 100 * r["mk"] / r["cost"]
    r["taken <= 50 ms"] = r["tr50"] / r["got"]
    r["e+25 keeps"] = r["e25"] / r["mk"]
    return r[["orders", "fill_rate", "rival_after25", "taken <= 50 ms", "mk10 c/$", "e+25 keeps"]].reset_index()


def main() -> None:
    pp = print_phase()
    o, ids = load()
    op = order_phase(o, ids)
    txt = ("# Rival timing cadence\n\n## Distinct print ms, phase within 100 ms (count / mean)\n\n" + md(pp, 2)
           + "\n\n## Our orders (all arms, L 0 / -40, unseen) by match-time phase (ms within 100)\n\n" + md(op, 3))
    (OUT / "diag-competition-cadence.md").write_text(txt)
    print(txt)


if __name__ == "__main__":
    main()
