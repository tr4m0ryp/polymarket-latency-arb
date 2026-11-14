"""Sent orders of the live micro runs as a flat table (one row per order)."""
from __future__ import annotations

import gzip
import json

import pandas as pd

from . import RUNS, TRADE


def load(runs=RUNS) -> pd.DataFrame:
    rows = []
    for run in runs:
        for f in sorted((TRADE / run).glob("*/orders-*.tsv.gz")):
            with gzip.open(f, "rt") as fh:
                for line in fh:
                    r = json.loads(line.split("\t", 1)[1].replace("NaN", "null"))
                    if r.get("decision") != "sent" or not r.get("final"):
                        continue
                    p = r.get("paper") or {}
                    rows.append({
                        "run": run, "sig": r["sig"], "slug": r["slug"], "token": r["token"],
                        "t_send": r["t_send_ns"] / 1e9, "t_ack": r["t_ack_ns"] / 1e9,
                        "t_event": r.get("t_event_venue"), "seen": r["seen"], "limit": r["limit"],
                        "edge": r["edge"], "size": r["size"], "filled": (r.get("fill_sh") or 0) > 0,
                        "fill_sh": r.get("fill_sh") or 0.0, "px": r.get("px"),
                        "paper_mk10": p.get("mk10"), "paper_fill": (p.get("fill_sh") or 0) > 0,
                        "paper_px": p.get("px"), "ack_ms": r["post"]["ms"],
                    })
    return pd.DataFrame(rows).sort_values("t_send").reset_index(drop=True)
