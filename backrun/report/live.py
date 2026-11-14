"""The two live micro runs of 2026-10-13 from their own order logs (Dublin, FAK, 5 shares,
arm vt_v1_m0.03_any, limit = seen ask + 2 c). Gross = before the taker fee, so the fee is
not counted twice in the bounds; `net_mk10_cpd` reproduces the ledger's after-fee figure."""
from __future__ import annotations

import gzip
import json

import pandas as pd

from .. import DATA, LIVE_RUNS, RUN
from .boot import draws, ratio, sums

KEEP = ("slug", "up", "seen", "limit", "size", "fill_sh", "fill_cost", "fee", "px", "mk10_live",
        "t_decision", "t_ack_ns")


def orders(run: str) -> pd.DataFrame:
    rows = []
    for f in sorted((DATA / "trade" / run).glob("*/orders-*.tsv.gz")):
        with gzip.open(f, "rt") as fh:
            for line in fh:
                r = json.loads(line.split("\t", 1)[1].replace("NaN", "null"))
                if r.get("decision") == "sent" and r.get("final"):
                    rows.append({k: r.get(k) for k in KEEP})
    df = pd.DataFrame(rows)
    oc = json.loads((RUN / "cache" / "strategy" / "outcomes.json").read_text())
    df["outcome"] = df["slug"].map(oc)
    df["won"] = df["outcome"].where(df["up"].astype(bool), 1 - df["outcome"])
    for c in ("fill_sh", "fill_cost", "fee"):
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0.0)
    df["mk"] = pd.to_numeric(df["mk10_live"], errors="coerce").fillna(df["won"])
    df["sought"] = df["size"] * df["limit"]
    df["v10"] = df["fill_sh"] * df["mk"] - df["fill_cost"]
    df["vres"] = df["fill_sh"] * df["won"] - df["fill_cost"]
    df["v10_net"] = df["v10"] - df["fee"]
    df["hold_ms"] = (df["t_ack_ns"] / 1e9 - df["t_decision"]) * 1e3
    return df


def summary(df: pd.DataFrame) -> dict:
    f = df[df["fill_sh"] > 0]
    i0 = f[f["px"] <= f["seen"] + 1e-9]            # fills that a limit at the seen ask would also get
    idx = draws(df["slug"].nunique())
    s = sums(df, ["fill_cost", "sought", "v10", "vres", "v10_net", "fee"])
    out = {"orders": len(df), "fills": len(f), "markets": int(df["slug"].nunique()),
           "fill_rate_count": round(len(f) / len(df), 4),
           "fill_rate_dollars": ratio(s, 0, 1, idx, 1.0),
           "gross_mk10_cpd": ratio(s, 2, 0, idx), "gross_res_cpd": ratio(s, 3, 0, idx),
           "net_mk10_cpd": ratio(s, 4, 0, idx), "fee_cpd": ratio(s, 5, 0, idx),
           "decision_to_ack_ms_p50": round(float(df["hold_ms"].median()), 1),
           "fills_at_seen_or_better": len(i0),
           "fill_rate_count_limit_seen": round(len(i0) / len(df), 4),
           "avg_fill_px_minus_seen_c": round(100 * float((f["px"] - f["seen"]).mean()), 2)}
    return out


def live() -> dict:
    per = {r: orders(r) for r in LIVE_RUNS}
    out = {r: summary(d) for r, d in per.items()}
    out["pooled"] = summary(pd.concat(per.values(), ignore_index=True))
    return out


if __name__ == "__main__":
    print(json.dumps(live(), indent=1))
