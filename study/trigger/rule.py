"""What the bots' direction and timing respond to.

  feature_accuracy  USD share of a wallet's live taker fills whose side
                    matches the sign of each candidate trigger
  lag_accuracy      the same against single Binance seconds j s before the
                    fill: which second's move the side follows
  fire_curve        per live second u, the 2 s Binance move m = log S[u-1] / S[u-3]
                    (known at u); fire = the wallet takes in [u+1, u+3].
                    Fire rate and direction accuracy by |m| bin
  gap_curve         at |m| >= 2 bp, fire rate by how far the book lags fair
                    in the move's direction (book staleness)"""
from __future__ import annotations

import numpy as np
import pandas as pd

M_BINS = [0, 0.25, 0.5, 1, 2, 3, 5, 8, 1e9]
GAP_BINS = [-1, -0.02, 0, 0.02, 0.05, 0.1, 1]


def _acc(s: np.ndarray, v: np.ndarray, u: np.ndarray) -> float:
    v = np.sign(v)
    m = (v != 0) & np.isfinite(v)
    return float(((s[m] == v[m]) * u[m]).sum() / u[m].sum()) if m.any() else np.nan


def feature_accuracy(tk: pd.DataFrame, who: dict[str, pd.Series]) -> pd.DataFrame:
    feats = {"r1": "r1", "r3": "r3", "r5": "r5", "r10": "r10", "r30": "r30",
             "move_since_open": "move_open_bp", "move_vs_strike": "move_strike_bp"}
    rows = []
    for name, sel in who.items():
        x = tk[sel]
        s, u = np.sign(x["q"]).to_numpy(), x["usd"].to_numpy()
        r = {"wallet": name}
        for k, c in feats.items():
            r[k] = _acc(s, x[c].to_numpy(), u)
        r["fair_gt_book"] = _acc(s, (x["fair"] - x["book"]).to_numpy(), u)
        r["fair_gt_paid"] = _acc(s, (x["fair"] - x["pi"]).to_numpy(), u)
        r["fresh10"] = _acc(s, (x["fair"] - x["fair_stale"]).to_numpy(), u)
        rows.append(r)
    return pd.DataFrame(rows)


def lag_accuracy(tk: pd.DataFrame, who: dict[str, pd.Series], sp) -> pd.DataFrame:
    ts = tk["ts"].to_numpy(np.int64)
    out = {}
    for name, sel in who.items():
        m = sel.to_numpy()
        s, u = np.sign(tk["q"].to_numpy()[m]), tk["usd"].to_numpy()[m]
        out[name] = [_acc(s, np.log(sp.at(ts[m] - j) / sp.at(ts[m] - j - 1)), u) for j in range(0, 9)]
    return pd.DataFrame(out, index=pd.Index(range(0, 9), name="second_before_fill"))


def _fires(g: pd.DataFrame, tk: pd.DataFrame) -> np.ndarray:
    fl = (np.sign(tk["q"]) * tk["usd"]).groupby([tk["condition_id"], tk["ts"]]).sum()
    tot = np.zeros(len(g))
    for d in (1, 2, 3):
        key = pd.MultiIndex.from_arrays([g["condition_id"], g["ts"] + d])
        tot += fl.reindex(key).fillna(0.0).to_numpy()
    return tot


def fire_curve(g: pd.DataFrame, sp, tk: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    ts = g["ts"].to_numpy(np.int64)
    m = 1e4 * np.log(sp.at(ts - 1) / sp.at(ts - 3))
    y = _fires(g, tk)
    ok = (ts < g["end_ts"].to_numpy() - 3) & g["book"].notna().to_numpy()
    d = pd.DataFrame({"m": np.abs(m), "fire": y != 0, "hit": np.sign(y) == np.sign(m),
                      "gap_al": np.sign(m) * g["gap"].to_numpy()})[ok]
    d["m_bin"] = pd.cut(d["m"], M_BINS, right=False)
    fc = d.groupby("m_bin", observed=True).agg(seconds=("fire", "size"), fire_rate=("fire", "mean"))
    fc["dir_accuracy"] = d[d["fire"] & (d["m"] > 0)].groupby("m_bin", observed=True)["hit"].mean()
    big = d[d["m"] >= 2].copy()
    big["gap_bin"] = pd.cut(big["gap_al"], GAP_BINS)
    gc = big.groupby("gap_bin", observed=True).agg(seconds=("fire", "size"), fire_rate=("fire", "mean"))
    gc["dir_accuracy"] = big[big["fire"]].groupby("gap_bin", observed=True)["hit"].mean()
    return fc.reset_index(), gc.reset_index()
