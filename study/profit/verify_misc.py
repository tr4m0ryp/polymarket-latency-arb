"""Verification of the remaining numeric claims in reports/latency-bot.md.

    python3 study/profit/verify_misc.py

Prints, per claim: Up/Down buy PnL of 5m latency_arb rows, last-fill timing,
15m trio clip sizes and taker shares, speed-PnL rank correlation with p and
bootstrap CI, the gross-vs-net r^2, profitability split by the mo2 gate, fee
and rebate totals, mo2 vs hold for long-horizon rows, and the 15m trio's
Binance-vs-tape disagreement and outcome skew."""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

from extract import ROOT, build

LAT = ROOT / "data" / "out" / "latency"
TRIO = ["0x32ed2e546b187ca15e2841edc82b22c713cf8ec3",
        "0x3725d52f3c252e8374999cc8617292ea2608ad88",
        "0xc2ad03f79ca3f3c17d8c7de2612ce0c89b7d40ed"]
FAM = "btc-up-or-down-"


def hdr(s: str) -> None:
    print(f"\n== {s}")


def up_down(s: pd.DataFrame) -> None:
    hdr("5m BUY PnL by outcome token (latency_arb)")
    f, mk = build(FAM + "5m")
    rows = s[(s["series"] == FAM + "5m") & (s["latency_class"] == "latency_arb")]
    b = f[(f["side"] == "BUY") & f["wallet"].isin(rows["wallet"])]
    t = b.groupby(["wallet", "outcome_index"])["pnl"].sum().unstack().round(0)
    t.columns = ["up", "down"]
    t["up_gt_down"] = t["up"] > t["down"]
    print(t.join(rows.set_index("wallet")["gross"].round(0)).sort_values("gross").to_string())
    r = f.groupby("condition_id")["R"].first()
    print("5m Up rate", r.mean().round(4), len(r))
    hdr("last fill secs_to_end per market (median, p10)")
    for w in ["0xc53375ff94e96100f2b30a4b5775db35218d69a9",
              "0x3048d65321be3497164cdfc2996f94f98a2e7537",
              "0x0ca4e9d27ff826a109ecbf74754fb66b93f277a6",
              "0xd84403efd50b49a1d8a7181627e00307e6ea5908"]:
        x = f[f["wallet"] == w].groupby("condition_id")["secs_to_end"].min()
        print(w, x.median(), x.quantile(0.1), f.loc[f["wallet"] == w, "secs_to_end"].quantile(0.01))


def trio() -> None:
    hdr("15m trio: clip sizes, taker share per family")
    for fam in ["5m", "15m", "hourly", "4h", "daily"]:
        f, _ = build(FAM + fam)
        for w in TRIO:
            x = f[f["wallet"] == w]
            if x.empty:
                continue
            ts = x.loc[x["taker"] == 1, "usd"].sum() / x["usd"].sum()
            vc = x["size"].round(2).value_counts(normalize=True).head(2)
            print(fam, w, "taker", round(ts, 3), "top sizes",
                  {k: round(v, 3) for k, v in vc.items()} if fam == "15m" else "")
    hdr("15m trio: Binance r3 vs tape disagreement, outcome skew")
    f, _ = build(FAM + "15m")
    r = f.groupby("condition_id").agg(R=("R", "first"), d=("start_ts", "first"))
    r["day"] = pd.to_datetime(r["d"], unit="s").dt.date
    print("15m Up rate", r["R"].mean().round(4), r.groupby("day")["R"].mean().round(3).to_dict())
    for w in TRIO + ["0x41e2e1ccf1e4940029af02259a31c6b89b9fa354"]:
        x = f[(f["wallet"] == w) & (f["taker"] == 1)].dropna(subset=["pi_prev"])
        tape = np.sign(x["pi"] - x["pi_prev"])
        dis = (np.sign(x["r3"]) != 0) & (tape != 0) & (np.sign(x["r3"]) != tape)
        y = x[dis]
        fb = np.sign(y["q"]) == np.sign(y["r3"])
        print(w, "disagree fills", len(y), "follow-binance share", round(fb.mean(), 3),
              "binance %/$", round(y[fb]["pnl"].sum() / y[fb]["usd"].sum(), 4),
              "tape %/$", round(y[~fb]["pnl"].sum() / y[~fb]["usd"].sum(), 4))
        a = f[f["wallet"] == w]
        if w in TRIO:
            b = a[a["side"] == "BUY"].groupby("outcome_index")["pnl"].sum().round(0).to_dict()
            pm = a.groupby("condition_id")["pnl"].sum().to_frame().join(r)
            print("   buy pnl up/down", b, "per-mkt pnl by R",
                  pm.groupby("R")["pnl"].mean().round(1).to_dict(),
                  "per-day", pm.groupby("day")["pnl"].sum().round(0).to_dict())


