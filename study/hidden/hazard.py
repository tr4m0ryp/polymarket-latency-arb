"""When do the 5m leaders fire? A 50 ms grid over every recorded 5m market (from 5 s after the
open to 30 s before the close, hours with perp data); label = the leader has a taker fill in
the bin. Features are side-free magnitudes known at the bin.

    nice -n 10 python3 study/hidden/hazard.py

Groups: state (price level, spread, time left, own cadence), forensic spot (|1-10 s spot move|),
Binance book trigger (|perp / spot micro, mid, imbalance, flow| in the trigger window ~0.21-0.33 s
before, plus pre/post windows), Polymarket flow (other takers, book move). Gradient boosting,
train first 2/3 of the hours, test the rest. Writes data/out/hidden/hazard.md and caches the grid
in data/cache/hidden/grid.pkl."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1] / "latency" / "leadlag"))
import load  # noqa: E402
import series  # noqa: E402
import window  # noqa: E402
from attrib import A, B, CACHE, ROOT  # noqa: E402
from features import flow  # noqa: E402

DT = 0.05
STATE = ["fav", "spread", "secs_left", "since_A", "since_B", "n5_A", "n5_B"]
FORENSIC = ["abs_r1", "abs_r2", "abs_r3", "abs_r5", "abs_r10"]
POLY = ["abs_book1", "abs_flow05", "n_prints05"]


def market_grid(m, d, s, fills) -> pd.DataFrame:
    t = np.arange(m.start + 5, m.end - 30, DT)
    q = t + DT / 2
    one = np.ones_like(q)
    f = {k: np.abs(v) for k, v in window.binance(s, q, one).items()}
    for k in (1, 2, 3, 5, 10):
        f[f"abs_r{k}"] = np.abs(1e4 * np.log(s["spot_tr"].at(np.floor(q) - 1) / s["spot_tr"].at(np.floor(q) - 1 - k)))
    bt = series.book_tops(d, m.condition_id, s["lag_clob"])
    mid = (bt["bb"].at(t - DT) + bt["ba"].at(t - DT)) / 2
    f["fav"], f["spread"] = np.abs(mid - 0.5), bt["ba"].at(t - DT) - bt["bb"].at(t - DT)
    f["abs_book1"] = np.abs(mid - (bt["bb"].at(t - 1) + bt["ba"].at(t - 1)) / 2)
    f["secs_left"] = m.end - t
    mf = fills[fills["market"] == m.condition_id]
    oth = mf[~mf["wallet"].isin([A, B])]
    f["abs_flow05"] = np.abs(flow(oth, t, 0.5))
    ots = oth["ts"].to_numpy()
    f["n_prints05"] = np.searchsorted(ots, t) - np.searchsorted(ots, t - 0.5)
    for name, w in (("A", A), ("B", B)):
        ts = mf.loc[mf["wallet"] == w, "ts"].to_numpy()
        i = np.searchsorted(ts, t, "left")
        f[f"since_{name}"] = np.minimum(t - np.r_[-np.inf, ts][i], 999.0)
        f[f"n5_{name}"] = i - np.searchsorted(ts, t - 5, "left")
        f[f"y_{name}"] = (np.searchsorted(ts, t + DT, "left") - i > 0).astype(np.int8)
    return pd.DataFrame(f).astype(np.float32).assign(t=t, market=m.condition_id)


def build() -> pd.DataFrame:
    fills = pd.read_pickle(CACHE / "fills_5m.pkl")
    fills = fills[fills["buy"] == 1]
    mk = load.markets()
    mk = mk[mk["fam"] == "5m"]
    hours = sorted(int(p.stem) for p in (CACHE / "prep").glob("*.pkl"))
    parts = []
    for h in hours:
        sub = mk[(mk["start"] + 5) // 3600 == h]
        if not len(sub):
            continue
        d = series.load(h + 1) if (h + 1) in hours else series.load(h)
        s = series.build(d)
        if "perp_micro" not in s:
            continue
        for m in sub.itertuples():
            if m.condition_id in set(fills["market"]):
                parts.append(market_grid(m, d, s, fills))
        print("hour", h, flush=True)
    g = pd.concat(parts, ignore_index=True)
    g.to_pickle(CACHE / "grid.pkl")
    return g


def main() -> None:
    p = CACHE / "grid.pkl"
    g = pd.read_pickle(p) if p.exists() else build()
    binance = ("perp_micro", "perp_mid", "perp_imb", "spot_")  # recorded in every hour (no perp trades)
    trig = [c for c in g.columns if c.startswith(binance)]
    hour = (g["t"] // 3600).astype(int)
    hrs = sorted(hour.unique())
    tr = (hour < hrs[int(len(hrs) * 2 / 3)]).to_numpy()
    groups = {"state": STATE, "state + forensic spot": STATE + FORENSIC,
              "state + perp book": STATE + [c for c in trig if c.startswith("perp")],
              "state + spot book": STATE + [c for c in trig if c.startswith("spot")],
              "state + Binance book trigger": STATE + trig,
              "state + Polymarket flow": STATE + POLY,
              "state + forensic + Binance book + Polymarket": STATE + FORENSIC + trig + POLY,
              "Binance book trigger alone": trig}
    lines = [f"# When do they fire? 50 ms bins: {len(g):,} (test {int((~tr).sum()):,})\n",
             "| features | AUC A | A fills in top-decile bins | AUC B | B fills in top decile |",
             "|---|---|---|---|---|"]
    for name, cols in groups.items():
        row = []
        for who in "AB":
            y = g[f"y_{who}"].to_numpy()
            peer = "B" if who == "A" else "A"  # own cadence is state; the peer's fills are not
            X = g[[c for c in cols if not c.endswith(f"_{peer}")]]
            clf = HistGradientBoostingClassifier(max_iter=300, learning_rate=0.05, max_leaf_nodes=31,
                                                 random_state=0).fit(X[tr], y[tr])
            pr = clf.predict_proba(X[~tr])[:, 1]
            top = pr >= np.quantile(pr, 0.9)
            row.append(f"{roc_auc_score(y[~tr], pr):.3f} | {y[~tr][top].sum() / y[~tr].sum():.2f}")
        lines.append(f"| {name} | {row[0]} | {row[1]} |")
    for who in "AB":
        y = g[f"y_{who}"]
        lines.append(f"\nbase rate {who}: {y.mean():.4f} per 50 ms bin")
    out = ROOT / "data" / "out" / "hidden" / "hazard.md"
    out.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
