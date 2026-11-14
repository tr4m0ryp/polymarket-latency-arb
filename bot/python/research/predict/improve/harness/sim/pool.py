"""Run arms over markets in a forked worker pool (arms may be closures or hold fitted models:
the fork inherits them, nothing is pickled) and memoise results per (arm key, market).

Default 2 workers x 1 BLAS/OpenMP thread each (the shared box's 2-thread budget)."""
from __future__ import annotations

import multiprocessing as mp
import time

import pandas as pd

from .. import windows as W
from ..guard import assert_allowed
from . import worker


class Sim:
    def __init__(self, L=(0, -40), variants=("base", "comp"), workers: int = 2, threads: int = 1):
        self.L, self.variants = tuple(L), tuple(variants)
        self.workers, self.threads = workers, threads
        self.arms: dict = {}
        self.done: dict[tuple[str, int], pd.DataFrame] = {}
        self.activity: dict[int, dict] = {}
        self.secs = 0.0

    def add(self, key: str, arm) -> None:
        if key in self.arms:
            assert self.arms[key] is arm or self.arms[key].name == arm.name, f"arm key clash: {key}"
            return
        self.arms[key] = arm

    def run(self, need: dict[str, list[int]]) -> None:
        """Simulate every (key, market) in `need` that is not memoised yet."""
        per_m: dict[int, list[str]] = {}
        for key, ids in need.items():
            for i in ids:
                if (key, i) not in self.done:
                    per_m.setdefault(i, []).append(key)
        if not per_m:
            return
        start = W._markets().start
        assert_allowed(start[list(per_m)], "simulation request")
        tasks = sorted(per_m.items())
        worker._CFG.update(arms=self.arms, L=self.L, variants=self.variants, threads=self.threads)
        t0 = time.time()
        ctx = mp.get_context("fork")
        with ctx.Pool(self.workers, initializer=worker.init_worker) as pool:
            for n, (i, agg, act) in enumerate(pool.imap(worker.simulate_market, tasks, chunksize=2), 1):
                if n % 50 == 0:
                    print(f"  {n}/{len(tasks)} markets, {time.time() - t0:.0f}s", flush=True)
                self.activity[i] = act
                for key in per_m[i]:
                    self.done[(key, i)] = agg[agg["arm"] == key] if len(agg) else agg
        self.secs += time.time() - t0
        print(f"simulated {len(tasks)} markets x {sum(map(len, per_m.values())) / len(tasks):.1f} arms "
              f"in {time.time() - t0:.0f}s", flush=True)

    def agg(self, key: str, ids, label: str | None = None) -> pd.DataFrame:
        """Aggregates of one arm key on markets `ids` (all must be simulated), arm renamed."""
        parts = [self.done[(key, i)] for i in ids]
        parts = [p for p in parts if len(p)]
        if not parts:
            return pd.DataFrame(columns=["arm", "L", "m", "end", "var", "mk10v", "pnl", "cost", "n"])
        out = pd.concat(parts, ignore_index=True)
        out["arm"] = label or key
        return out
