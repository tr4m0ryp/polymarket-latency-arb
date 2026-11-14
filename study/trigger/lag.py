"""How fast bots fire after a Binance move.

Lag convention: ret[t] = log(S[t] / S[t-1]) is the move inside second t
(S[t] = Binance close of [t, t+1)), so it is fully known at t + 1. A lag of k
pairs that move with fills whose Polygon block timestamp is t + k.
  xcorr        corr(signed taker USD per second at t + k, ret[t]) for one
               wallet, all bots, all other takers, and the YES last-print change
  event_study  BTC jumps (|log S[t] / S[t-2]| >= JUMP_BP) inside a live window;
               mean jump-aligned bot USD, other-taker USD and book change at
               t + k, plus the delay to the first aligned bot fill"""
from __future__ import annotations

import numpy as np
import pandas as pd

LAGS = range(-5, 16)
JUMP_BP = 3.0


def _per_second(x: pd.DataFrame, T: np.ndarray) -> np.ndarray:
    s = (np.sign(x["q"]) * x["usd"]).groupby(x["ts"]).sum()
    return s.reindex(T).fillna(0.0).to_numpy()


def _corr(y: np.ndarray, r: np.ndarray, k: int) -> float:
    if k >= 0:
        a, b = y[k:], r[:len(r) - k]
    else:
        a, b = y[:k], r[-k:]
    return float(np.corrcoef(a, b)[0, 1])


def _book_change(g: pd.DataFrame, T: np.ndarray) -> np.ndarray:
    """Per-second change of the live market's last print (summed if markets overlap)."""
    g = g.sort_values(["condition_id", "ts"])
    db = g.groupby("condition_id")["book"].diff().fillna(0.0)
    live = g["ts"] >= g["start_ts"]
    return db[live].groupby(g.loc[live, "ts"]).sum().reindex(T).fillna(0.0).to_numpy()


def series(f: pd.DataFrame, g: pd.DataFrame, sp, bots: list[str], top: list[str]):
    t0, t1 = int(g["ts"].min()), int(g["ts"].max()) + 1
    T = np.arange(t0, t1)
    ret = np.nan_to_num(np.log(sp.at(T) / sp.at(T - 1)))
    tk = f[(f["taker"] == 1) & f["live"]]
    ys = {"all_bots": _per_second(tk[tk["wallet"].isin(bots)], T),
          "other_takers": _per_second(tk[~tk["wallet"].isin(bots)], T)}
    for w in top:
        ys[w] = _per_second(tk[tk["wallet"] == w], T)
    ys["book_last_print"] = _book_change(g, T)
    return T, ret, ys


def xcorr(ret: np.ndarray, ys: dict) -> pd.DataFrame:
    return pd.DataFrame({n: [_corr(y, ret, k) for k in LAGS] for n, y in ys.items()},
                        index=pd.Index(list(LAGS), name="lag_s"))


def event_study(T: np.ndarray, sp, ys: dict, g: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    jump = 1e4 * np.nan_to_num(np.log(sp.at(T) / sp.at(T - 2)))
    live = np.zeros(len(T), bool)
    for s, e in g.groupby("condition_id")[["start_ts", "end_ts"]].first().itertuples(index=False):
        live[max(s - T[0], 0):max(e - 20 - T[0], 0)] = True  # skip the last 20 s
    ev = np.where(live & (np.abs(jump) >= JUMP_BP))[0]
    # keep only the first second of a jump cluster
    ev = ev[np.r_[True, np.diff(ev) > 5]]
    ev = ev[(ev >= 10) & (ev < len(T) - 20)]
    d = np.sign(jump[ev])
    out = {}
    for n in ("all_bots", "other_takers", "book_last_print"):
        y = ys[n]
        out[n] = [float(np.mean(d * y[ev + k])) for k in LAGS]
    tab = pd.DataFrame(out, index=pd.Index(list(LAGS), name="lag_s"))
    # delay to first aligned bot fill within 15 s
    yb = ys["all_bots"]
    first = []
    for i, s in zip(ev, d):
        hit = np.where(s * yb[i:i + 16] > 0)[0]
        first.append(hit[0] if len(hit) else np.nan)
    first = np.array(first, float)
    # baseline: same statistic at random live seconds with a random side
    rng = np.random.default_rng(0)
    rs = rng.choice(np.where(live[:len(T) - 20])[0], size=len(ev))
    rd = rng.choice([-1.0, 1.0], size=len(ev))
    base = np.array([np.any(s * yb[i:i + 7] > 0) for i, s in zip(rs, rd)], float)
    stats = {"n_events": int(len(ev)), "jump_bp_med": float(np.median(np.abs(jump[ev]))),
             "hit_within_6s": float(np.mean(first <= 6)),
             "hit_within_6s_random": float(base.mean()),
             "first_fill_lag_median": float(np.nanmedian(first)),
             "first_fill_lag_p25": float(np.nanpercentile(first, 25)),
             "first_fill_lag_p75": float(np.nanpercentile(first, 75))}
    return tab, stats
