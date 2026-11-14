"""A live-test run's logs as frames. Orders: one row per signal (live result joined with the
paper prediction), outcomes from the run's settle stream or Gamma (paper report's loader), 10 s
markout values in $ for both legs, a missing mark valued at the outcome as the paper report does."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from recorder.live.sink import read_stream
from btclat.paper.report.load import outcomes


def rows(root: Path, name: str) -> list[dict]:
    return [json.loads(raw) for _, raw in read_stream(name, root=root)]


def orders(root: Path, gamma: bool = True) -> pd.DataFrame:
    df = pd.DataFrame(rows(root, "orders"))
    if not len(df):
        return df
    oc = outcomes(root, df["slug"].unique()) if gamma else {r["slug"]: r["outcome"] for r in rows(root, "settle")}
    df["outcome"] = df["slug"].map(oc)
    df["won"] = np.where(df["up"].astype(bool), df["outcome"], 1 - df["outcome"])
    for c in ("fill_sh", "fill_cost", "fee", "px", "mk10_live", "t_send_ns", "t_ack_ns", "sign_us"):
        df[c] = pd.to_numeric(df[c], errors="coerce") if c in df else np.nan
    df["fill_sh"] = df["fill_sh"].fillna(0.0)
    df["fee"] = df["fee"].fillna(0.0)
    mk = df["mk10_live"].fillna(df["won"])
    df["live_v10"] = np.where(df["fill_sh"] > 0, df["fill_sh"] * mk - df["fill_cost"] - df["fee"], np.nan)
    df["live_vres"] = np.where(df["fill_sh"] > 0, df["fill_sh"] * df["won"] - df["fill_cost"] - df["fee"], np.nan)
    papers = [x if isinstance(x, dict) else {} for x in (df["paper"] if "paper" in df else [None] * len(df))]
    p = pd.DataFrame(papers, index=df.index).add_prefix("p_")
    df = pd.concat([df, p], axis=1)
    for c in ("p_fill_sh", "p_cost", "p_fee", "p_px", "p_mk10"):
        df[c] = pd.to_numeric(df[c], errors="coerce") if c in df else np.nan
    df["p_fill_sh"] = df["p_fill_sh"].fillna(0.0)
    pmk = df["p_mk10"].fillna(df["won"])
    df["paper_v10"] = np.where(df["p_fill_sh"] > 0, df["p_fill_sh"] * pmk - df["p_cost"] - df["p_fee"], np.nan)
    df["sent"] = df["decision"] == "sent"
    df["filled"] = df["fill_sh"] > 0
    df["p_filled"] = df["p_fill_sh"] > 0
    return df


def probe(root: Path) -> pd.DataFrame:
    return pd.DataFrame(rows(root, "probe"))


def events(root: Path) -> list[dict]:
    return rows(root, "events")
