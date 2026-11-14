"""A paper run's logs as frames: one row per would-be order (orders stream) with the market
outcome joined (settle stream; Gamma for markets the run did not settle), scored like the
simulator's fills (research/predict/sim/fills.py): hold to resolution at the 0% tier, and
10 s / 3 s venue-mid markouts, a missing mid valued at the outcome."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from recorder.live.sink import read_stream

AGG = dict(n=("shares", "size"), won_n=("won", "sum"), shares=("shares", "sum"),
           cost=("cost", "sum"), fee=("fee", "sum"), pnl=("pnl", "sum"), mk3v=("mk3v", "sum"),
           mk10v=("mk10v", "sum"))


def _rows(root: Path, name: str) -> list[dict]:
    return [json.loads(raw) for _, raw in read_stream(name, root=root)]


def outcomes(root: Path, slugs) -> dict[str, float]:
    oc = {r["slug"]: float(r["outcome"]) for r in _rows(root, "settle")}
    missing = [s for s in slugs if s not in oc]
    if missing:
        from research.strategy.ingest.markets import _gamma_outcome
        for s in missing:
            try:
                o = _gamma_outcome(s)
            except OSError:
                o = None
            if o is not None:
                oc[s] = o
    return oc


def orders(root: Path) -> pd.DataFrame:
    df = pd.DataFrame(_rows(root, "orders"))
    if not len(df):
        return df
    oc = outcomes(root, df["slug"].unique())
    df["outcome"] = df["slug"].map(oc)
    return df


def fills(df: pd.DataFrame) -> pd.DataFrame:
    """Filled, gap-free, settled orders in the simulator's fill columns."""
    f = df[(df["fill_sh"] > 0) & ~df["gap"].astype(bool) & df["outcome"].notna()].copy()
    f["shares"] = f["fill_sh"]
    f["won"] = np.where(f["side"] > 0, f["outcome"], 1 - f["outcome"])
    f["pnl"] = f["shares"] * f["won"] - f["cost"] - f["fee"]
    for h in (3, 10):
        mk = pd.to_numeric(f.get(f"mk{h}"), errors="coerce") if f"mk{h}" in f else np.nan
        f[f"mk{h}v"] = f["shares"] * pd.Series(mk, index=f.index).fillna(f["won"]) - f["cost"] - f["fee"]
    f["m"] = f["slug"]
    return f


def aggregate(f: pd.DataFrame) -> pd.DataFrame:
    return f.groupby(["arm", "L", "m", "end"]).agg(**AGG).reset_index()
