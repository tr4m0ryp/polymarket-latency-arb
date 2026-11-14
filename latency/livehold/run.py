"""Sweep counterfactual limits over the live orders and write the tables.

    PYTHONPATH=. python3 -m latency.livehold.run   -> data/out/livehold/{rows.pkl,summary.md}"""
from __future__ import annotations

import pickle

import numpy as np
import pandas as pd

from research.predict.report.md import md
from . import OUT, TAPE
from .orders import load
from .replay import streams
from .sweep import run

B = 2000


def boot(df: pd.DataFrame, rng) -> tuple[float, float, float]:
    """Mean markout c/$ (cost-weighted) with a 95% bootstrap over markets."""
    f = df.dropna(subset=["mk10_c"])
    if f.empty:
        return np.nan, np.nan, np.nan
    g = f.groupby("slug").agg(pnl=("pnl", "sum"), cost=("cost", "sum"))
    pnl, cost = g["pnl"].to_numpy(), g["cost"].to_numpy()
    est = pnl.sum() / cost.sum() * 100
    idx = rng.integers(0, len(g), (B, len(g)))
    bs = pnl[idx].sum(1) / cost[idx].sum(1) * 100
    return est, *np.percentile(bs, [2.5, 97.5])


def table(rows: pd.DataFrame, subset: pd.Series | None = None) -> pd.DataFrame:
    rng = np.random.default_rng(7)
    out = []
    for rule, d in rows.groupby("rule", sort=False):
        if subset is not None:
            d = d[d["sig"].isin(subset)]
        n = len(d)
        f = d[d["fill_sh"] > 0]
        est, lo, hi = boot(f, rng)
        out.append({"rule": rule, "orders": n, "fill_rate": len(f) / n if n else np.nan,
                    "mk10_c_per_$": est, "lo": lo, "hi": hi,
                    "usd_per_order": f["pnl"].sum() / n if n else np.nan,
                    "avg_px_minus_seen_c": ((f["px"] - f["seen"]) * 100).mean()})
    return pd.DataFrame(out)


def main():
    o = load()
    cache = TAPE / "streams.pkl"
    if cache.exists():
        st = pickle.loads(cache.read_bytes())
    else:
        st = streams(set(o["token"]))
        cache.write_bytes(pickle.dumps(st))
    rows = run(o, st)
    OUT.mkdir(parents=True, exist_ok=True)
    rows.to_pickle(OUT / "rows.pkl")
    live = rows[rows["rule"] == "live"]
    v = pd.crosstab(live["filled_live"], live["fill_sh"] > 0, rownames=["live filled"], colnames=["replay fills"])
    missed = set(o.loc[~o["filled"], "sig"])
    parts = ["# Live hold: counterfactual limits\n", f"orders {len(o)}, live fills {int(o['filled'].sum())}, "
             f"markets {o['slug'].nunique()}\n", "## Replay check at the live limit\n", md(v.reset_index()),
             "\n## All sent orders\n", md(table(rows), 2),
             "\n## Orders that missed live\n", md(table(rows, missed), 2)]
    (OUT / "summary.md").write_text("\n".join(parts) + "\n")
    print("\n".join(parts))


if __name__ == "__main__":
    main()
