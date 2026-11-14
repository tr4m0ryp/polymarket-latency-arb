"""Run baseline and prediction arms through the strategy replay simulator on chosen markets.

    nice -n 10 python3 -m research.predict.sim.run --arms <module> --tag <name>
        --seg select [--L=-40,0,50] [--workers 3] [--J 0.01] [--cap 1.0]

`<module>` under research/predict/sim/arms/ exposes ARMS: dicts with kind
  base   : a strategy arm dict (`arm`), decided on the strategy v2 feature table,
  basemaker: a strategy maker arm (sim/maker.py through eval/sim.py _maker),
  vtaker : value-model taker (sim/rules.py), params + `model` (name; `_L{L}` appended),
  vmaker : value-model maker.
Fills use the strategy taker / maker simulators unchanged (150 ms hold, venue stamps,
survival-window competition). Writes data/out/predict/agg-<tag>.pkl (+ fills-<tag>.pkl)."""
from __future__ import annotations

import argparse
import importlib
from multiprocessing import Pool

import numpy as np
import pandas as pd

from .. import OUT
from ...strategy.eval import sim as ssim
from ...strategy.eval.prep import FEAT2
from ...strategy.ingest.load import Store
from ...strategy.sim import maker, taker
from ...strategy.sim.grid import Book
from ..model.data import TAB, market_ids
from ..model.store import load_model, predict_sides
from . import rules
from .fills import aggregate, score

_st, _cfg, _mdl = None, None, {}


def _model(name):
    if name not in _mdl:
        _mdl[name] = load_model(name)
    return _mdl[name]


def _taker_fills(book, d, L):
    fills, skipped = taker.run(book, d["t"], d["side"], d["shares"], d["limit"], L / 1000,
                               _cfg["J"], _cfg["cap"], _cfg["hold"])
    return pd.DataFrame(fills) if fills else pd.DataFrame()


def _one(i: int):
    global _st
    _st = _st or Store()
    m = _st.market(i)
    meta = m["meta"]
    book = Book(m["ev"], meta["start"] - 2, meta["end"] + 2, m["gaps"])
    o = float(m["outcome"])
    with np.load(TAB / f"{i}.npz") as z:
        tab = pd.DataFrame({k: z[k] for k in z.files})
    p2 = FEAT2 / f"{i}.pkl"
    f2 = pd.read_pickle(p2) if p2.exists() else None
    preds, out, keep, dec = {}, [], [], []
    for arm in _cfg["arms"]:
        for L in _cfg["L"]:
            d = None
            if arm["kind"] == "basemaker":
                f = ssim._maker(book, m, f2, arm["arm"], L / 1000) if f2 is not None and len(f2) else pd.DataFrame()
            elif arm["kind"] == "base":
                if f2 is None or not len(f2):
                    continue
                d = ssim.decisions(f2, arm["arm"])
                f = _taker_fills(book, d, L) if len(d["t"]) else pd.DataFrame()
            else:
                key = f"{arm['model']}_L{L}" if arm.get("per_L", True) else arm["model"]
                if key not in preds:
                    preds[key] = predict_sides(tab, _model(key), arm.get("perp_trades", False))
                pu, pdn = preds[key]
                if arm["kind"] == "vtaker":
                    d = rules.vtaker(tab, pu, pdn, **arm["params"])
                    f = _taker_fills(book, d, L) if len(d["t"]) else pd.DataFrame()
                else:
                    t, b, a = rules.vmaker(tab, pu, pdn, **arm["params"])
                    r = maker.run(book, m["tr"], t, b, a, L / 1000, arm.get("size", 60.0),
                                  arm.get("max_open", 300.0), _cfg["hold"])
                    f = pd.DataFrame(r, columns=["tf", "side", "shares", "px"]) if r else pd.DataFrame()
                    if len(f):
                        f["t"], f["cost"], f["fee"] = f["tf"], f["shares"] * f["px"], 0.0
            if d is not None:  # taker decisions, for the fill rate
                dec.append({"arm": arm["name"], "L": L, "m": i, "ndec": len(d["t"])})
            if not len(f):
                continue
            f["arm"], f["L"], f["m"], f["end"] = arm["name"], L, i, meta["end"]
            f = score(f, book, o)
            out.append(aggregate(f))
            keep.append(f[["arm", "L", "m", "t", "tf", "side", "shares", "cost", "fee", "px", "won",
                           "pnl", "mk3v", "mk10v"]])
    cat = lambda x: pd.concat(x, ignore_index=True) if x else pd.DataFrame()  # noqa: E731
    return cat(out), cat(keep), pd.DataFrame(dec)


def _init(cfg):
    global _cfg
    _cfg = cfg
    ssim._init({"xhold": cfg["hold"]})


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--arms", required=True)
    ap.add_argument("--tag", required=True)
    ap.add_argument("--seg", default="select")
    ap.add_argument("--L", default="-40,0,50")
    ap.add_argument("--J", type=float, default=0.010)
    ap.add_argument("--cap", type=float, default=1.0)
    ap.add_argument("--hold", type=float, default=0.150)
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--exclude", default=None, help="skip the markets of an earlier tag (extension runs)")
    a = ap.parse_args()
    mod = importlib.import_module(f"research.predict.sim.arms.{a.arms}")
    cfg = {"arms": mod.ARMS, "L": [int(x) for x in a.L.split(",")], "J": a.J, "cap": a.cap,
           "hold": a.hold}
    st = Store()
    ids = market_ids(a.seg, st)
    if a.exclude:
        done = set(pd.read_csv(OUT / f"markets-{a.exclude}.csv")["m"])
        ids = [i for i in ids if i not in done]
    aggs, fills, decs = [], [], []
    with Pool(a.workers, initializer=_init, initargs=(cfg,)) as pool:
        for ag, fl, dc in pool.imap(_one, ids, chunksize=4):
            aggs.append(ag)
            fills.append(fl)
            decs.append(dc)
    OUT.mkdir(parents=True, exist_ok=True)
    for name, parts in (("agg", aggs), ("fills", fills), ("dec", decs)):
        parts = [p for p in parts if len(p)]
        if parts:
            pd.concat(parts, ignore_index=True).to_pickle(OUT / f"{name}-{a.tag}.pkl")
    pd.DataFrame({"m": ids, "start": st.mk.start[ids].to_numpy()}).to_csv(OUT / f"markets-{a.tag}.csv", index=False)
    print("markets", len(ids))


if __name__ == "__main__":
    main()
