"""Dry / live maker vs the simulator.

1. Reference: the run's arm's pooled unseen-market row (data/out/predict/hold/summary.csv, hold
   0.27 s, L = 50 ms: fills per day, 10 s markout c/$ with CI; 60-share quotes; none yet for the
   inside gate).
2. Same markets (when the run recorded its raw feeds, `--record`): the replay simulator on the
   run's own recording, converted by the research pipeline (btclat/paper/report/sim.py
   `prepare`), the frozen arm at 5-share quotes and the run's L and hold:

    python3 -m btclat.trade.report.maker.sim --run <run> [--L 50] [--hold 0.27]

writes data/trade/<run>/sim-fills.pkl, which the report then reads."""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from recorder.live.sink import read_stream
from research.predict import OUT as POUT
from research.predict.report.md import md

from ..stats import boot_cpd

TRADE = Path(__file__).resolve().parents[4] / "data" / "trade"
REF = POUT / "hold" / "summary.csv"
SIZE, MAX_OPEN = 5.0, 20.0           # our quote size; ~ the $10 market cap in shares at p ~ 0.5


def reference(L: int = 50, hold: str = "hold270", arm: str | None = None) -> dict | None:
    from btclat.trade.maker.arm import NAME
    if not REF.exists():
        return None
    d = pd.read_csv(REF)
    r = d[(d["hold"] == hold) & (d["arm"] == (arm or NAME)) & (d["L"] == L)]
    return None if not len(r) else r.iloc[0].to_dict()


def section(root: Path, f: pd.DataFrame, h: float, arm: str | None = None) -> list[str]:
    rows = []
    ref = reference(arm=arm)
    if ref is not None:
        rows.append({"source": "sim reference (575 unseen markets, 60 sh)", "fills_h": ref["fills_day"] / 24,
                     "mk10_cpd": ref["mk10_cpd"], "lo": ref["mk_lo"], "hi": ref["mk_hi"]})
    if len(f):
        mk = boot_cpd(f["v10"], f["cost"], f["slug"])
        rows.append({"source": "this run", "fills_h": len(f) / h if h == h and h > 0 else np.nan,
                     "mk10_cpd": mk[0], "lo": mk[1], "hi": mk[2]})
    p = Path(root) / "sim-fills.pkl"
    if p.exists():
        s = pd.read_pickle(p)
        if len(s):
            mk = boot_cpd(s["mk10v"], s["cost"], s["m"])
            rows.append({"source": f"sim (frozen arm), same markets ({s['m'].nunique()}), 5 sh", "fills_h": len(s) / h if h == h and h > 0 else np.nan,
                         "mk10_cpd": mk[0], "lo": mk[1], "hi": mk[2]})
    if not rows:
        return []
    note = [] if p.exists() else ["(same-market sim: record the run with --record, then "
                                  "`python3 -m btclat.trade.report.maker.sim --run <run>`)"]
    return ["Versus the simulator (fill events per hour, 10 s markout c/$):", "", md(pd.DataFrame(rows), 2), *note]


def simulate(slugs: list[str], L: int, hold: float) -> pd.DataFrame:
    """In-process; the research path overrides must already be in the environment."""
    from research.predict.sim import run as prun
    from research.strategy import CACHE

    from btclat.trade.maker.arm import ARM
    mk = pd.read_csv(CACHE / "markets.csv", dtype={"up": str, "down": str})
    ids = [int(i) for i in mk.index[mk["slug"].isin(slugs)]]
    prun._init({"arms": [dict(ARM, size=SIZE, max_open=MAX_OPEN)], "L": [L], "J": 0.010, "cap": 1.0, "hold": hold})
    out = []
    for i in ids:
        try:
            _, f, _ = prun._one(i)
        except (FileNotFoundError, TypeError):   # no tables or no outcome: not usable
            continue
        if len(f):
            out.append(f.assign(slug=mk.loc[i, "slug"]))
    return pd.concat(out, ignore_index=True) if out else pd.DataFrame()


def main() -> None:
    from btclat.paper.report import sim as psim
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    ap.add_argument("--L", type=int, default=50)
    ap.add_argument("--hold", type=float, default=0.27)
    a = ap.parse_args()
    root = TRADE / a.run
    if "BTCLAT_LIVE" not in os.environ:
        psim.prepare(a.run, root=TRADE)
        os.execve(sys.executable, [sys.executable, "-m", "btclat.trade.report.maker.sim", *sys.argv[1:]],
                  psim.env_for(a.run, root=TRADE))
    q = pd.DataFrame([json.loads(r) for _, r in read_stream("quotes", root=root)])
    slugs = sorted(q["slug"].unique()) if len(q) else []
    f = simulate(slugs, a.L, a.hold)
    f.to_pickle(root / "sim-fills.pkl")
    print("sim fills", len(f), "markets", len(slugs))


if __name__ == "__main__":
    main()
