"""Leaders' fills on 2026-10-13 14:00-20:00: taker share, price vs the touch, 10 s markout.

Taker fills = rows of the takerOnly feed; maker fills = the rest of the full feed (same
tx hash, asset, price, size). Markout c/$ for a BUY at p: (mid10 - p - fee) / p, fee =
0.07 p (1 - p) for takers at our 0% tier (and at their 50% rebate tier), 0 for makers.

    PYTHONPATH=. python3 -m latency.livehold.lstats   -> data/out/livehold/leaders.md"""
from __future__ import annotations

import numpy as np
import pandas as pd

from research.predict.report.md import md
from . import OUT
from .run import boot

KEY = ["transactionHash", "asset", "price", "size"]


def fills() -> pd.DataFrame:
    tr = pd.read_pickle(OUT / "leaders_trades.pkl")
    tr = tr[tr["side"] == "BUY"]
    tk = tr[tr["taker_only"]].drop_duplicates(KEY)
    al = tr[~tr["taker_only"]].drop_duplicates(KEY)
    al = al.merge(tk[KEY].assign(role="taker"), on=KEY, how="left").fillna({"role": "maker"})
    al = pd.concat([al, tk[~tk.set_index(KEY).index.isin(al.set_index(KEY).index)].assign(role="taker")])
    lb = pd.read_pickle(OUT / "leaders_rows.pkl").drop_duplicates(["tx", "asset"])
    df = al.merge(lb, left_on=["transactionHash", "asset"], right_on=["tx", "asset"], how="inner")
    p = df["price"]
    fee = np.where(df["role"] == "taker", 0.07 * p * (1 - p), 0.0)
    df["usd"] = p * df["size"]
    for name, f in (("0pct", fee), ("50pct", fee * 0.5)):
        df[f"pnl_{name}"] = df["size"] * (df["mid10"] - p - f)
    df["pnl"], df["cost"] = df["pnl_0pct"], df["usd"]
    df["mk10_c"] = df["pnl"] / df["cost"] * 100
    df["px_minus_ask250_c"] = (p - df["ba_250"]) * 100
    df["px_minus_ask1_c"] = (p - df["ba_1"]) * 100
    df["ask_move_c"] = (df["ba_1"] - df["ba_250"]) * 100
    return df.dropna(subset=["mid10"])


def main():
    df = fills()
    rng = np.random.default_rng(7)
    rows = []
    for (who, role), g in df.groupby(["who", "role"]):
        est, lo, hi = boot(g, rng)
        r50 = g["pnl_50pct"].sum() / g["cost"].sum() * 100
        rows.append({"who": who, "role": role, "fills": len(g), "usd": g["usd"].sum(),
                     "usd_share": g["usd"].sum() / df.loc[df["who"] == who, "usd"].sum(),
                     "mk10_c_0pct": est, "lo": lo, "hi": hi, "mk10_c_50pct": r50,
                     "med_px": g["price"].median(), "med_size": g["size"].median()})
    t1 = pd.DataFrame(rows)
    tk = df[df["role"] == "taker"]
    rows = []
    for who, g in tk.groupby("who"):
        q = lambda s: np.nanpercentile(s, [10, 50, 90]).round(1).tolist()
        rows.append({"who": who, "taker_fills": len(g),
                     "px - ask 250 ms before (c) p10/50/90": q(g["px_minus_ask250_c"]),
                     "px - ask 1 ms before (c) p10/50/90": q(g["px_minus_ask1_c"]),
                     "ask move in last 250 ms (c) p10/50/90": q(g["ask_move_c"]),
                     "share px > ask250": (g["px_minus_ask250_c"] > 0.5).mean()})
    t2 = pd.DataFrame(rows)
    # markout by how far above the 250 ms-earlier ask the leader paid
    tk = tk.assign(band=pd.cut(tk["px_minus_ask250_c"], [-100, 0.5, 2.5, 5.5, 100], labels=["<=0", "1-2", "3-5", ">5"]))
    rows = []
    for (who, band), g in tk.groupby(["who", "band"], observed=True):
        est, lo, hi = boot(g, rng)
        rows.append({"who": who, "paid_above_ask250_c": band, "fills": len(g), "mk10_c_0pct": est, "lo": lo, "hi": hi})
    t3 = pd.DataFrame(rows)
    txt = ["# Leaders on the live-run tape (2026-10-13 14:00-20:00 UTC)\n",
           f"fills joined to tape: {len(df)}\n", "## Role split and 10 s markout\n", md(t1, 2),
           "\n## Taker price vs the touch\n", md(t2, 2), "\n## Taker markout by price paid above the ask 250 ms earlier\n", md(t3, 2)]
    (OUT / "leaders.md").write_text("\n".join(txt) + "\n")
    print("\n".join(txt))


if __name__ == "__main__":
    main()
