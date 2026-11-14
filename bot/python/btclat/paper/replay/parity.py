"""Feature parity: replay recorded hours through the live state and compare every decision
row with the offline table (data/cache/predict/tab/<i>.npz, research/predict/feats/build.py).

    nice -n 10 python3 -m btclat.paper.replay.parity [--hour 497697] [--max-markets 12]

Polymarket messages are put on the research 5 ms grid (replay/source.py quantize) so both
sides read the same book. Prints per-column max |live - offline| (offline is float32) and
the value-model scores of both pipelines; writes data/paper/parity-<hour>.json."""
from __future__ import annotations

import argparse
import json
import time

import numpy as np
import pandas as pd

from research.predict.model.data import TAB
from research.strategy import CACHE as SCACHE

from ..engine.world import World
from ..features.raw import row
from . import source
from .compare import compare, grid_quirk
from .scores import score_parity

ROOT = source.LIVE.parent / "paper"


def offline(hour: int, max_markets: int) -> tuple[dict, dict]:
    mk = pd.read_csv(SCACHE / "markets.csv", dtype={"up": str, "down": str})
    w = mk[(mk.start >= hour * 3600) & (mk.start < (hour + 1) * 3600)].head(max_markets)
    tabs, ids = {}, {}
    for i, m in w.iterrows():
        p = TAB / f"{i}.npz"
        if p.exists():
            with np.load(p) as z:
                tabs[m["slug"]] = {k: z[k] for k in z.files}
            ids[m["slug"]] = i
    return tabs, ids


def live_rows(hour: int, tabs: dict) -> dict:
    qs = sorted((float(q), s, j) for s, d in tabs.items() for j, q in enumerate(d["t"]))
    out = {s: [None] * len(d["t"]) for s, d in tabs.items()}
    w, k = World(), 0
    for ev in source.events(source.LIVE, (hour - 1, hour), quantize=True):
        while k < len(qs) and qs[k][0] < ev[1]:
            q, s, j = qs[k]
            out[s][j] = row(q, w.ctx, w.mkts[s])
            k += 1
        w.apply(ev)
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--hour", type=int, default=497697)
    ap.add_argument("--max-markets", type=int, default=12)
    a = ap.parse_args()
    t0 = time.time()
    tabs, ids = offline(a.hour, a.max_markets)
    rows = live_rows(a.hour, tabs)
    starts = {s: int(s.rsplit("-", 1)[1]) for s in tabs}
    cmp, counts = compare(tabs, rows, starts)
    pd.set_option("display.width", 200)
    pd.set_option("display.max_rows", 300)
    print(cmp.to_string(index=False), counts)
    quirk = {s: grid_quirk(d["t"], starts[s]) for s, d in tabs.items()}
    sc = score_parity(tabs, rows, quirk=quirk)
    print(json.dumps(sc, indent=1))
    ROOT.mkdir(parents=True, exist_ok=True)
    (ROOT / f"parity-{a.hour}.json").write_text(json.dumps(
        {"hour": a.hour, "markets": ids, "rows": int(sum(len(d["t"]) for d in tabs.values())),
         "counts": counts, "features": cmp.to_dict("records"),
         "scores": sc, "secs": time.time() - t0}, indent=1, default=float))


if __name__ == "__main__":
    main()
