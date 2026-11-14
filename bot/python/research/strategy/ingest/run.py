"""Convert every complete recorded hour to data/cache/strategy/hour-<h>.npz (5m CLOB,
Binance spot, Binance perp) and refresh market outcomes from Gamma.

    nice -n 10 python3 -m research.strategy.ingest.run [--workers 2]

Idempotent: hours already converted are skipped. An hour is complete once the recorder has
moved past it (2 min margin)."""
from __future__ import annotations

import argparse
import time
from multiprocessing import Pool

import numpy as np

from .. import CACHE, LIVE
from . import binance, clob, markets



def hours() -> list[int]:
    hs = sorted({int(p.name.split("-")[-1].split(".")[0]) for p in LIVE.glob("*/clob_5m-*.tsv.gz")})
    return [h for h in hs if (h + 1) * 3600 < time.time() - 120]


def _one(args) -> str:
    h, assets = args
    out = CACHE / f"hour-{h}.npz"
    if out.exists():
        return f"{h} cached"
    t0 = time.time()
    d = {}
    for p in LIVE.glob(f"*/clob_5m-{h}.tsv.gz"):
        d.update(clob.parse(p, assets))
    for p in LIVE.glob(f"*/binance-{h}.tsv.gz"):
        d.update(binance.spot(p))
    for p in LIVE.glob(f"*/binance_fut-{h}.tsv.gz"):
        d.update(binance.perp(p))
    tmp = CACHE / f"hour-{h}.tmp.npz"
    np.savez(tmp, **d)
    tmp.rename(out)
    return f"{h} {time.time() - t0:.0f}s ev={len(d.get('ev_t', []))}"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=2)
    a = ap.parse_args()
    CACHE.mkdir(parents=True, exist_ok=True)
    mk = markets.markets()
    mk.to_csv(CACHE / "markets.csv", index=False)
    assets = markets.assets(mk)
    todo = [(h, assets) for h in hours()]
    with Pool(a.workers) as pool:
        for msg in pool.imap_unordered(_one, todo):
            print(msg, flush=True)
    o = markets.outcomes(mk)
    print("outcomes", len(o), "of", len(mk), "markets")


if __name__ == "__main__":
    main()
