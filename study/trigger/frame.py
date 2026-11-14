"""Per-fill and per-second frames for the price-trigger study.

fill_frame adds, to features.family_frame, everything a bot could see at the
moment it fired (spot series end at S[ts-1], the book at the last print
strictly before ts):
  move_open_usd / move_open_bp   S[ts-1] - S[start_ts-1]   (raw spot vs window open)
  move_strike_bp                 S[ts-1] vs the settlement strike (60 s TWAP
                                 before open for 5m/15m, open candle otherwise)
  r5                             log move over the 5 s before the fill
  book                           last YES print before ts in the same market
  gap                            fair - book: spot-implied mispricing of the book
  edge                           sign(q) * (fair - pi): model value per share at
                                 the price actually paid (YES frame, so one
                                 formula covers Up buys, Down buys and sells)
second_grid builds one row per live market second (strike window included)
with Binance return, fair, book, gap and the bots' signed taker USD."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from features import TW, TWAP_FAMILIES, fair_up, family_frame  # noqa: E402
from spot import Spot  # noqa: E402

ROOT = HERE.parents[1]
WALLETS = ROOT / "data" / "out" / "latency" / "wallets.csv"


def bots(slug: str, cls: str = "latency_arb") -> list[str]:
    w = pd.read_csv(WALLETS, usecols=["wallet", "series", "latency_class", "pnl"])
    w = w[(w["series"] == slug) & (w["latency_class"] == cls)]
    return w.sort_values("pnl", ascending=False)["wallet"].tolist()


def _strike(sp: Spot, slug: str, start: np.ndarray) -> np.ndarray:
    if slug in TWAP_FAMILIES:
        return sp.mean(start - TW, start)
    return sp.at(start - 1)


def _book_before(f: pd.DataFrame) -> np.ndarray:
    """Last YES print in the same market with ts strictly below the fill's ts."""
    out = np.full(len(f), np.nan)
    ts_all, pi_all = f["ts"].to_numpy(), f["pi"].to_numpy()
    for _, idx in f.groupby("condition_id").indices.items():
        o = idx[np.argsort(ts_all[idx], kind="stable")]
        ts, pi = ts_all[o], pi_all[o]
        j = np.searchsorted(ts, ts, side="left") - 1
        ok = j >= 0
        out[o[ok]] = pi[j[ok]]
    return out


def fill_frame(slug: str) -> tuple[pd.DataFrame, pd.DataFrame, Spot]:
    f, mk = family_frame(slug)
    sp = Spot(int(mk["start_ts"].min()) - 3600, int(mk["end_ts"].max()) + 120)
    ts = f["ts"].to_numpy(np.int64)
    st = f["start_ts"].to_numpy(np.int64)
    now = sp.at(ts - 1)
    s_open = sp.at(st - 1)
    f["spot"] = now
    f["move_open_usd"] = now - s_open
    f["move_open_bp"] = 1e4 * np.log(now / s_open)
    f["move_strike_bp"] = 1e4 * np.log(now / _strike(sp, slug, st))
    f["r5"] = np.log(now / sp.at(ts - 6))
    f["vol300_bp"] = 1e4 * sp.vol(ts - 1)
    f["book"] = _book_before(f)
    f["gap"] = f["fair"] - f["book"]
    f["edge"] = np.sign(f["q"]) * (f["fair"] - f["pi"])
    f["secs_left"] = f["end_ts"].to_numpy(np.int64) - ts
    f["live"] = (ts >= st - (TW if slug in TWAP_FAMILIES else 0)) & (f["secs_left"] > 0)
    return f, mk, sp


def second_grid(f: pd.DataFrame, mk: pd.DataFrame, sp: Spot, slug: str,
                bot_set: set[str]) -> pd.DataFrame:
    """One row per (market, second) in [start - TW, end) for TWAP families,
    [start, end) otherwise. book = last print before the second."""
    pre = TW if slug in TWAP_FAMILIES else 0
    rows = []
    tk = f[(f["taker"] == 1) & f["wallet"].isin(bot_set)]
    flow = (np.sign(tk["q"]) * tk["usd"]).groupby([tk["condition_id"], tk["ts"]]).sum()
    for cid, m in mk.iterrows():
        s0, e0 = int(m["start_ts"]) - pre, int(m["end_ts"])
        t = np.arange(s0, e0, dtype=np.int64)
        g = pd.DataFrame({"condition_id": cid, "ts": t,
                          "start_ts": int(m["start_ts"]), "end_ts": e0})
        rows.append(g)
    g = pd.concat(rows, ignore_index=True)
    ts, st, en = (g[c].to_numpy(np.int64) for c in ("ts", "start_ts", "end_ts"))
    now = sp.at(ts - 1)
    g["ret1"] = np.log(now / sp.at(ts - 2))
    g["fair"] = fair_up(sp, slug, ts, st, en, now)
    # last print before each second, per market
    pr = f.sort_values("ts")
    book = np.full(len(g), np.nan)
    gi = g.groupby("condition_id").indices
    for cid, idx in pr.groupby("condition_id").indices.items():
        if cid not in gi:
            continue
        gidx = gi[cid]
        pts, ppi = pr["ts"].to_numpy()[idx], pr["pi"].to_numpy()[idx]
        j = np.searchsorted(pts, ts[gidx], side="left") - 1
        ok = j >= 0
        book[gidx[ok]] = ppi[j[ok]]
    g["book"] = book
    g["gap"] = g["fair"] - g["book"]
    key = pd.MultiIndex.from_arrays([g["condition_id"], g["ts"]])
    g["bot_flow"] = flow.reindex(key).fillna(0.0).to_numpy()
    return g