def ranks() -> None:
    hdr("speed-PnL rank correlation, 5m")
    p = pd.read_csv(LAT / "peers_rank.csv")
    p = p[p["series"] == FAM + "5m"]
    for name, x in [("arb+partial", p[p["latency_class"].str.startswith("latency_arb")]),
                    ("arb only", p[p["latency_class"] == "latency_arb"])]:
        rho, pv = stats.spearmanr(x["duel"], x["pnl"])
        rng = np.random.default_rng(0)
        bs = [stats.spearmanr(*x[["duel", "pnl"]].to_numpy()[rng.integers(0, len(x), len(x))].T)[0]
              for _ in range(2000)]
        print(name, len(x), round(rho, 3), "p", round(pv, 4),
              "95% CI", np.nanpercentile(bs, [2.5, 97.5]).round(2))


def summary(s: pd.DataFrame, w: pd.DataFrame) -> None:
    hdr("49 latency_arb rows: fees, r^2, mo2 gate")
    a = s[s["latency_class"] == "latency_arb"]
    print("rows", len(a), "gross", a["gross"].sum().round(0), "fee", a["fee"].sum().round(0),
          "taker rebate", a["taker_rebate_est"].sum().round(0),
          "maker rebate", a["maker_rebate"].sum().round(0), "net", a["net_after_rebate"].sum().round(0))
    fpu = a["fee"] / a["usd"]
    print("std gross/$", a["gross_per_usd"].std().round(4), "std fee/$", fpu.std().round(4),
          "r2 gross vs net", round(a["gross_per_usd"].corr(a["net_after_rebate_per_usd"]) ** 2, 3))
    for lab, x in [("arb+partial", w[w["latency_class"].str.startswith("latency_arb")]),
                   ("none", w[w["latency_class"] == "none"])]:
        for g, y in x.groupby(x["mo2"] > 0):
            print(lab, "mo2>0" if g else "mo2<=0", len(y), round((y["pnl"] > 0).mean(), 3))
    x = w[(w["wallet"] == "0x06dc51826bc524d9a83770e7de9dd7e005b04524") & (w["series"] == FAM + "daily")]
    print("0x06dc daily n_markets", x["n_markets"].tolist())


def long_horizon() -> None:
    hdr("long-horizon rows: mo2 vs hold, concentration")
    rows = [("daily", "0x06dc51826bc524d9a83770e7de9dd7e005b04524"),
            ("4h", "0xb55fa1296e6ec55d0ce53d93b9237389f11764d4"),
            ("4h", "0x576b0696fd5a9225d66fd9500fd98f5be10b0cab"),
            ("4h", "0x2ed94d1a460379292d2e3b46f2cf7d94b033f271"),
            ("4h", "0xeebde7a0e019a63e6b476eb425505b7b3e6eba30")]
    for fam, w in rows:
        f, _ = build(FAM + fam)
        x = f[f["wallet"] == w]
        tk = x[x["taker"] == 1]
        pm = x.groupby("condition_id")["pnl"].sum()
        byR = x.groupby("R")["pnl"].sum().round(0).to_dict()
        print(fam, w, "mo2", round(tk["mo2"].sum()), "hold", round((tk["pnl"] - tk["mo2"]).sum()),
              "maker", round(x.loc[x["taker"] == 0, "pnl"].sum()),
              "top5 share", round(pm.nlargest(5).sum() / pm.sum(), 3), "pnl by R", byR,
              "Up rate", round(f.groupby("condition_id")["R"].first().mean(), 3),
              "span", pd.to_datetime([x["ts"].min(), x["ts"].max()], unit="s").strftime("%m-%d %H:%M").tolist())


def main() -> None:
    s = pd.read_csv(LAT / "profit" / "summary.csv")
    w = pd.read_csv(LAT / "wallets.csv")
    up_down(s)
    trio()
    ranks()
    summary(s, w)
    long_horizon()


if __name__ == "__main__":
    main()
