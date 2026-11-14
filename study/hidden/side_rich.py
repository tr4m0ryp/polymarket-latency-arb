"""Variants for the unexplained side residual (reports/hidden-trigger.md, 'What would have to be
true'): (1) fine windows of perp and spot microprice and imbalance changes from 0 to 2.5 s before
the print plus imbalance levels (decayed memory, learned weights); (2) per-fill event anchoring:
the sign of the largest 20 ms microprice step within 0.15-0.45 s before the print; (3) pricing:
d * (perp-implied fair change - Up-book mid change) over H s ending at send time (print - 0.27 s),
fair change = phi(z) / (sigma sqrt(tau)) * d ln(perp microprice), z from the book mid.

    OMP_NUM_THREADS=2 nice -n 10 python3 study/hidden/side_rich.py

Held out by time on no-move fills as in side.py. Prints AUC / accuracy."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import norm
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import series  # noqa: E402
from attrib import A, CACHE  # noqa: E402

sys.path.insert(0, str(HERE.parents[1] / "latency" / "leadlag"))
import load  # noqa: E402

EDGES = [0.0, 0.1, 0.18, 0.21, 0.24, 0.27, 0.30, 0.33, 0.37, 0.42, 0.5, 0.6, 0.8, 1.0, 1.5, 2.5]


def biggest_step(st: series.Step, tau: np.ndarray, lo=0.15, hi=0.45, dt=0.02) -> np.ndarray:
    grid = tau[:, None] - np.arange(lo, hi + 1e-9, dt)[None, :]
    lv = np.log(st.at(grid))
    steps = lv[:, :-1] - lv[:, 1:]  # change over each 20 ms step (later minus earlier)
    k = np.nanargmax(np.abs(np.nan_to_num(steps)), axis=1)
    return np.sign(steps[np.arange(len(tau)), k])


def value_gap(d, s, g: pd.DataFrame) -> dict[str, np.ndarray]:
    end = load.markets().set_index("condition_id")["end"]
    out = {f"val{H}": np.full(len(g), np.nan) for H in (1, 3, 10)}
    for cid in g["market"].unique():
        i = np.flatnonzero(g["market"].to_numpy() == cid)
        bt = series.book_tops(d, cid, s["lag_clob"])
        send = g["ts"].to_numpy()[i] - 0.27
        px = s["perp_mid"].at(np.arange(send.min() - 300, send.min(), 1.0))
        sig = np.nanstd(np.diff(np.log(px[~np.isnan(px)])))
        mid = lambda q: (bt["bb"].at(q) + bt["ba"].at(q)) / 2  # noqa: E731
        m0 = mid(send)
        with np.errstate(divide="ignore", invalid="ignore"):
            slope = norm.pdf(norm.ppf(np.clip(m0, 0.02, 0.98))) / (sig * np.sqrt(np.maximum(end[cid] - send, 5)))
        for H in (1, 3, 10):
            dl = np.log(s["perp_micro"].at(send) / s["perp_micro"].at(send - H))
            out[f"val{H}"][i] = 100 * (slope * dl - (m0 - mid(send - H)))
    return out


def build(f: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for h, g in f.groupby("hour"):
        d = series.load(h)
        s = series.build(d)
        sb = d["spot_bk"]
        s["spot_imb"] = series.Step(sb["t"].to_numpy() - s["lag_spot"], ((sb["bq"] - sb["aq"]) / (sb["bq"] + sb["aq"])).to_numpy())
        tau = g["ts"].to_numpy()
        r = {}
        for a, b in zip(EDGES[1:], EDGES[:-1]):
            for k in ("perp_micro", "spot_micro"):
                r[f"{k}_{b}_{a}"] = 1e4 * np.log(s[k].at(tau - b) / s[k].at(tau - a))
            for k in ("perp_imb", "spot_imb"):
                r[f"{k}_{b}_{a}"] = s[k].at(tau - b) - s[k].at(tau - a)
        for L in (0.21, 0.27, 0.33, 0.5):
            r[f"perp_imb_at{L}"], r[f"spot_imb_at{L}"] = s["perp_imb"].at(tau - L), s["spot_imb"].at(tau - L)
        r.update(value_gap(d, s, g))
        r["perp_step"] = biggest_step(s["perp_micro"], tau)
        r["spot_step"] = biggest_step(s["spot_micro"], tau)
        rows.append(pd.DataFrame(r, index=g.index))
    return f.join(pd.concat(rows))


def main() -> None:
    f = pd.read_pickle(CACHE / "feat.pkl")
    f = f[f["perp_micro_trig"].notna()].copy()
    f["who"] = np.where(f["wallet"] == A, "A", "B")
    f = build(f)
    cols = [c for c in f.columns if c.startswith(("perp_micro_", "spot_micro_", "perp_imb_", "spot_imb_"))
            and not c.endswith(("_trig", "_pre", "_post", "_wide", "_chg")) and not c.startswith("perp_step")]
    hrs = sorted(f["hour"].unique())
    cut = hrs[int(len(hrs) * 2 / 3)]
    for who, g in f.groupby("who"):
        nm = g["spot_r3.0"].abs() < 0.2
        tr, te = (g["hour"] < cut) & nm, (g["hour"] >= cut) & nm
        y = (g["d"] > 0).astype(int)
        for name, cc in (("fine windows, perp + spot", cols), ("fine windows, perp", [c for c in cols if c.startswith("perp")])):
            clf = HistGradientBoostingClassifier(max_iter=400, learning_rate=0.05, max_leaf_nodes=15,
                                                 l2_regularization=1.0, random_state=0).fit(g.loc[tr, cc], y[tr])
            p = clf.predict_proba(g.loc[te, cc])[:, 1]
            print(f"{who} {name}: no-move AUC {roc_auc_score(y[te], p):.3f}, acc {((p > 0.5) == y[te]).mean():.3f}")
        p, q = np.sign(g["perp_micro_trig"]), np.sign(g["spot_micro_trig"].fillna(0))
        opp = (p + q < 0) & (p * q >= 0)
        for H in (1, 3, 10):
            v = g[f"val{H}"] * g["d"]
            print(f"{who} pricing gap {H} s: side acc all {(v.dropna() > 0).mean():.3f}, "
                  f"Binance-opposite fills {(v[opp].dropna() > 0).mean():.3f}")
        for k in ("perp_step", "spot_step"):
            v = g.loc[nm, k] * g.loc[nm, "d"]
            print(f"{who} largest 20 ms {k} in 0.15-0.45 s: acc {(v[v != 0] > 0).mean():.3f}, cov {(v != 0).mean():.2f}")


if __name__ == "__main__":
    main()
