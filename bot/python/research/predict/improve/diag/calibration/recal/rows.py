"""Row-level test of the recalibration forms (best level, no depth or rivals: a proxy; the
simulator in recal/sim.py is the judge).

    OMP_NUM_THREADS=2 nice -n 10 python3 -m research.predict.improve.diag.calibration.recal.rows

Timeline = chosen rows of train -> select -> dev3 -> final -> ext (contiguous hours). Forms
from recal/registry.py (static ones fitted on select only; online ones carry no fitted
parameter) plus a q25 lower-bound GBDT (train fit, threshold budget-matched on select).
Per window: orders after the 0.2 s refractory, their realised 10 s value at the best level
(60 sh), c/sh, c/$, $/day, and the paired $/day difference vs the frozen rule (m3: p >= 3 c)
with a market-bootstrap CI. Writes OUT/recal_rows.md and recal_rows.csv."""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor

from .. import OUT
from .....report.md import md
from ..analyze.common import chosen, level
from .registry import FORMS, make_fit, score

WINS = ("train", "select", "dev3", "final", "ext")
QX = ["pred", "bn60", "rv10", "rv60", "pmtr60", "pmtop10", "seen", "secs_left", "delta", "tok_mid", "pm_tsc"]


def timeline(model: str) -> pd.DataFrame:
    parts = [chosen(w, model).assign(win=w) for w in WINS]
    d = pd.concat(parts, ignore_index=True).sort_values("t", kind="stable").reset_index(drop=True)
    d["lv"] = level(d, "busy")
    return d


def orders(d: pd.DataFrame, score: np.ndarray, thr: float, refr: float = 0.2) -> np.ndarray:
    """Row indices that fire (score >= thr) after a per-market refractory."""
    keep = np.zeros(len(d), bool)
    ok = score >= thr
    for _, g in d[ok].groupby("m", sort=False):
        last = -np.inf
        for i, t in zip(g.index.to_numpy(), g["t"].to_numpy()):
            if t - last >= refr:
                keep[i], last = True, t
    return keep


def metrics(d: pd.DataFrame, k: np.ndarray, base: np.ndarray, win: str, B: int = 1000) -> dict:
    w = (d["win"] == win).to_numpy()
    mk = np.unique(d.loc[w, "m"])
    days = len(mk) / 288
    v = pd.Series(60 * d["r10"].to_numpy() * k, index=d["m"])[w].groupby(level=0).sum().reindex(mk, fill_value=0)
    vb = pd.Series(60 * d["r10"].to_numpy() * base, index=d["m"])[w].groupby(level=0).sum().reindex(mk, fill_value=0)
    diff = (v - vb).to_numpy()
    s = diff[np.random.default_rng(7).integers(0, len(diff), size=(B, len(diff)))].sum(1) / days
    f = d[w & k]
    return {"orders_h": len(f) / (len(mk) / 12), "pred_c": 100 * f["pred"].mean(), "r1_c": 100 * f["r1"].mean(),
            "r10_c_sh": 100 * f["r10"].mean(), "r10_c_usd": 100 * f["r10"].sum() / f["seen"].sum(),
            "usd_day": v.sum() / days, "vs_frozen": diff.sum() / days, "lo": np.percentile(s, 2.5),
            "hi": np.percentile(s, 97.5)}


def scores(d: pd.DataFrame, L: int) -> dict:
    sel = (d["win"] == "select").to_numpy()
    tr = (d["win"] == "train").to_numpy()
    p, y, t = d["pred"].to_numpy(), d["r1"].to_numpy(), d["t"].to_numpy()
    fit = make_fit({L: d}, None)
    lvp = level(d, "pmtr60")
    out = {f: score(f, p, t, d["lv"].to_numpy(), lvp, L, fit) for f in FORMS}
    w = tr & (p >= 0.0)
    q = HistGradientBoostingRegressor(loss="quantile", quantile=0.25, max_iter=150, max_leaf_nodes=15,
                                      min_samples_leaf=200, learning_rate=0.05, random_state=0)
    q.fit(np.nan_to_num(d.loc[w, QX].to_numpy(np.float32)), y[w])
    q25 = np.where(p >= 0.0, q.predict(np.nan_to_num(d[QX].to_numpy(np.float32))), -1.0)
    n0 = ((p >= 0.03) & sel).sum()                      # budget-matched on select
    thr = np.sort(q25[sel])[::-1][n0 - 1]
    out[f"q25 (thr {100 * thr:.2f} c)"] = (q25, thr)
    return out


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    allr, txt = [], ["# Recalibration forms, row-level proxy (best level, 60 sh, 0.2 s refractory)\n"]
    for model, L in (("v1_L0", 0), ("v1_L-40", -40)):
        d = timeline(model)
        sc = scores(d, L)
        base = orders(d, *sc["m3"])
        for name, (s, thr) in sc.items():
            k = base if name == "m3" else orders(d, s, thr)
            for w in WINS[1:]:
                allr.append({"model": model, "form": name, "win": w, **metrics(d, k, base, w)})
            print(model, name, flush=True)
    r = pd.DataFrame(allr)
    r.to_csv(OUT / "recal_rows.csv", index=False)
    for (model, w), g in r.groupby(["model", "win"], sort=False):
        txt.append(f"\n## {model}, {w}\n")
        txt.append(md(g.drop(columns=["model", "win"]), 2))
    (OUT / "recal_rows.md").write_text("\n".join(txt))


if __name__ == "__main__":
    main()
