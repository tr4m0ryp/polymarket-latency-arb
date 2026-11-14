"""Build the order streams: data/out/bankroll/stream.npz (one file, both arms, all hours).

    PYTHONPATH=. nice -n 10 python3 -m research.bankroll.stream.run --workers 6"""
from __future__ import annotations

import argparse
from multiprocessing import Pool

import numpy as np

from .. import K, OUT, SCENS
from .decide import orders
from .extract import market_ladders
from .hold import holds

_st = _o = _H = None


def _init(o, H):
    global _o, _H
    _o, _H = o, H


def _do(i):
    global _st
    from research.strategy.ingest.load import Store
    _st = _st or Store(keep=2)
    o = _o[_o["m"] == i]
    m = _st.market(i)
    if m is None or m["outcome"] is None:
        return i, None
    return i, market_ladders(m, o, _H, np.random.default_rng(i))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=6)
    a = ap.parse_args()
    o = orders()
    H = holds()
    ids = sorted(o["m"].unique())
    with Pool(a.workers, _init, (o, H)) as p:
        res = dict(p.imap_unordered(_do, ids, chunksize=1))
    n = len(o)
    where = {i: np.flatnonzero(o["m"].to_numpy() == i) for i in ids}   # same order _do saw
    out = {}
    for sc in SCENS:
        h = np.zeros((n, K), np.float32)
        off, cnt = np.zeros((n, K), np.int64), np.zeros((n, K), np.int32)
        cols, ticks, shs, tot = [], [], [], 0
        for i in ids:
            if res.get(i) is None:
                continue
            hh, lad = res[i][sc]
            for s, r in enumerate(where[i]):
                h[r] = hh[s]
                for k in range(K):
                    c, p, q = lad[s][k]
                    off[r, k], cnt[r, k] = tot, len(c)
                    cols.append(c); ticks.append(p); shs.append(q)
                    tot += len(c)
        out[f"{sc}_h"], out[f"{sc}_off"], out[f"{sc}_n"] = h, off, cnt
        out[f"{sc}_col"] = np.concatenate(cols).astype(np.int16)
        out[f"{sc}_tick"] = np.concatenate(ticks).astype(np.int16)
        out[f"{sc}_sh"] = np.concatenate(shs).astype(np.float32)
    ok = np.array([res.get(i) is not None for i in o["m"].to_numpy()])
    for c in ("m", "t", "side", "seen", "won", "end", "score", "tau", "v1val", "test"):
        out[c] = o[c].to_numpy()
    out["arm"] = o["arm"].to_numpy().astype("U12")
    out["ok"] = ok
    OUT.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(OUT / "stream.npz", **out)
    print({arm: int(((out["arm"] == arm) & ok).sum()) for arm in np.unique(out["arm"])}, "markets", len(ids),
          "dropped", int((~ok).sum()))


if __name__ == "__main__":
    main()
