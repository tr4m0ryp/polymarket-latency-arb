"""Per wallet x family profit decomposition of the latency wallets.

PnL identities used (YES frame, per fill, USD):
  gross   = q * (R - pi)                        hold-to-resolution trading PnL
  net     = gross - fee + maker_rebate          before the wallet-level taker
                                                rebate (added in rebates.py)
  gross   = q * (pi_prev - pi)                  price paid vs the last block
          + q * (pi_2s - pi_prev)               book repricing within 2 s
          + q * (R - pi_2s)                     residual (hold) value
Buckets: seconds left in the window, |BTC move| over the 10 s before the fill,
token side, token price, fill size, maker/taker."""
from __future__ import annotations

import numpy as np
import pandas as pd

SECS = [-np.inf, 0, 10, 30, 60, 120, 300, 900, 3600, 4 * 3600, np.inf]
SECS_LBL = ["after", "0-10", "10-30", "30-60", "60-120", "120-300", "300-900",
            "900-3600", "1h-4h", ">4h"]
MOVE_BP = [-0.01, 1, 2, 5, 10, np.inf]
MOVE_LBL = ["<1bp", "1-2bp", "2-5bp", "5-10bp", ">10bp"]
PRICE = [0, 0.1, 0.3, 0.5, 0.7, 0.9, 1.0001]
PRICE_LBL = ["0-.1", ".1-.3", ".3-.5", ".5-.7", ".7-.9", ".9-1"]
SIZE = [0, 5, 20, 100, 500, np.inf]
SIZE_LBL = ["<$5", "$5-20", "$20-100", "$100-500", ">$500"]


def add_dims(f: pd.DataFrame) -> pd.DataFrame:
    f = f.copy()
    f["net"] = f["pnl"] - f["fee"] + f["maker_rebate"]
    f["secs_left"] = pd.cut(f["secs_to_end"], SECS, labels=SECS_LBL, right=False)
    f["btc_move"] = pd.cut(f["r10"].abs() * 1e4, MOVE_BP, labels=MOVE_LBL)
    tok = np.where(f["outcome_index"] == 0, "Up", "Down")
    f["token_side"] = f["side"].str.lower() + "_" + tok
    f["tok_price"] = pd.cut(f["price"], PRICE, labels=PRICE_LBL, right=False)
    f["size_bkt"] = pd.cut(f["usd"], SIZE, labels=SIZE_LBL, right=False)
    f["role"] = np.where(f["taker"] == 1, "taker", "maker")
    pi2 = f["pi"] + np.where(f["q"] != 0, f["mo2"] / f["q"].where(f["q"] != 0, 1), 0)
    prev = f["pi_prev"].fillna(f["pi"])
    f["c_price"] = f["q"] * (prev - f["pi"])
    f["c_reprice"] = f["q"] * (pi2 - prev)
    f["c_hold"] = f["q"] * (f["R"] - pi2)
    f["c_model"] = f["q"] * (f["fair"] - f["pi"])
    return f


def _agg(g) -> pd.DataFrame:
    a = g.agg(usd=("usd", "sum"), fills=("usd", "size"), gross=("pnl", "sum"),
              fee=("fee", "sum"), maker_rebate=("maker_rebate", "sum"), net=("net", "sum"))
    u = a["usd"].clip(lower=1e-9)
    a["gross_per_usd"] = a["gross"] / u
    a["net_per_usd"] = a["net"] / u
    return a


def buckets(f: pd.DataFrame) -> pd.DataFrame:
    dims = ["secs_left", "btc_move", "token_side", "tok_price", "size_bkt", "role"]
    out = []
    for d in dims:
        a = _agg(f.groupby(["wallet", d], observed=True)).reset_index()
        a = a.rename(columns={d: "bucket"})
        a.insert(1, "dim", d)
        out.append(a)
    return pd.concat(out, ignore_index=True)


def summary(f: pd.DataFrame, mk: pd.DataFrame) -> pd.DataFrame:
    g = f.groupby("wallet")
    s = _agg(g)
    tk = f[f["taker"] == 1]
    gt = tk.groupby("wallet")
    tu = gt["usd"].sum().reindex(s.index).clip(lower=1e-9)
    s["taker_share"] = gt["usd"].sum().reindex(s.index).fillna(0) / s["usd"]
    s["taker_gross_per_usd"] = gt["pnl"].sum().reindex(s.index) / tu
    s["taker_fee_per_usd"] = gt["fee"].sum().reindex(s.index) / tu
    mu = f[f["taker"] == 0].groupby("wallet")
    s["maker_gross_per_usd"] = mu["pnl"].sum() / mu["usd"].sum().clip(lower=1e-9)
    for c in ["c_price", "c_reprice", "c_hold", "c_model"]:
        s[f"taker_{c[2:]}_per_usd"] = gt[c].sum().reindex(s.index) / tu
    s["taker_tok_price"] = (gt.apply(lambda x: np.average(x["price"], weights=x["usd"]),
                                     include_groups=False).reindex(s.index))
    s["n_markets"] = g["condition_id"].nunique()
    s["coverage"] = s["n_markets"] / len(mk)
    s["fills_per_market"] = s["fills"] / s["n_markets"]
    s["med_fill_usd"] = g["usd"].median()
    s["big_move_usd_share"] = (f[f["r10"].abs() * 1e4 >= 5].groupby("wallet")["usd"].sum()
                               .reindex(s.index).fillna(0) / s["usd"])
    s["last60s_usd_share"] = (f[f["secs_to_end"].between(0, 60)].groupby("wallet")["usd"]
                              .sum().reindex(s.index).fillna(0) / s["usd"])
    pm = f.groupby(["wallet", "condition_id"])["pnl"].sum()
    s["win_rate_mkts"] = (pm > 0).groupby(level=0).mean()
    return s.reset_index()
