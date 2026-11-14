"""What weight does the data give the other side? (C3 round 3 premise check.)

On near-firing rows (max(pred_up, pred_dn) >= 2 c, frozen gates) of every allowed window, the
realized best-level 1 s value y of the side the frozen rule picks is regressed on
[pred_side, pred_other, c_seen, c_hat]. The identity projection is (1/2, -1/2, -1/2 on the
cost); the frozen score is (1, 0, 0). A weight near 0 on pred_other means the second side
carries no value information and the projection only adds its noise. Diagnostic only.

    OMP_NUM_THREADS=1 nice -n 10 python3 -m research.predict.improve.cand.<pkg>.diag_ols
Writes data/out/predict/improve/c3_coherence/diag_ols.csv."""
from __future__ import annotations

import numpy as np
import pandas as pd

from research.predict.improve.harness import windows as W
from research.predict.improve.harness.fold import Fold
from research.predict.improve.harness.guard import SEALED

from .cost import chat
from .diag_e import CHOOSE_FOLD, DST, _markets
from .score import costs, fee


def rows(L: int = 0) -> pd.DataFrame:
    mks, busy = _markets()
    by_id = {m.id: m for m in mks}
    out = []
    for w, f in CHOOSE_FOLD.items():
        lab = Fold(f).load_rows(windows=(w,), cols=["t", f"x_ba{L}", f"x_bb{L}", f"x_m1_{L}", f"x_m10_{L}"])
        assert lab["m"].map(W._markets().start).max() < SEALED
        for i, g in lab.groupby("m", sort=False):
            m = by_id[int(i)]
            tab = m.tab
            pu, pd_ = (np.asarray(x, float) for x in m.pred("v1", L))
            ba, bb = g[f"x_ba{L}"].to_numpy(float) / 100, g[f"x_bb{L}"].to_numpy(float) / 100
            mk1 = g[f"x_m1_{L}"].to_numpy(float)
            mk10 = g[f"x_m10_{L}"].to_numpy(float)
            mid = tab["pm_mid"].to_numpy(float)
            ok = (ba > 0.005) & (ba < 0.995) & (bb > 0.005) & (bb < 0.995) & np.isfinite(mk1)
            ok &= (tab["pm_bb"].to_numpy() > 0) & (tab["pm_ba"].to_numpy() < 100) & (mid >= 0.05) & (mid <= 0.95)
            ok &= (tab["secs_left"].to_numpy() >= 20) & (np.maximum(pu, pd_) >= 0.02)
            ix = np.flatnonzero(ok)
            if not len(ix):
                continue
            up = pu[ix] >= pd_[ix]
            yu, yd = mk1 - ba - fee(ba), bb - mk1 - fee(1 - bb)
            out.append(pd.DataFrame({"m": m.id, "win": w, "busyQ": m.id in busy,
                                     "y": np.where(up, yu[ix], yd[ix]),
                                     "y10": np.where(up, (mk10 - ba - fee(ba))[ix], (bb - mk10 - fee(1 - bb))[ix]), "ps": np.where(up, pu[ix], pd_[ix]),
                                     "po": np.where(up, pd_[ix], pu[ix]), "cs": costs(tab)[ix], "ch": chat(tab, L)[ix]}))
    return pd.concat(out, ignore_index=True)


def fit(g: pd.DataFrame) -> pd.Series:
    X = np.column_stack([np.ones(len(g)), g["ps"], g["po"], g["cs"], g["ch"]])
    b = np.linalg.lstsq(X, g["y"].to_numpy(), rcond=None)[0]
    X2 = np.column_stack([np.ones(len(g)), g["ps"]])
    b2 = np.linalg.lstsq(X2, g["y"].to_numpy(), rcond=None)[0]
    proj = (g["ps"] - g["po"]) / 2 - g["ch"] / 2
    return pd.Series({"n": len(g), "b_side": b[1], "b_other": b[2], "b_cseen": b[3], "b_chat": b[4],
                      "b_side_alone": b2[1], "corr_y_pred": g["y"].corr(g["ps"]), "corr_y_proj": g["y"].corr(proj),
                      "corr_y_other": g["y"].corr(g["po"])})


def topk(r: pd.DataFrame, ycol: str = "y") -> pd.DataFrame:
    """Mean realized y (c) of the top q of near-firing rows under each score, per window."""
    e_s, e_h = r["ps"] + r["po"] + r["cs"], r["ps"] + r["po"] + r["ch"]
    sc = {"pred": r["ps"], "proj_seen": r["ps"] - e_s / 2, "proj_cm": r["ps"] - e_h / 2,
          "cap_seen": r["ps"] - np.maximum(e_s, 0) / 2, "cap_cm": r["ps"] - np.maximum(e_h, 0) / 2,
          "half_seen": r["ps"] - e_s / 4}
    out = []
    for w, g in list(r.groupby("win")) + [("busyQ", r[r["busyQ"]]), ("all", r)]:
        for q in (0.03, 0.1, 0.3):
            k = max(1, int(q * len(g)))
            row = {"win": w, "q": q, "k": k, "y": ycol}
            for n, s in sc.items():
                yy = g[ycol].to_numpy()[np.argsort(-s.loc[g.index].to_numpy())[:k]]
                row[n] = 100 * np.nanmean(yy)
            out.append(row)
    return pd.DataFrame(out)


def main() -> None:
    from .cost import DIR
    p = DIR / "ols_rows10.pkl"
    r = pd.read_pickle(p) if p.exists() else rows(0)
    r.to_pickle(p)
    t = pd.concat([topk(r, "y"), topk(r, "y10")], ignore_index=True)
    t.to_csv(DST / "diag_topk.csv", index=False)
    print(t.round(2).to_string())
    s = pd.concat([r.groupby("win").apply(fit).reset_index(),
                   fit(r[r["busyQ"]]).to_frame().T.assign(win="busyQ"), fit(r).to_frame().T.assign(win="all")])
    s.to_csv(DST / "diag_ols.csv", index=False)
    print(s.round(3).to_string())


if __name__ == "__main__":
    main()
