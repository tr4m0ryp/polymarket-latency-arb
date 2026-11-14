"""Taker vs maker under the venue's taker hold: one row per arm x L x hold tag, from pooled
tags (sim.pool) run with --hold 0.15 and 0.27. Fill rate = simulated fills / decisions (takers
only); 10 s markout c/$ and $/day with a 95% market bootstrap CI.

    python3 -m research.predict.sim.holdcmp --tags hold150,hold270 --out data/out/predict/hold/summary.md"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from .. import OUT
from ..report.md import md
from ...strategy.eval.metrics import DAY_MARKETS


def _boot(g: pd.DataFrame, mk: np.ndarray, boot: int = 2000, seed: int = 3) -> dict:
    a = g.set_index("m").reindex(mk)
    v, c = a["mk10v"].fillna(0).to_numpy(), a["cost"].fillna(0).to_numpy()
    k = np.random.default_rng(seed).integers(0, len(mk), size=(boot, len(mk)))
    bv, bc = v[k].sum(1), c[k].sum(1)
    days = len(mk) / DAY_MARKETS
    return {"fills_day": a["n"].fillna(0).sum() / days,
            "mk10_cpd": 100 * v.sum() / c.sum() if c.sum() else np.nan,
            "mk_lo": 100 * np.percentile(bv / np.maximum(bc, 1e-9), 2.5),
            "mk_hi": 100 * np.percentile(bv / np.maximum(bc, 1e-9), 97.5),
            "mk10_day": v.sum() / days, "day_lo": np.percentile(bv, 2.5) / days,
            "day_hi": np.percentile(bv, 97.5) / days, "res_day": a["pnl"].fillna(0).sum() / days}


def rows(tag: str) -> pd.DataFrame:
    agg = pd.read_pickle(OUT / f"agg-{tag}.pkl")
    mk = pd.read_csv(OUT / f"markets-{tag}.csv")["m"].to_numpy()
    dp = OUT / f"dec-{tag}.pkl"
    dec = pd.read_pickle(dp).groupby(["arm", "L"])["ndec"].sum() if dp.exists() else pd.Series(dtype=float)
    out = []
    for (arm, L), g in agg.groupby(["arm", "L"]):
        r = {"hold": tag, "arm": arm, "L": L, **_boot(g, mk)}
        nd = dec.get((arm, L))
        r["fill_rate"] = g["n"].sum() / nd if nd else np.nan
        out.append(r)
    return pd.DataFrame(out)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tags", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    t = pd.concat([rows(x) for x in a.tags.split(",")], ignore_index=True)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    t.to_csv(Path(a.out).with_suffix(".csv"), index=False)
    cols = ["arm", "L", "hold", "fills_day", "fill_rate", "mk10_cpd", "mk_lo", "mk_hi", "mk10_day",
            "day_lo", "day_hi", "res_day"]
    Path(a.out).write_text(md(t[cols].sort_values(["L", "arm", "hold"]), 2) + "\n")
    print(Path(a.out).read_text())


if __name__ == "__main__":
    main()
