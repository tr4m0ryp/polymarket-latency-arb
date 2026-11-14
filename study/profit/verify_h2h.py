"""Verification of the 5m head-to-head claims in reports/latency-bot.md.

    python3 study/profit/verify_h2h.py

Splits each leader's 5m net PnL into shared same-block taker flow, solo taker
flow and maker flow; splits taker gross into the 2 s markout (mo2) and the
hold-to-resolution residual (pnl - mo2); prices Up+Down pairs per wallet; and
writes the block-size bucket table. Outputs under data/out/latency/profit/:
  h2h_flows.csv      flow x wallet: usd, gross, mo2, hold, fee_net, net
  h2h_blocks.csv     block-USD bucket x wallet: usd, gross, gross_per_usd
  h2h_pairs.csv      per wallet: share-weighted Up+Down pair cost, pair PnL"""
from __future__ import annotations

import numpy as np
import pandas as pd

from extract import ROOT, build

OUT = ROOT / "data" / "out" / "latency" / "profit"
A = "0xc53375ff94e96100f2b30a4b5775db35218d69a9"
B = "0x3048d65321be3497164cdfc2996f94f98a2e7537"
SLUG = "btc-up-or-down-5m"
BKT = [0, 10, 25, 50, 100, 1e9]


def rebate_rate(w: str) -> float:
    s = pd.read_csv(OUT / "summary.csv")
    r = s.loc[(s["wallet"] == w) & (s["series"] == SLUG), "taker_rebate_rate"]
    return float(min(r.iloc[0], 0.5))


def flows(f: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    f = f[f["wallet"].isin([A, B])].copy()
    rate = {w: rebate_rate(w) for w in (A, B)}
    f["fee_net"] = f["fee"] * (1 - f["wallet"].map(rate)) - f["maker_rebate"]
    f["hold"] = np.where(f["taker"] == 1, f["pnl"] - f["mo2"], 0.0)
    f["mo2t"] = np.where(f["taker"] == 1, f["mo2"], 0.0)
    f["d"] = np.sign(f["q"])
    key = ["condition_id", "ts", "d"]
    tk = f[f["taker"] == 1]
    ka = set(map(tuple, tk.loc[tk["wallet"] == A, key].to_numpy()))
    kb = set(map(tuple, tk.loc[tk["wallet"] == B, key].to_numpy()))
    shared = ka & kb
    kk = list(map(tuple, f[key].to_numpy()))
    f["flow"] = np.where(f["taker"] == 0, "maker",
                         np.where([k in shared for k in kk], "shared", "solo"))
    g = f.groupby(["flow", "wallet"]).agg(usd=("usd", "sum"), gross=("pnl", "sum"),
                                          mo2=("mo2t", "sum"), hold=("hold", "sum"),
                                          fee_net=("fee_net", "sum"))
    g["net"] = g["gross"] - g["fee_net"]
    g["gross_per_usd"] = g["gross"] / g["usd"]
    return g.reset_index(), f


def hold_t(f: pd.DataFrame) -> dict:
    sh = f[f["flow"] == "shared"]
    pm = sh.groupby(["condition_id", "wallet"])["hold"].sum().unstack("wallet").fillna(0)
    d = pm[A] - pm[B]
    return {"n_mkts": len(d), "hold_diff_sum": d.sum(),
            "t": d.mean() / (d.std(ddof=1) / np.sqrt(len(d)))}


def blocks(f: pd.DataFrame) -> pd.DataFrame:
    tk = f[f["taker"] == 1]
    b = tk.groupby(["wallet", "condition_id", "ts", "d"]).agg(usd=("usd", "sum"),
                                                              gross=("pnl", "sum"))
    b["bkt"] = pd.cut(b["usd"], BKT, right=False,
                      labels=["<10", "10-25", "25-50", "50-100", ">=100"])
    o = b.groupby(["wallet", "bkt"], observed=True)[["usd", "gross"]].sum()
    o["gross_per_usd"] = o["gross"] / o["usd"]
    return o.reset_index()


def pairs(f: pd.DataFrame, wallets: list[str]) -> pd.DataFrame:
    rows = []
    buy = f[(f["side"] == "BUY") & f["wallet"].isin(wallets)]
    for w, x in buy.groupby("wallet"):
        g = x.groupby(["condition_id", "outcome_index"]).agg(sh=("size", "sum"),
                                                             usd=("usd", "sum"))
        g = g.unstack("outcome_index").dropna()
        if g.empty:
            continue
        n = np.minimum(g[("sh", 0)], g[("sh", 1)])
        cost = g[("usd", 0)] / g[("sh", 0)] + g[("usd", 1)] / g[("sh", 1)]
        rows.append({"wallet": w, "mkts": len(g), "pair_shares": n.sum(),
                     "pair_cost_w": (cost * n).sum() / n.sum(),
                     "pair_pnl": ((1 - cost) * n).sum()})
    return pd.DataFrame(rows)


def main() -> None:
    f, _ = build(SLUG)
    g, ff = flows(f)
    g.to_csv(OUT / "h2h_flows.csv", index=False)
    print(g.round(4).to_string())
    print("hold diff on shared (A-B) per market:", hold_t(ff))
    tot = ff.groupby("wallet").agg(mo2=("mo2t", "sum"), hold=("hold", "sum"))
    print(tot.round(0))
    bl = blocks(ff)
    bl.to_csv(OUT / "h2h_blocks.csv", index=False)
    print(bl.round(4).to_string())
    pr = pairs(f, [A, B])
    pr.to_csv(OUT / "h2h_pairs.csv", index=False)
    print(pr.round(4).to_string())


if __name__ == "__main__":
    main()
