"""Replay paper simulator: every arm x latency on every usable market.

    nice -n 10 python3 -m research.strategy.eval.sim --arms <module> --tag <name>
        [--L 25,50,100,150,200] [--J 0.01] [--cap 1.0] [--hold 0.15] [--xhold <hold>]
        [--split train|test|all] [--workers 2] [--micro]

L = our receipt of the Binance message to our order at the CLOB (Paris receipt is ~112 ms
after the Binance event, so a Dublin host is L ~ 0-10 ms and the split Tokyo build ~ -40 ms).

`<module>` names a module under research/strategy/eval/arms/ exposing ARMS (list of dicts
name/kind/params). Writes data/out/strategy/agg-<tag>.pkl (one row per arm x L x market:
fills, wins, cost, fee, pnl, 3 s markout value) and, for arms with keep=True,
fills-<tag>.pkl (one row per fill with the decision's features)."""
from __future__ import annotations

import argparse
import importlib
from multiprocessing import Pool

import numpy as np
import pandas as pd

from .. import OUT
from ..ingest.load import Store
from ..sim import maker, taker
from ..sim.grid import Book
from ..signals import rules
from ..signals.fair import Fair
from . import prep
from .prep import split, usable

_st, _cfg, _models = None, None, {}


def _model(name: str) -> Fair:
    if name not in _models:
        _models[name] = Fair.load(OUT / f"fair-{name}.json")
    return _models[name]


def _maker(book, m: dict, df: pd.DataFrame, arm: dict, L: float) -> pd.DataFrame:
    p = dict(arm["params"])
    size, max_open = p.pop("size", 60.0), p.pop("max_open", 300.0)
    fn = rules.quotes_book if p.pop("anchor", "fair") == "book" else rules.quotes
    t, b, a = fn(df, _model(p.pop("model")).p(df), **p)
    out = maker.run(book, m["tr"], t, b, a, L, size, max_open, _cfg["xhold"])
    if not out:
        return pd.DataFrame()
    f = pd.DataFrame(out, columns=["tf", "side", "shares", "px"])
    f["t"], f["cost"], f["fee"], f["i"] = f["tf"], f["shares"] * f["px"], 0.0, -1
    return f


def decisions(df: pd.DataFrame, arm: dict) -> dict:
    p = dict(arm["params"])
    if arm["kind"] == "momentum":
        return rules.momentum(df, **p)
    if arm["kind"] == "fair":
        return rules.fair(df, _model(p.pop("model")).p(df), **p)
    if arm["kind"] == "micro":
        name = p.pop("model", None)
        return rules.micro(df, p_fair=_model(name).p(df) if name else None, **p)
    raise ValueError(arm["kind"])


AGG = dict(n=("shares", "size"), won_n=("won", "sum"), shares=("shares", "sum"),
           cost=("cost", "sum"), fee=("fee", "sum"), pnl=("pnl", "sum"), mk3v=("mk3v", "sum"),
           mk10v=("mk10v", "sum"))


def _one(i: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    global _st
    _st = _st or Store()
    df = pd.read_pickle(_cfg["feat"] / f"{i}.pkl")
    if not len(df):
        return pd.DataFrame(), pd.DataFrame()
    m = _st.market(i)
    meta = m["meta"]
    book = Book(m["ev"], meta["start"] - 2, meta["end"] + 2, m["gaps"])
    o = float(m["outcome"])
    out, keep = [], []
    for arm in _cfg["arms"]:
        if arm.get("needs") == "perp" and not np.isfinite(df["perp_r1"]).any():
            continue
        is_maker = arm["kind"] == "maker"
        d = None if is_maker else decisions(df, arm)
        if d is not None and not len(d["t"]):
            continue
        for L in _cfg["L"]:
            if is_maker:
                f = _maker(book, m, df, arm, L / 1000)
                if not len(f):
                    continue
                f["secs_left"] = meta["end"] - f["tf"]
            else:
                fills, skipped = taker.run(book, d["t"], d["side"], d["shares"], d["limit"],
                                           L / 1000, _cfg["J"], _cfg["cap"], _cfg["hold"])
                if not fills:
                    continue
                f = pd.DataFrame(fills)
                f["n_dec"], f["skipped"] = len(d["t"]), skipped
                f["edge_est"] = d["edge"][f["i"].to_numpy()]
                row = df.iloc[d["idx"][f["i"].to_numpy()]]
                for c in ("secs_left", "mid", "spot_r3", "perp_r1", "perp_r3"):
                    f[c] = row[c].to_numpy()
            f["arm"], f["L"], f["m"], f["end"] = arm["name"], L, i, meta["end"]
            won = np.where(f["side"] > 0, o, 1 - o)
            f["won"] = won
            f["pnl"] = f["shares"] * won - f["cost"] - f["fee"]
            for h in (3, 10):
                mid = book.mid(book.g_ceil(f["tf"].to_numpy() + h))
                f[f"mk{h}"] = np.where(f["side"] > 0, mid, 1 - mid)
            for h in (3, 10):
                f[f"mk{h}v"] = f["shares"] * f[f"mk{h}"].fillna(f["won"]) - f["cost"] - f["fee"]
            out.append(f.groupby(["arm", "L", "m", "end"]).agg(**AGG).reset_index())
            if arm.get("keep"):
                keep.append(f)
    cat = lambda x: pd.concat(x, ignore_index=True) if x else pd.DataFrame()  # noqa: E731
    return cat(out), cat(keep)


def _init(cfg):
    global _cfg
    _cfg = cfg


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--arms", required=True)
    ap.add_argument("--tag", required=True)
    ap.add_argument("--L", default="25,50,100,150,200")
    ap.add_argument("--J", type=float, default=0.010)
    ap.add_argument("--cap", type=float, default=1.0)
    ap.add_argument("--hold", type=float, default=0.150)
    ap.add_argument("--xhold", type=float, default=None)
    ap.add_argument("--split", default="all")
    ap.add_argument("--micro", action="store_true", help="use the v2 (microprice) feature tables")
    ap.add_argument("--workers", type=int, default=2)
    a = ap.parse_args()
    mod = importlib.import_module(f"research.strategy.eval.arms.{a.arms}")
    cfg = {"arms": mod.ARMS, "L": [int(x) for x in a.L.split(",")], "J": a.J, "cap": a.cap,
           "hold": a.hold, "xhold": a.hold if a.xhold is None else a.xhold,
           "feat": prep.FEAT2 if a.micro else prep.FEAT}
    st = Store()
    sp = split(st.mk)
    ids = [i for i in usable(st) if (cfg["feat"] / f"{i}.pkl").exists() and a.split in ("all", sp[i])]
    aggs, fills = [], []
    with Pool(a.workers, initializer=_init, initargs=(cfg,)) as pool:
        for ag, fl in pool.imap(_one, ids, chunksize=8):
            aggs.append(ag)
            fills.append(fl)
    OUT.mkdir(parents=True, exist_ok=True)
    for name, parts in (("agg", aggs), ("fills", fills)):
        parts = [p for p in parts if len(p)]
        if parts:
            d = pd.concat(parts, ignore_index=True)
            d["split"] = sp.reindex(d["m"]).to_numpy()
            d.to_pickle(OUT / f"{name}-{a.tag}.pkl")
    meta = pd.DataFrame({"m": ids, "split": [sp[i] for i in ids], "start": st.mk.start[ids].to_numpy()})
    meta.to_csv(OUT / f"markets-{a.tag}.csv", index=False)
    print("markets", len(ids))


if __name__ == "__main__":
    main()
