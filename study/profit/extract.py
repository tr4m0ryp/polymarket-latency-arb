"""Per-fill cost and price-context columns for the latency wallets of one family.

Adds to features.family_frame (all fills of the family are needed for the
market-level pools, only latency wallets are kept afterwards):
  fee           taker fee in USDC, fee = C * 0.07 * p * (1 - p) (Gamma
                feeSchedule crypto_fees_v2: rate 0.07, exponent 1, takerOnly);
                p is the traded token's price. Makers pay nothing.
  maker_rebate  maker share of the market's rebate pool: pool = 20 % of the
                market's taker fees (rebateRate 0.2), split pro rata on the
                fee-equivalent C * 0.07 * p * (1 - p) of maker fills.
  pi_prev       taker VWAP of the previous block in the same market (YES
                frame): the price on screen before this fill printed.
  tok_price     price of the token actually traded (= price column).
  mkt_move      |log(S_end / S_open)| of the market's window on Binance 1 s.
Cached to data/cache/latency_profit/<slug>.pkl."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from features import family_frame  # noqa: E402
from spot import Spot  # noqa: E402

ROOT = HERE.parents[1]
CACHE = ROOT / "data" / "cache" / "latency_profit"
FEE_RATE, REBATE_RATE = 0.07, 0.20
KEEP = ["wallet", "condition_id", "ts", "start_ts", "end_ts", "secs_to_end", "t_rel",
        "taker", "q", "pi", "price", "side", "outcome_index", "size", "usd", "R", "pnl",
        "fee", "maker_rebate", "pi_prev", "mo2", "mo10", "mo60", "r1", "r3", "r10",
        "fair", "fair_stale", "mkt_move", "tx"]


def latency_wallets(slug: str) -> set[str]:
    w = pd.read_csv(ROOT / "data" / "out" / "latency" / "wallets.csv",
                    usecols=["wallet", "series", "latency_class"])
    # latency in ANY family: multi-family wallets need all their fees per day
    return set(w.loc[w["latency_class"] != "none", "wallet"])


def add_costs(f: pd.DataFrame) -> None:
    ppq = f["size"] * f["price"] * (1 - f["price"]) * FEE_RATE
    tk = f["taker"] == 1
    f["fee"] = np.where(tk, ppq, 0.0)
    feq = np.where(tk, 0.0, ppq)
    pool = REBATE_RATE * f.groupby("condition_id")["fee"].transform("sum")
    tot = pd.Series(feq, index=f.index).groupby(f["condition_id"]).transform("sum")
    f["maker_rebate"] = np.where(tot > 0, feq / tot.clip(lower=1e-12) * pool, 0.0)


def add_prev_price(f: pd.DataFrame) -> None:
    tk = f[f["taker"] == 1]
    w = tk["q"].abs()
    b = (tk.assign(pw=tk["pi"] * w, w=w).groupby(["condition_id", "ts"])[["pw", "w"]]
         .sum().reset_index())
    b["vwap"] = b["pw"] / b["w"]
    b["pi_prev"] = b.groupby("condition_id")["vwap"].shift(1)
    key = pd.MultiIndex.from_frame(f[["condition_id", "ts"]])
    f["pi_prev"] = b.set_index(["condition_id", "ts"])["pi_prev"].reindex(key).to_numpy()


def market_moves(mk: pd.DataFrame) -> pd.Series:
    sp = Spot(int(mk["start_ts"].min()) - 120, int(mk["end_ts"].max()) + 120)
    o, e = mk["start_ts"].to_numpy(np.int64), mk["end_ts"].to_numpy(np.int64)
    return pd.Series(np.abs(np.log(sp.at(e - 1) / sp.at(o - 1))), index=mk.index)


def build(slug: str, refresh: bool = False) -> tuple[pd.DataFrame, pd.DataFrame]:
    CACHE.mkdir(parents=True, exist_ok=True)
    pf, pm = CACHE / f"{slug}.pkl", CACHE / f"{slug}.markets.pkl"
    if pf.exists() and pm.exists() and not refresh:
        return pd.read_pickle(pf), pd.read_pickle(pm)
    f, mk = family_frame(slug)
    add_costs(f)
    add_prev_price(f)
    mk = mk.copy()
    mk["mkt_move"] = market_moves(mk)
    mk["taker_fees"] = f.groupby("condition_id")["fee"].sum()
    mk["taker_usd"] = f[f["taker"] == 1].groupby("condition_id")["usd"].sum()
    f["mkt_move"] = f["condition_id"].map(mk["mkt_move"])
    out = f.loc[f["wallet"].isin(latency_wallets(slug)), KEEP].reset_index(drop=True)
    out.to_pickle(pf)
    mk.to_pickle(pm)
    return out, mk
