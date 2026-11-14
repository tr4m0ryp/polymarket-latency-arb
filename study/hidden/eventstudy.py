"""Event study around the leaders' taker fills: the average signed path of every candidate
driver on a 10 ms grid from -3 s to +1 s of the fill (venue clocks), so the ordering of
perp, spot, Polymarket book and other takers' flow can be read directly.

    nice -n 10 python3 study/hidden/eventstudy.py

Signed = multiplied by the side bought (Up +1). Prices in bp relative to the value at -3 s; the
book in cents; flows in cumulative signed shares since -3 s. Subsets: all fills, no-move fills
(|spot 3 s move| < 0.2 bp), and burst openers (no fill of the same wallet in the prior 5 s).
Output data/out/hidden/eventstudy.csv (who, subset, series, offset_ms, mean, n)."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import series  # noqa: E402
from attrib import A, B, CACHE, ROOT  # noqa: E402
from features import flow  # noqa: E402

GRID = np.round(np.arange(-3.0, 1.0001, 0.01), 3)
OUT = ROOT / "data" / "out" / "hidden"


def paths(h: int, ev: pd.DataFrame, fills: pd.DataFrame) -> dict[str, np.ndarray]:
    d = series.load(h)
    s = series.build(d)
    tau, dd = ev["ts"].to_numpy(), ev["d"].to_numpy()
    q = tau[:, None] + GRID[None, :]
    out: dict[str, np.ndarray] = {}
    for name in ("spot_tr", "spot_mid", "perp_mid", "perp_micro"):
        if name in s:
            x = s[name].at(q)
            out[name] = dd[:, None] * 1e4 * np.log(x / x[:, :1])
    bm = np.full(q.shape, np.nan)
    fl = {k: np.full(q.shape, np.nan) for k in ("other", "A", "B")}
    for cid in ev["market"].unique():
        i = np.flatnonzero(ev["market"].to_numpy() == cid)
        bt = series.book_tops(d, cid, s["lag_clob"])
        bm[i] = 100 * (bt["bb"].at(q[i]) + bt["ba"].at(q[i])) / 2
        mf = fills[fills["market"] == cid]
        groups = {"other": mf[~mf["wallet"].isin([A, B])], "A": mf[mf["wallet"] == A],
                  "B": mf[mf["wallet"] == B]}
        for k, g in groups.items():
            ts = g["ts"].to_numpy()
            c = np.r_[0, np.cumsum((g["d"] * g["size"]).to_numpy())]
            fl[k][i] = c[np.searchsorted(ts, q[i], "left")] - c[np.searchsorted(ts, q[i][:, :1], "left")]
    out["book_mid"] = dd[:, None] * (bm - bm[:, :1])
    for k, v in fl.items():
        out[f"flow_{k}"] = dd[:, None] * v
    return out


def main() -> None:
    feat = pd.read_pickle(CACHE / "feat.pkl")
    fills = pd.read_pickle(CACHE / "fills_5m.pkl")
    feat["who"] = np.where(feat["wallet"] == A, "A", "B")
    feat = feat.sort_values("ts")
    prev = feat.groupby(["who", "market"])["ts"].shift(1)
    feat["opener"] = (feat["ts"] - prev).fillna(99) > 5
    feat["nomove"] = feat["spot_r3.0"].abs() < 0.2
    acc: dict = {}
    for h, ev in feat.groupby("hour"):
        p = paths(h, ev, fills)
        for who in ("A", "B"):
            for sub in ("all", "nomove", "opener", "nomove_opener"):
                m = (ev["who"] == who).to_numpy().copy()
                if "nomove" in sub:
                    m &= ev["nomove"].to_numpy()
                if "opener" in sub:
                    m &= ev["opener"].to_numpy()
                for k, v in p.items():
                    x = v[m]
                    key = (who, sub, k)
                    s0, n0 = acc.get(key, (0, 0))
                    acc[key] = (s0 + np.nansum(x, 0), n0 + np.sum(~np.isnan(x), 0))
        print("hour", h, flush=True)
    rows = [(w, sub, k, o, s_ / max(n_, 1), n_) for (w, sub, k), (sv, nv) in acc.items()
            for o, s_, n_ in zip((GRID * 1000).round().astype(int), sv, nv)]
    OUT.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows, columns=["who", "subset", "series", "offset_ms", "mean", "n"]).to_csv(
        OUT / "eventstudy.csv", index=False)


if __name__ == "__main__":
    main()
