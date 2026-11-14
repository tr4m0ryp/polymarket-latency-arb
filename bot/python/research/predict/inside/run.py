"""Score the pre-registered arms (prereg.py CONFIG) on one market set; one row per market x
arm x haircut x L x size, written to data/out/predict/inside/agg-<set>.pkl.

    nice -n 10 python3 -m research.predict.inside.run --set dublin|dry [--workers 3] [--limit N]

Sets are recordings converted by the research pipeline (btclat/paper/report/sim.py `prepare`);
the process re-executes itself with that set's cache environment. `local` (default caches,
already used for selection) exists only to check the engine against the study's mk engine."""
from __future__ import annotations

import argparse
import os
import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
OUTD = ROOT / "data" / "out" / "predict" / "inside"
SETS = {"dublin": ROOT / "data" / "paper" / "dublin-20261012",
        "dry": ROOT / "data" / "trade" / "dublin-makerdry-20261014",
        "local": None}
_st, _mdl, _cfg = None, None, None


def env_for(name: str) -> dict:
    d = SETS[name]
    if d is None:
        return dict(os.environ, BTCLAT_INSIDE_SET=name)
    return dict(os.environ, BTCLAT_INSIDE_SET=name, BTCLAT_LIVE=str(d / "raw"),
                BTCLAT_STRATEGY_CACHE=str(d / "cache" / "strategy"), BTCLAT_PREDICT_CACHE=str(d / "cache" / "predict"))


def _preds(i: int, tab: pd.DataFrame):
    from .. import CACHE
    from ..model.store import load_model, predict_sides
    global _mdl
    p = CACHE / "pred_v1_L50" / f"{i}.npz"
    if p.exists():
        with np.load(p) as z:
            return z["pu"], z["pdn"]
    _mdl = _mdl or load_model(_cfg["model"])
    pu, pdn = predict_sides(tab, _mdl)
    p.parent.mkdir(exist_ok=True)
    np.savez(p, pu=pu, pdn=pdn)
    return pu, pdn


def _one(i: int) -> pd.DataFrame:
    from ...strategy.ingest.load import Store
    from ...strategy.sim.grid import Book
    from ...strategy.sim.maker import _flow
    from ..model.data import TAB
    from ..sim import rules
    from ..sim.fills import score
    from . import engine
    global _st
    _st = _st or Store()
    m = _st.market(i)
    if m is None or m["outcome"] is None or not (TAB / f"{i}.npz").exists():
        return pd.DataFrame()
    meta = m["meta"]
    with np.load(TAB / f"{i}.npz") as z:
        tab = pd.DataFrame({k: z[k] for k in z.files if not k.startswith(("y_", "x_"))})
    if not len(tab):
        return pd.DataFrame()
    book = Book(m["ev"], meta["start"] - 2, meta["end"] + 2, m["gaps"])
    flow, o = _flow(m["tr"]), float(m["outcome"])
    pu, pdn = _preds(i, tab)
    rows = []
    for arm in _cfg["arms"]:
        fn = getattr(rules, arm["rule"])
        t, b, a = fn(tab, pu, pdn, **arm["params"])
        for hc in arm["haircut"]:
            for L in _cfg["L_ms"]:
                for size, mo in _cfg["sizes"]:
                    f, st = engine.run(book, flow, t, b, a, L / 1000, _cfg["k"], size, mo, _cfg["xhold"],
                                       seed=1000 * i + L, haircut=hc)
                    r = {"arm": arm["name"], "hc": hc, "L": L, "size": size, "m": i, "start": meta["start"],
                         **st, "n": 0, "shares": 0.0, "cost": 0.0, "mk10v": 0.0, "pnl": 0.0, "rebate": 0.0,
                         "n_src0": 0, "n_src1": 0, "n_src2": 0}
                    if f:
                        f = pd.DataFrame(f, columns=["tf", "side", "shares", "px", "src", "ton"])
                        f["t"], f["cost"], f["fee"] = f["tf"], f["shares"] * f["px"], 0.0
                        f = score(f, book, o)
                        r.update(n=len(f), shares=f["shares"].sum(), cost=f["cost"].sum(), mk10v=f["mk10v"].sum(),
                                 pnl=f["pnl"].sum(),
                                 rebate=(_cfg["rebate"] * f["px"] * (1 - f["px"]) * f["shares"]).sum(),
                                 **{f"n_src{s}": int((f["src"] == s).sum()) for s in (0, 1, 2)})
                    rows.append(r)
    return pd.DataFrame(rows)


def _init(cfg):
    global _cfg
    _cfg = cfg


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--set", required=True, choices=sorted(SETS))
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--config", default=None, help="prereg JSON (default: the frozen one)")
    a = ap.parse_args()
    if os.environ.get("BTCLAT_INSIDE_SET") != a.set:
        os.execve(sys.executable, [sys.executable, "-m", "research.predict.inside.run", *sys.argv[1:]], env_for(a.set))
    from ...strategy.ingest.load import Store
    from ..model.data import market_ids
    from .prereg import load
    cfg = load(a.config)
    st = Store()
    ids = market_ids("train,select,dev3,test3", st)
    lo = cfg["sets"].get(a.set, {}).get("start_min", 0)
    ids = [i for i in ids if st.mk.start[i] >= lo][: a.limit]
    with Pool(min(a.workers, 3), initializer=_init, initargs=(cfg,)) as pool:
        parts = [p for p in pool.imap(_one, ids, chunksize=2) if len(p)]
    OUTD.mkdir(parents=True, exist_ok=True)
    out = pd.concat(parts, ignore_index=True)
    out.to_pickle(OUTD / f"agg-{a.set}{'' if a.limit is None else '-limit'}.pkl")
    print(a.set, "markets", out["m"].nunique(), "of", len(ids))


if __name__ == "__main__":
    main()
