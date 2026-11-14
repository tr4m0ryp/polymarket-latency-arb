"""Busy-state calibration of the refits vs the frozen v1_L0, out of sample only (H6: the busy
slope should move from ~0.75 toward 1).

Rows: every gated decision of a window, the side the model would buy (higher prediction), with
the realised 1 s value (the training target, bad0 == 0). Slope = OLS of realised on predicted
over pred >= 0 (as diag/calibration/analyze/calib.slope), with a market-bootstrap CI; also the
firing rate (pred >= 3 c) per market-hour and the realised-minus-predicted gap of firing rows,
by busy tertile (cuts on run 2 train rows). A fold's model is scored only on its evaluate
windows (fold A on test3r1 + ext, fold B on select + dev3), loaded through the other fold's
training path (Fold.load_rows asserts no sealed market).

    OMP_NUM_THREADS=2 nice -n 10 python3 -m <this package>.eval.calib [--frac 0.2] [--schemes plain,bal]"""
from __future__ import annotations

import argparse

import numpy as np
import pandas as pd

from .....model.learners import clean
from .....model.stack import gate, stacked
from .....model.store import load_model
from .....report.md import md
from ....harness import windows as W
from ....harness.fold import Fold
from ..fit.busy import busy_rows, tertile
from ..fit.model import BUSY_FEAT, fit_fold
from . import OUT_DIR


def _slope(m, x, y, B=300):
    k = x >= 0
    g = pd.DataFrame({"m": m[k], "sx": x[k], "sy": y[k], "n": 1.0, "sxx": x[k] ** 2, "sxy": x[k] * y[k]})
    a = g.groupby("m").sum().to_numpy()
    if len(a) < 3:
        return np.nan, np.nan, np.nan

    def b(s):
        sx, sy, n, sxx, sxy = s.sum(0)
        return (sxy - sx * sy / n) / max(sxx - sx * sx / n, 1e-12)
    bs = [b(a[i]) for i in np.random.default_rng(5).integers(0, len(a), size=(B, len(a)))]
    return b(a), np.percentile(bs, 2.5), np.percentile(bs, 97.5)


def score(tr, vf, b, models, cuts, win) -> list[dict]:
    """Per model and busy level: slope, firing at 3 c, and at the frozen model's 3 c firing
    count (rate-matched threshold: ranking quality free of the prediction scale)."""
    ok = np.isfinite(tr["v1_0"].to_numpy()) & (tr["bad0"] == 0).to_numpy()
    X = clean(tr[vf].to_numpy())
    out, n_ref = [], {}
    for name, mdl in models.items():
        Xm = np.c_[X, clean(b)] if BUSY_FEAT in mdl["vf"] else X
        p = mdl["model"].predict(Xm)
        d = pd.DataFrame({"m": tr["m"].to_numpy(), "row": tr["row"].to_numpy(), "p": p,
                          "y": tr["v1_0"].to_numpy(float), "ok": ok, "b": b})
        d = d.sort_values(["row", "p"], ascending=[True, False]).drop_duplicates("row")
        d = d[d["ok"]]
        ter = tertile(d["b"].to_numpy(), cuts)
        hours = d["m"].nunique() * 5 / 60
        for lv, k in (("all", np.ones(len(d), bool)), ("quiet", ter == 0), ("mid", ter == 1), ("busy", ter == 2)):
            s = d[k]
            sl, lo, hi = _slope(s["m"].to_numpy(), s["p"].to_numpy(), s["y"].to_numpy())
            f = s[s["p"] >= 0.03]
            n_ref.setdefault(lv, len(f))                  # the first model is the frozen reference
            top = s.nlargest(max(n_ref[lv], 1), "p")
            out.append({"win": win, "model": name, "level": lv, "rows": len(s), "slope": sl, "lo": lo, "hi": hi,
                        "fire_per_mkt_h": len(f) / hours, "fire_pred_c": 100 * f["p"].mean(),
                        "fire_real_c": 100 * f["y"].mean(), "fire_gap_c": 100 * (f["y"] - f["p"]).mean(),
                        "thr_matched_c": 100 * top["p"].min(), "matched_real_c": 100 * top["y"].mean()})
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--frac", type=float, default=0.2)
    ap.add_argument("--schemes", default="plain,bal")
    a = ap.parse_args()
    names = tuple(a.schemes.split(","))
    frozen = {"frozen_v1_L0": load_model("v1_L0")}
    res = []
    for f, other in (("A", "B"), ("B", "A")):
        fits = fit_fold(Fold(f), names)
        cuts = fits[names[0]]["meta"]["cuts"]
        for win in W.FOLDS[f][1]:
            rows = Fold(other).load_rows(windows=(win,), frac=a.frac, seed=7)
            b0 = busy_rows(rows)
            g = gate(rows).to_numpy()
            tr, vf = stacked(rows)
            b = b0[g][tr["row"].to_numpy()]
            models = {**frozen, **{f"{f}_{n}": fits[n] for n in names}}
            res += score(tr, vf, b, models, cuts, win)
            print(win, "done", flush=True)
    t = pd.DataFrame(res)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    t.to_csv(OUT_DIR / "calib_refit.csv", index=False)
    txt = md(t.round(3))
    (OUT_DIR / "calib_refit.md").write_text("# Out-of-sample calibration of the C5 refits vs frozen v1_L0\n\n" + txt)
    print(txt)


if __name__ == "__main__":
    main()
