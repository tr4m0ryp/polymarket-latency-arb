"""Where does a live maker insert's ~100 ms go? Offline, from one run's logs (no network).

    python3 -m latency.infra.maker_latency.run --run dublin-maker-inside-20261014 [--no-book] [--no-load]

Per op (ops.py): decision -> send, signing, copy skew, round trip; venue book stamp split
(book.py: in = send -> on the venue's book, out = book -> ack); feed load at send (load.py).
Baselines from the same process: GET /data/order lookups (one session, one thread) and
keep-warm GET /time. Writes data/out/infra/maker_latency-<run>.csv."""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from . import book, load, ops

ROOT = Path(__file__).resolve().parents[3]
Q = (0.1, 0.5, 0.9)


def q(s: pd.Series) -> str:
    s = pd.to_numeric(s, errors="coerce").dropna()
    if not len(s):
        return "n 0"
    return f"n {len(s):3d}  " + "  ".join(f"p{int(x * 100)} {s.quantile(x):7.1f}" for x in Q)


def main(argv=None) -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    ap.add_argument("--no-book", action="store_true")
    ap.add_argument("--no-load", action="store_true")
    a = ap.parse_args(argv)
    root = ROOT / "data" / "trade" / a.run
    df = ops.frame(root)
    if not a.no_book:
        df = book.stamp(root, df)
    if not a.no_load:
        df = load.attach(df, load.per_second(root))
        df = load.attach(df, load.per_second(root, ("clob_5m",)), "clob_1s")     # the venue's own activity
    print(f"run {a.run}: {len(df)} acked ops")
    print(f"baseline GET /data/order (1 session)   {q(ops.lookups(root))}")
    print(f"baseline keep-warm GET /time           {q(ops.warm(root))}")
    for (what, via), g in df.groupby(["what", "via"]):
        print(f"\n{what} via {via} (k = {sorted(g['k'].dropna().unique())})")
        cols = ["dec_log", "log_send", "sign", "skew", "rtt", "rtt_min", "ack_spread"]
        cols += [c for c in ("in_ms", "out_ms", "feed_lag") if c in g]
        for c in cols:
            if g[c].notna().any():
                print(f"  {c:11s} {q(g[c])}")
        if "in_ms" in g:
            print(f"  book stamp found for {g['in_ms'].notna().sum()} / {len(g)}")
            c = g[(g["feed_lag"] < 25) & g["ok"]]                  # feed on time: the split is readable
            print(f"  feed lag < 25 ms: in  {q(c['in_ms'])}")
            print(f"  feed lag < 25 ms: out {q(c['out_ms'])}")
        if "msgs_1s" in g and g["msgs_1s"].notna().sum() > 5:
            lo = g["msgs_1s"] <= g["msgs_1s"].median()
            print(f"  feed msgs in the 1 s before send: {q(g['msgs_1s'])}")
            print(f"  rtt at load <= median: {q(g.loc[lo, 'rtt'])}")
            print(f"  rtt at load >  median: {q(g.loc[~lo, 'rtt'])}")
            for col in ("msgs_1s", "clob_1s"):
                r = np.corrcoef(g[col].fillna(0), g["rtt"])[0, 1]
                print(f"  corr(rtt, {col}) {r:+.2f}")
    out = ROOT / "data" / "out" / "infra" / f"maker_latency-{a.run}.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False)
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
