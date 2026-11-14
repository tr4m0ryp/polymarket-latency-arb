"""Second, coarser evaluation on the forensic fills (2026-10-07 to 10-09, block-time
resolution, every latency bot's fills; study/profit/extract.py).

    python3 -m research.strategy.eval.forensic

No book and no perp here, so rules are applied as SELECTION filters on taker buys that really
happened (at the incumbents' speed): an upper bound for a rule's edge, useful to check that the
selection logic generalises to a different, more volatile period. Train = the first half of the
window, test = the second half. Net = pnl - full taker fee (our 0% tier). The z-move uses the
fill's 3 s Binance move scaled by the settlement z-scale with sigma = the market's realized
1 s volatility (median absolute 1 s move of all fills in the market / 0.6745, a robust proxy).
Writes data/out/strategy/forensic.csv."""
from __future__ import annotations

import numpy as np
import pandas as pd

from .. import OUT, ROOT, fee

LEADERS = {"0xc53375ff94e96100f2b30a4b5775db35218d69a9": "A",
           "0x3048d65321be3497164cdfc2996f94f98a2e7537": "B"}


def frame() -> pd.DataFrame:
    d = pd.read_pickle(ROOT / "data" / "cache" / "latency_profit" / "btc-up-or-down-5m.pkl")
    d = d[(d["side"] == "BUY") & (d["taker"] == 1)].copy()
    d["d"] = np.sign(d["q"])
    d["net"] = d["pnl"] - d["fee"]
    sig = d.groupby("condition_id")["r1"].transform(lambda x: np.median(np.abs(x[x != 0])) / 0.6745
                                                    if (x != 0).any() else np.nan)
    tau = d["secs_to_end"].clip(lower=3)
    eff = np.where(tau >= 60, tau - 40, tau / 3)
    d["zmove"] = d["d"] * d["r3"] / (sig.clip(lower=0.03e-4) * np.sqrt(eff))
    d["move_bp"] = 1e4 * d["d"] * d["r3"]
    val = np.where(d["d"] > 0, d["fair"], 1 - d["fair"])
    d["fair_edge"] = val - d["price"] - fee(d["price"])
    mid_t = d["ts"].min() + (d["ts"].max() - d["ts"].min()) / 2
    d["split"] = np.where(d["ts"] < mid_t, "train", "test")
    d["who"] = d["wallet"].map(LEADERS).fillna("other")
    return d


RULES = {
    "all taker buys (any bot)": lambda d: d.index == d.index,
    "their fills: leader A": lambda d: d["who"] == "A",
    "their fills: leader B": lambda d: d["who"] == "B",
    "aligned 3 s move > 1 bp, price < 0.70": lambda d: (d["move_bp"] > 1) & (d["price"] < 0.70),
    "aligned z-move > 0.1": lambda d: d["zmove"] > 0.1,
    "aligned z-move > 0.2, price 0.05-0.95": lambda d: (d["zmove"] > 0.2) & d["price"].between(0.05, 0.95),
    "aligned z-move > 0.3, price 0.05-0.95": lambda d: (d["zmove"] > 0.3) & d["price"].between(0.05, 0.95),
    "spot-model fair edge > 0.03": lambda d: d["fair_edge"] > 0.03,
    "z-move > 0.2 and fair edge > 0": lambda d: (d["zmove"] > 0.2) & (d["fair_edge"] > 0),
}


def main() -> None:
    d = frame()
    days = {s: (g["ts"].max() - g["ts"].min()) / 86400 for s, g in d.groupby("split")}
    rows = []
    for name, rule in RULES.items():
        for s, g in d.groupby("split"):
            x = g[rule(g)]
            rows.append({"rule": name, "split": s, "fills_day": len(x) / days[s],
                         "usd_day": x["usd"].sum() / days[s], "net_day": x["net"].sum() / days[s],
                         "c_per_usd": 100 * x["net"].sum() / max(x["usd"].sum(), 1e-9),
                         "mo2_c": 100 * (x["mo2"] - x["fee"]).sum() / max(x["usd"].sum(), 1e-9),
                         "win": (x["pnl"] > 0).mean()})
    t = pd.DataFrame(rows)
    t.to_csv(OUT / "forensic.csv", index=False)
    print(t.round(2).to_string(index=False))


if __name__ == "__main__":
    main()
