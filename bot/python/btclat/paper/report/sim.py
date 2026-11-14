"""The replay simulator on the paper run's markets, same four arms, same L.

    python3 -m btclat.paper.report.sim --run <run> --L 0 [--raw]

Without --raw the markets come from the research caches (data/live recorded them: replay
runs, or hours the local recorder also covered). With --raw the run's own recording
(data/paper/<run>/raw, e.g. from Dublin) is converted first, into data/paper/<run>/cache,
by the research pipeline itself: strategy ingest -> v2 feature tables -> predict tables.
Then research/predict/sim/run.py `_one` runs per market. Writes data/paper/<run>/sim-fills.pkl."""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

PAPER = Path(__file__).resolve().parents[3] / "data" / "paper"


def env_for(run: str, root: Path = PAPER) -> dict:
    d = root / run
    return dict(os.environ, BTCLAT_LIVE=str(d / "raw"), BTCLAT_STRATEGY_CACHE=str(d / "cache" / "strategy"),
                BTCLAT_PREDICT_CACHE=str(d / "cache" / "predict"))


def prepare(run: str, root: Path = PAPER) -> None:
    env = env_for(run, root)
    for k in ("BTCLAT_STRATEGY_CACHE", "BTCLAT_PREDICT_CACHE"):
        Path(env[k]).mkdir(parents=True, exist_ok=True)
    (Path(env["BTCLAT_PREDICT_CACHE"]) / "tab").mkdir(exist_ok=True)
    for mod, args in (("research.strategy.ingest.run", ["--workers", "1"]),
                      ("research.strategy.eval.prep", ["--micro", "--workers", "1"]),
                      ("research.predict.feats.run", ["--seg", "train,select,dev3,test3", "--workers", "1"])):
        subprocess.run(["nice", "-n", "10", sys.executable, "-m", mod, *args], env=env, check=True)


def simulate(slugs: list[str], L: int) -> "object":
    """In-process; the research path overrides must already be in the environment."""
    import pandas as pd

    from research.predict.sim import run as prun
    from research.predict.sim.arms.base import ARMS as BASE
    from research.strategy import CACHE

    from ..arms.defs import VT_ARMS
    mk = pd.read_csv(CACHE / "markets.csv", dtype={"up": str, "down": str})
    ids = [int(i) for i in mk.index[mk["slug"].isin(slugs)]]
    prun._init({"arms": list(BASE) + VT_ARMS, "L": [L], "J": 0.010, "cap": 1.0, "hold": 0.150})
    out = []
    for i in ids:
        try:
            _, f, _ = prun._one(i)   # (agg, fills, taker decision counts)
        except (FileNotFoundError, TypeError):   # no tables or no outcome: not usable in the sim
            continue
        if len(f):
            out.append(f.assign(slug=mk.loc[i, "slug"]))
    return pd.concat(out, ignore_index=True) if out else pd.DataFrame()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    ap.add_argument("--L", type=int, default=0)
    ap.add_argument("--raw", action="store_true")
    ap.add_argument("--slugs", default=None, help="json list (internal)")
    a = ap.parse_args()
    if a.raw and "BTCLAT_LIVE" not in os.environ:
        prepare(a.run)
        os.execve(sys.executable, [sys.executable, "-m", "btclat.paper.report.sim", *sys.argv[1:]],
                  env_for(a.run))
    slugs = json.loads(a.slugs) if a.slugs else json.loads((PAPER / a.run / "slugs.json").read_text())
    f = simulate(slugs, a.L)
    f.to_pickle(PAPER / a.run / "sim-fills.pkl")
    print("sim fills", len(f))


if __name__ == "__main__":
    main()
