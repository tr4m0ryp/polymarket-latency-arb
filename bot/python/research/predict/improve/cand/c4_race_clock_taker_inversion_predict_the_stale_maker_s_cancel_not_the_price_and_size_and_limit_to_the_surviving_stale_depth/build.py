"""Build the depth cache of every allowed market (run 2 train, select, dev3, test3 run 1, ext).

    OMP_NUM_THREADS=1 nice -n 10 python3 -m research.predict.improve.cand.<c4 package>.build"""
from __future__ import annotations

import time
from multiprocessing import get_context

from ...harness import windows as W
from . import assert_open, depth

WINS = ("train", "select", "dev3", "test3r1", "ext")


def ids() -> list[int]:
    out = sorted({i for w in WINS for i in W.ids(w)})
    mk = W._markets()
    assert_open(mk.start[out])
    return out


def _one(i: int) -> int:
    depth.load(i)
    return i


def main(workers: int = 2) -> None:
    todo = [i for i in ids() if not (depth.DIR / f"{i}.npz").exists()]
    t0 = time.time()
    with get_context("fork").Pool(workers) as pool:
        for n, _ in enumerate(pool.imap_unordered(_one, todo, chunksize=4), 1):
            if n % 50 == 0:
                print(f"{n}/{len(todo)} {time.time() - t0:.0f}s", flush=True)
    print(f"built {len(todo)} markets in {time.time() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
