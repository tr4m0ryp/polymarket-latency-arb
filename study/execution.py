"""Execution microstructure of the latency wallets.

    python3 study/execution.py

Takes the latency rows of data/out/latency/wallets.csv (all latency_arb,
latency_arb_partial with |PnL| >= $100, momentum_taker with PnL >= $2k or
<= -$500), recomputes per-fill features per family and writes one row of
exec_stats.wallet_exec per wallet x family to data/out/latency/execution.csv,
plus a per-market example cycle for each wallet to execution_cycles.csv."""
from __future__ import annotations

import sys
import time
from pathlib import Path

import pandas as pd

from exec_stats import wallet_exec
from features import family_frame

OUT = Path(__file__).resolve().parents[1] / "data" / "out" / "latency"


def selected() -> pd.DataFrame:
    d = pd.read_csv(OUT / "wallets.csv")
    c, p = d["latency_class"], d["pnl"]
    keep = ((c == "latency_arb") | ((c == "latency_arb_partial") & (p.abs() >= 100))
            | ((c == "momentum_taker") & ((p >= 2000) | (p <= -500))))
    return d.loc[keep, ["wallet", "series", "latency_class", "pnl"]]


def example_cycle(x: pd.DataFrame) -> pd.DataFrame:
    """Tx-level trace of the wallet's median-fill-count market."""
    n = x.groupby("condition_id").size()
    cid = (n - n.median()).abs().idxmin()
    g = x[x["condition_id"] == cid]
    t = g.groupby("tx", sort=False).agg(
        ts=("ts", "first"), t_rel=("t_rel", "first"), secs_to_end=("secs_to_end", "first"),
        side=("side", "first"), outcome=("outcome_index", "first"), shares=("size", "sum"),
        usd=("usd", "sum"), price=("price", "mean"), taker=("taker", "max"),
        fills=("q", "size"), r3_bp=("r3", "first"), fair=("fair", "first"), pi=("pi", "mean"),
        R=("R", "first"))
    t["r3_bp"] *= 1e4
    t.insert(0, "condition_id", cid)
    return t.reset_index()


def main() -> None:
    sel = selected()
    rows, cycles = [], []
    for slug, s in sel.groupby("series"):
        t0 = time.time()
        f, _ = family_frame(slug)
        f = f[f["wallet"].isin(set(s["wallet"]))]
        for _, r in s.iterrows():
            x = f[f["wallet"] == r["wallet"]]
            rows.append({"wallet": r["wallet"], "series": slug, "latency_class": r["latency_class"],
                         **wallet_exec(x)})
            cycles.append(example_cycle(x).assign(wallet=r["wallet"], series=slug))
        print(f"{slug}: {len(s)} wallets, {time.time() - t0:.0f}s", flush=True)
        del f
    out = pd.DataFrame(rows).sort_values("pnl", ascending=False)
    out.to_csv(OUT / "execution.csv", index=False, float_format="%.6g")
    pd.concat(cycles).to_csv(OUT / "execution_cycles.csv", index=False, float_format="%.6g")
    print(f"{len(out)} rows -> {OUT / 'execution.csv'}")


if __name__ == "__main__":
    sys.exit(main())
