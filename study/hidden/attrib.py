"""Attribute every live 5m taker print to its wallet: join the websocket last_trade_price
(ms venue stamp, receipt time) to the Data API taker fill (wallet) by transaction hash.

    python3 study/hidden/attrib.py

Output data/cache/hidden/fills_5m.pkl, one row per taker fill: ts (CLOB match time, s, ms
resolution), t (our receipt), block (Data API second, Polygon block time), wallet, market,
d (+1 = the taker gained Up exposure: bought Up or sold Down), price_up (Up-frame price of the
fill), size, buy (1 if the taker bought). Prints the match rate and block-time minus match-time."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "latency" / "leadlag"))
import load  # noqa: E402

CACHE = ROOT / "data" / "cache" / "hidden"
A = "0xc53375ff94e96100f2b30a4b5775db35218d69a9"
B = "0x3048d65321be3497164cdfc2996f94f98a2e7537"


def prints() -> pd.DataFrame:
    parts = []
    for p in sorted((CACHE / "prep").glob("*.pkl")):
        d = pd.read_pickle(p)
        if "prints" in d:
            parts.append(d["prints"])
    return pd.concat(parts, ignore_index=True).drop_duplicates("tx")


def build() -> pd.DataFrame:
    f = pd.read_pickle(CACHE / "taker_5m.pkl")
    pr = prints()
    mk = load.markets()
    up = set(mk[mk["fam"] == "5m"]["up"])
    j = f.merge(pr[["tx", "t", "ts", "asset", "side", "price"]], left_on="transactionHash",
                right_on="tx", how="inner", suffixes=("", "_ws"))
    is_up = j["asset"].isin(up).to_numpy()
    buy = (j["side"] == "BUY").to_numpy()
    out = pd.DataFrame({
        "ts": j["ts"], "t": j["t"], "block": j["timestamp"].astype(float), "wallet": j["proxyWallet"],
        "market": j["condition_id"], "d": np.where(is_up == buy, 1, -1),
        "price_up": np.where(is_up, j["price"], 1 - j["price"]), "size": j["size"],
        "buy": buy.astype(int), "tx": j["transactionHash"]})
    print(f"Data API taker fills {len(f)}, ws prints {len(pr)}, joined {len(out)}")
    in_win = f[f["condition_id"].isin(pr["market"].unique())]
    print(f"match rate on recorded markets: {len(out) / len(in_win):.3f} of fills, "
          f"{len(out) / len(pr):.3f} of prints")
    lag = out["block"] - out["ts"]
    print("block minus match time, s:", lag.describe().round(3).to_dict())
    return out.sort_values("ts").reset_index(drop=True)


if __name__ == "__main__":
    df = build()
    df.to_pickle(CACHE / "fills_5m.pkl")
    for name, w in (("A", A), ("B", B)):
        x = df[df["wallet"] == w]
        print(name, "fills", len(x), "buys", x["buy"].mean().round(3), "markets", x["market"].nunique())
