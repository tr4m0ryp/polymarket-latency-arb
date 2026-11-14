"""Reverse-engineer the two 5m leaders' taker triggers.

    python3 study/trigger/reverse.py

One row per live market second. Features are what a bot could know before the second: Binance
moves over 1-10 s, spot-implied fair vs the last Polymarket print (gap), time left, and the bot's
own state (net position, last side, time since its last taker buy, the pair gain of buying each
side given its average costs). Labels: did the wallet take (buy) in that block, and which side.
Fits gradient boosting for 'fires?' and 'which side?', reports AUC / accuracy, permutation
importance and a depth-3 tree, plus simple single-rule baselines. Writes
data/out/latency/reverse.md."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.inspection import permutation_importance
from sklearn.metrics import roc_auc_score
from sklearn.tree import DecisionTreeClassifier, export_text

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from frame import ROOT, fill_frame, second_grid  # noqa: E402

SLUG = "btc-up-or-down-5m"
WALLETS = {"A": "0xc53375ff94e96100f2b30a4b5775db35218d69a9",
           "B": "0x3048d65321be3497164cdfc2996f94f98a2e7537"}
FEATS = ["r1", "r2", "r3", "r5", "r10", "gap", "book", "secs_left", "pos", "last_side",
         "since_last", "pair_up", "pair_dn", "book_chg2"]


def own_state(g: pd.DataFrame, fills: pd.DataFrame) -> pd.DataFrame:
    """Bot state before each second from its own fills (taker and maker) in that market."""
    out = []
    for cid, gg in g.groupby("condition_id", sort=False):
        ff = fills[fills["condition_id"] == cid].sort_values("ts")
        ts = gg["ts"].to_numpy()
        n = np.searchsorted(ff["ts"].to_numpy(), ts, side="left")  # fills strictly before ts
        q = ff["q"].to_numpy()
        up_sh = np.r_[0, np.cumsum(np.where(q > 0, q, 0))][n]
        dn_sh = np.r_[0, np.cumsum(np.where(q < 0, -q, 0))][n]
        up_c = np.r_[0, np.cumsum(np.where(q > 0, ff["usd"], 0))][n]
        dn_c = np.r_[0, np.cumsum(np.where(q < 0, ff["usd"], 0))][n]
        tk = ff[ff["taker"] == 1]
        m = np.searchsorted(tk["ts"].to_numpy(), ts, side="left")
        last_ts = np.r_[np.nan, tk["ts"].to_numpy()][m]
        last_side = np.r_[0, np.sign(tk["q"].to_numpy())][m]
        with np.errstate(invalid="ignore", divide="ignore"):
            avg_up, avg_dn = up_c / up_sh, dn_c / dn_sh
        book = gg["book"].to_numpy()
        out.append(pd.DataFrame({"pos": up_sh - dn_sh, "last_side": last_side,
                                 "since_last": ts - last_ts,
                                 "pair_up": 1 - avg_dn - book,       # buy Up now vs held Down
                                 "pair_dn": 1 - avg_up - (1 - book)},  # buy Down now vs held Up
                                index=gg.index))
    return pd.concat(out)


def build(name: str) -> pd.DataFrame:
    f, mk, sp = fill_frame(SLUG)
    w = WALLETS[name]
    g = second_grid(f, mk, sp, SLUG, {w})
    g = g[(g["ts"] >= g["start_ts"]) & (g["ts"] < g["end_ts"])].copy()
    ts = g["ts"].to_numpy(np.int64)
    now = sp.at(ts - 1)
    for k in (1, 2, 3, 5, 10):
        g[f"r{k}"] = 1e4 * np.log(now / sp.at(ts - 1 - k))
    g["secs_left"] = g["end_ts"] - g["ts"]
    g["book_chg2"] = g["book"] - g.groupby("condition_id")["book"].shift(2)
    g = g.join(own_state(g, f[f["wallet"] == w]))
    g["fire"] = (g["bot_flow"] != 0).astype(int)
    g["side"] = np.sign(g["bot_flow"]).astype(int)
    return g
