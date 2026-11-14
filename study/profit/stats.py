"""Robustness and counterfactual columns for the profit decomposition.

    python3 study/profit/stats.py

Adds to data/out/latency/profit/summary.csv (writes summary_stats.csv):
  net_t          t-stat of per-market net PnL (net = gross - fee + maker rebate
                 + taker rebate at the wallet's observed rate, capped at 50 %)
  net_A, net_B   net PnL in the chronological first / second half of markets
  net_at_50      net PnL had the wallet been at the 50 % taker-rebate tier
  net_at_0       net PnL with no taker rebate
and writes head_to_head.csv: for wallet pairs in one family, the blocks in
which both took the same direction in the same market, with each side's
YES-frame VWAP; price_gap > 0 means wallet a paid less for its side."""
from __future__ import annotations

import numpy as np
import pandas as pd

from extract import ROOT, build
from run import FAMILIES, OUT


def per_market(f: pd.DataFrame, rate: pd.Series) -> pd.DataFrame:
    r = f["wallet"].map(rate).fillna(0).clip(upper=0.5)
    f = f.assign(net=f["pnl"] - f["fee"] * (1 - r) + f["maker_rebate"])
    return f.groupby(["wallet", "condition_id"]).agg(net=("net", "sum"), ts=("ts", "min"))


def robust(pm: pd.DataFrame) -> pd.DataFrame:
    def one(x: pd.DataFrame) -> pd.Series:
        n = x["net"].to_numpy()
        half = x["ts"] <= x["ts"].median()
        t = n.mean() / (n.std(ddof=1) / np.sqrt(len(n))) if len(n) > 2 and n.std() > 0 else np.nan
        return pd.Series({"net_t": t, "net_A": x.loc[half, "net"].sum(),
                          "net_B": x.loc[~half, "net"].sum()})
    return pm.groupby(level=0).apply(one).reset_index()


def head_to_head(f: pd.DataFrame, a: str, b: str) -> dict:
    tk = f[(f["taker"] == 1) & f["wallet"].isin([a, b])].assign(d=lambda x: np.sign(x["q"]))
    tk = tk.assign(pw=tk["pi"] * tk["q"].abs(), w=tk["q"].abs())
    g = tk.groupby(["condition_id", "ts", "d", "wallet"])[["pw", "w", "pnl", "usd"]].sum()
    g["vwap"] = g["pw"] / g["w"]
    p = g["vwap"].unstack("wallet").dropna()
    if p.empty:
        return {}
    d = p.index.get_level_values("d")
    gap = (p[b] - p[a]) * d  # >0: a bought Up cheaper / sold Up dearer
    u = g["usd"].unstack("wallet").reindex(p.index)
    both = g["usd"].unstack("wallet")
    return {"a": a, "b": b, "shared_blocks": len(p),
            "a_usd_share_shared": u[a].sum() / both[a].sum(),
            "b_usd_share_shared": u[b].sum() / both[b].sum(),
            "price_gap_mean": float(gap.mean()), "a_better_share": float((gap > 0).mean()),
            "b_better_share": float((gap < 0).mean())}


PAIRS = {"btc-up-or-down-5m": [("0xc53375ff94e96100f2b30a4b5775db35218d69a9",
                                "0x3048d65321be3497164cdfc2996f94f98a2e7537"),
                               ("0xc53375ff94e96100f2b30a4b5775db35218d69a9",
                                "0x0ca4e9d27ff826a109ecbf74754fb66b93f277a6"),
                               ("0xc53375ff94e96100f2b30a4b5775db35218d69a9",
                                "0x41e2e1ccf1e4940029af02259a31c6b89b9fa354")],
         "btc-up-or-down-15m": [("0x32ed2e546b187ca15e2841edc82b22c713cf8ec3",
                                 "0xb55fa1296e6ec55d0ce53d93b9237389f11764d4"),
                                ("0x32ed2e546b187ca15e2841edc82b22c713cf8ec3",
                                 "0xc2ad03f79ca3f3c17d8c7de2612ce0c89b7d40ed")]}


def main() -> None:
    s = pd.read_csv(OUT / "summary.csv")
    rate = s.groupby("wallet")["taker_rebate_rate"].first()
    rows, h2h = [], []
    for slug in FAMILIES:
        f, _ = build(slug)
        f = f[f["wallet"].isin(s.loc[s["series"] == slug, "wallet"])]
        r = robust(per_market(f, rate))
        r.insert(1, "series", slug)
        rows.append(r)
        h2h += [head_to_head(f, a, b) | {"series": slug} for a, b in PAIRS.get(slug, [])]
    s = s.merge(pd.concat(rows), on=["wallet", "series"], how="left")
    base = s["net"]
    s["net_at_50"] = base + 0.5 * s["fee"]
    s["net_at_0"] = base
    s.to_csv(OUT / "summary_stats.csv", index=False, float_format="%.6g")
    pd.DataFrame(h2h).to_csv(OUT / "head_to_head.csv", index=False, float_format="%.6g")
    print(pd.DataFrame(h2h).to_string())


if __name__ == "__main__":
    main()
