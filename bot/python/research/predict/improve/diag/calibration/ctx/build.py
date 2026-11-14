"""Build the per-row activity context of every allowed market (train, select, dev3, test3
run 1, ext) from the store, causal at each decision-table row time q.

    OMP_NUM_THREADS=1 nice -n 10 python3 -m research.predict.improve.diag.calibration.ctx.build [--workers 2]

Columns (float32, one per tab row):
- regime.py: bn10 bn60 sp10 rv1 rv10 rv60 jump10 pm10 pmtr60 pmtop10
- sp60: spot bookTicker msgs/s over 60 s; pm60: Polymarket book msgs/s over 60 s
- srv60: spot mid realised volatility over 60 s, bp per sqrt(s)
- pch60 / sch60: perp / spot mid changes per second over 60 s
- stn60 / stv60: spot trades per second / BTC per second over 60 s
Every stream is cut at SEALED before use (no row after the prereg2 seal is read)."""
from __future__ import annotations

import argparse
import time
from multiprocessing import Pool

import numpy as np

from ...... import predict
from .. import SEALED
from ..rows.regime import _count, _rv, regime
from ..safe import SafeStore, check, market_ids, start_of
from . import DIR

WINS = ("train", "select", "dev3", "final", "ext")
_ST = None


def _cut(d: dict) -> dict:
    if not d or "t" not in d:
        return d
    k = np.asarray(d["t"], float) < SEALED
    return {c: np.asarray(v)[k] for c, v in d.items()}


def context(m: dict, tab: dict) -> dict:
    for k in ("perp", "spot_bk", "spot_tr", "ev", "tr"):
        m[k] = _cut(m[k])
    q = np.asarray(tab["t"], float)
    assert q.max() < SEALED
    out = regime(m, tab)
    sb = m["spot_bk"]
    st = np.asarray(sb["t"], float)
    out["sp60"] = _count(st, q, 60.0)
    smid = np.log((sb["b"] + sb["a"]) / 2)
    cs = np.r_[0.0, np.cumsum(np.r_[0.0, np.diff(smid) ** 2])]
    out["srv60"] = _rv(st, cs, q, 60.0)
    pt = np.asarray(m["perp"]["t"], float)
    pmid = (m["perp"]["b"] + m["perp"]["a"]) / 2
    out["pch60"] = _count(pt[1:][np.diff(pmid) != 0], q, 60.0)
    smd = (sb["b"] + sb["a"]) / 2
    out["sch60"] = _count(st[1:][np.diff(smd) != 0], q, 60.0)
    out["pm60"] = _count(np.sort(np.asarray(m["ev"]["t"], float)), q, 60.0)
    tr = m["spot_tr"]
    tt = np.asarray(tr.get("t", []), float)
    o = np.argsort(tt, kind="stable")
    tt, qq = tt[o], np.asarray(tr.get("q", []), float)[o]
    out["stn60"] = _count(tt, q, 60.0)
    cq = np.r_[0.0, np.cumsum(qq)]
    out["stv60"] = (cq[np.searchsorted(tt, q, side="right")] - cq[np.searchsorted(tt, q - 60, side="right")]) / 60
    return {k: np.asarray(v, np.float32) for k, v in out.items()}


def one(i: int) -> tuple[int, int]:
    DIR.mkdir(parents=True, exist_ok=True)
    global _ST
    _ST = _ST or SafeStore()
    dst = DIR / f"{i}.npz"
    with np.load(predict.CACHE / "tab" / f"{i}.npz") as z:
        tab = {k: z[k] for k in ("t", "pm_bb", "pm_ba")}
    if dst.exists():
        with np.load(dst) as z:
            if len(z["bn60"]) == len(tab["t"]):
                return i, 0
    m = _ST.market(i)
    if m is None:
        return i, -1
    c = context(m, tab)
    tmp = dst.with_name(f"{i}.tmp.npz")
    np.savez(tmp, **c)
    tmp.replace(dst)
    return i, len(tab["t"])


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--win", default=",".join(WINS))
    ap.add_argument("--workers", type=int, default=2)
    a = ap.parse_args()
    DIR.mkdir(parents=True, exist_ok=True)
    ids = []
    for w in a.win.split(","):
        x = market_ids(w)
        check(start_of(x))
        ids += x
    t0 = time.time()
    with Pool(min(a.workers, 2)) as pool:
        for j, (i, n) in enumerate(pool.imap_unordered(one, ids, chunksize=4)):
            if j % 50 == 0:
                print(j, len(ids), i, n, f"{time.time() - t0:.0f}s", flush=True)
    print("done", len(ids), f"{time.time() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
