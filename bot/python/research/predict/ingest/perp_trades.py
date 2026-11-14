"""Run-3 Binance USD-M perp raw trades (`binance_fut-<h>`, @trade) -> data/cache/predict/
ftr-<h>.npz: receipt t, trade time T, price, qty, buyer-is-maker. The strategy ingest keeps
only the perp bookTicker, so the trade stream is parsed here.

    nice -n 10 python3 -m research.predict.ingest.perp_trades [--workers 2]"""
from __future__ import annotations

import argparse
import json
import time
from multiprocessing import Pool

import numpy as np

from .. import CACHE, RUN3
from ...strategy import LIVE
from ...strategy.ingest.clob import _lines


def _one(path) -> str:
    h = int(path.name.split("-")[-1].split(".")[0])
    out = CACHE / f"ftr-{h}.npz"
    if out.exists():
        return f"{h} cached"
    rows = []
    for t, raw in _lines(path):
        if '"@trade"' not in raw[:40] and "btcusdt@trade" not in raw[:40]:
            continue
        d = json.loads(raw)["data"]
        rows.append((t, d["T"] / 1e3, float(d["p"]), float(d["q"]), float(d["m"])))
    a = np.array(rows, dtype=float).reshape(-1, 5)
    tmp = CACHE / f"ftr-{h}.tmp.npz"
    np.savez(tmp, t=a[:, 0], T=a[:, 1], px=a[:, 2], q=a[:, 3].astype(np.float32),
             m=a[:, 4].astype(np.int8))
    tmp.rename(out)
    return f"{h} n={len(a)}"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=2)
    a = ap.parse_args()
    CACHE.mkdir(parents=True, exist_ok=True)
    done = time.time() - 120
    todo = [p for p in sorted(LIVE.glob("*/binance_fut-*.tsv.gz"))
            if RUN3 // 3600 <= int(p.name.split("-")[-1].split(".")[0]) and
            (int(p.name.split("-")[-1].split(".")[0]) + 1) * 3600 < done]
    with Pool(a.workers) as pool:
        for msg in pool.imap_unordered(_one, todo):
            print(msg, flush=True)


if __name__ == "__main__":
    main()
