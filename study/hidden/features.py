"""Per-fill features at millisecond resolution for the two 5m leaders' taker fills.

    nice -n 10 python3 study/hidden/features.py

For each taker fill at venue time tau (CLOB match stamp) and side d (+1 Up, -1 Down):
  spot_r{w}, perp_r{w}, micro_r{w}, chain_r{w}: signed move d * 1e4 * ln(x(tau) / x(tau - w)) bp,
      x = Binance spot trade price, perp bookTicker mid / microprice, Chainlink.
  spotL_r{w}, perpL_r{w}: the same move ending L = 0.2 s before tau (what a 200 ms bot saw).
  book_r{w}: signed change of the Up-book mid over [tau - w, tau - 50 ms], cents.
  flow{w}_other / _A / _B: signed taker shares of everyone else / of each leader in
      [tau - w, tau - 50 ms]; flow0_* the same in the last 50 ms.
  <feed>_<window>: window.binance (perp/spot micro, mid, taker flow in the trigger window).
  blk_r3: the forensic study's feature (block-time second, 1 s closes over [blk - 4, blk - 1]).
  mid, spread, bas_hit (size at the level hit), secs_left, gap_fair (spot-implied P(Up) - mid).
Output data/cache/hidden/feat.pkl (one row per leader fill; side, wallet, hour)."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.special import ndtr

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1] / "latency" / "leadlag"))
import load  # noqa: E402
import series  # noqa: E402
import window  # noqa: E402
from attrib import A, B, CACHE  # noqa: E402

WINS = (0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 3.0, 5.0, 10.0)
LAG = 0.2
EPS = 0.05  # the fill's own book update is stamped up to ~30 ms before its print: read state before


def signed_move(st: series.Step, tau, d, w, lag=0.0) -> np.ndarray:
    return d * 1e4 * np.log(st.at(tau - lag) / st.at(tau - lag - w))


def flow(fl: pd.DataFrame, tau, w) -> np.ndarray:
    """Up-direction taker shares in [tau - w, tau) from fills fl (sorted by ts)."""
    ts = fl["ts"].to_numpy()
    c = np.r_[0, np.cumsum((fl["d"] * fl["size"]).to_numpy())]
    return c[np.searchsorted(ts, tau, "left")] - c[np.searchsorted(ts, tau - w, "left")]


def hour_feats(h: int, fills: pd.DataFrame, mk: pd.DataFrame) -> pd.DataFrame:
    lead = fills[fills["wallet"].isin([A, B]) & (fills["buy"] == 1)
                 & (fills["ts"] // 3600 == h)].copy()
    if not len(lead):
        return pd.DataFrame()
    d = series.load(h)
    s = series.build(d)
    out = []
    for cid, g in lead.groupby("market"):
        m = mk.loc[cid]
        tau, dd = g["ts"].to_numpy(), g["d"].to_numpy()
        f: dict = {}
        for w in WINS:
            f[f"spot_r{w}"] = signed_move(s["spot_tr"], tau, dd, w)
            f[f"spotL_r{w}"] = signed_move(s["spot_tr"], tau, dd, w, LAG)
            f[f"spotbk_r{w}"] = signed_move(s["spot_mid"], tau, dd, w)
            if "perp_mid" in s:
                f[f"perp_r{w}"] = signed_move(s["perp_mid"], tau, dd, w)
                f[f"perpL_r{w}"] = signed_move(s["perp_mid"], tau, dd, w, LAG)
                f[f"micro_r{w}"] = signed_move(s["perp_micro"], tau, dd, w)
            if "chain" in s:
                f[f"chain_r{w}"] = signed_move(s["chain"], tau, dd, w)
        f.update(window.binance(s, tau, dd))
        bt = series.book_tops(d, cid, s["lag_clob"])
        pre = tau - EPS
        bb, ba = bt["bb"].at(pre), bt["ba"].at(pre)
        mid = (bb + ba) / 2
        f["mid"], f["spread"] = mid, ba - bb
        f["size_top"] = np.where(dd > 0, bt["bas"].at(pre), bt["bbs"].at(pre))
        for w in WINS:
            past = (bt["bb"].at(pre - w) + bt["ba"].at(pre - w)) / 2
            f[f"book_r{w}"] = dd * 100 * (mid - past)
        mf = fills[fills["market"] == cid]
        other = mf[~mf["wallet"].isin([A, B])]
        groups = {"other": other, "A": mf[mf["wallet"] == A], "B": mf[mf["wallet"] == B]}
        for name, gg in groups.items():
            f[f"flow0_{name}"] = dd * flow(gg, tau, EPS)
            for w in (0.1, 0.25, 0.5, 1.0, 3.0):
                f[f"flow{w}_{name}"] = dd * flow(gg, pre, w)
        blk = np.floor(g["block"].to_numpy())
        f["blk_r3"] = dd * 1e4 * np.log(s["spot_tr"].at(blk - 1) / s["spot_tr"].at(blk - 4))
        f["secs_left"] = m["end"] - tau
        if "chain" in s:
            k = s["chain"].at(np.array([m["start"] + 0.001]))[0]
            spot = s["spot_tr"].at(tau)
            px = s["spot_tr"].at(np.arange(tau.min() - 300, tau.min(), 1.0))
            sig = np.nanstd(np.diff(np.log(px[~np.isnan(px)])))
            basis = np.nanmedian(s["chain"].at(tau) - spot)
            fair = ndtr(np.log((spot + basis) / k) / (sig * np.sqrt(np.maximum(m["end"] - tau, 5.0))))
            f["gap_fair"] = dd * (fair - mid)
        out.append(pd.DataFrame(f, index=g.index))
    feat = pd.concat(out)
    return lead.join(feat).assign(hour=h, lag_spot=s["lag_spot"], lag_clob=s["lag_clob"],
                                  lag_perp=s.get("lag_perp", np.nan))


def main() -> None:
    fills = pd.read_pickle(CACHE / "fills_5m.pkl")
    mk = load.markets()
    mk = mk[mk["fam"] == "5m"].set_index("condition_id")
    hours = sorted(int(p.stem) for p in (CACHE / "prep").glob("*.pkl"))
    parts = []
    for h in hours:
        x = hour_feats(h, fills, mk)
        if len(x):
            parts.append(x)
            print(h, len(x), flush=True)
    pd.concat(parts).copy().to_pickle(CACHE / "feat.pkl")


if __name__ == "__main__":
    main()
