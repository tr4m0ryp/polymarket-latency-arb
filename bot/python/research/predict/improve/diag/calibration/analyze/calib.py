"""Calibration of the frozen value models by prediction decile and activity regime.

    python3 -m research.predict.improve.diag.calibration.analyze.calib

Rows = the side each model would buy at every gated decision (common.chosen). For every
window x model: deciles of the prediction (cut per window) with mean predicted vs realised 1 s
(the training target) and 10 s (the edge measure) value; and in the firing region (pred >=
1 / 2 / 3 / 5 c) the realised-minus-predicted gap per regime level with a market-bootstrap CI,
the calibration slope (OLS of realised 1 s on pred over pred >= 0) and the firing rate per
market-hour. Writes OUT/calib.md and OUT/calib_regime.csv."""
from __future__ import annotations

import numpy as np
import pandas as pd

from .. import OUT
from .....report.md import md
from .common import LEVELS, REGIMES, boot_ratio, chosen, fmt, level

WINS = ("train", "select", "dev3", "final", "ext")
MODELS = ("v1_L0", "v1_L-40", "v3p_L0")
BINS = (0.01, 0.02, 0.03, 0.05)


def deciles(c: pd.DataFrame) -> pd.DataFrame:
    b = pd.qcut(c["pred"].rank(method="first"), 10, labels=False)
    g = c.assign(b=b).groupby("b").agg(n=("pred", "size"), pred_c=("pred", "mean"), r1_c=("r1", "mean"),
                                       r10_c=("r10", "mean"))
    g[["pred_c", "r1_c", "r10_c"]] *= 100
    return g.reset_index()


def slope(c: pd.DataFrame, B: int = 300) -> tuple[float, float, float]:
    """Calibration slope of realised 1 s value on the prediction over pred >= 0 rows."""
    c = c[c["pred"] >= 0]
    if len(c) < 50:
        return np.nan, np.nan, np.nan
    g = c.groupby("m").agg(sx=("pred", "sum"), sy=("r1", "sum"), n=("pred", "size"),
                           sxx=("pred", lambda x: (x * x).sum()),
                           sxy=("pred", lambda x: (x * c.loc[x.index, "r1"]).sum()))
    a = g.to_numpy()

    def b(s):
        sx, sy, n, sxx, sxy = s.sum(0)
        return (sxy - sx * sy / n) / max(sxx - sx * sx / n, 1e-12)
    k = np.random.default_rng(5).integers(0, len(a), size=(B, len(a)))
    bs = [b(a[i]) for i in k]
    return b(a), np.percentile(bs, 2.5), np.percentile(bs, 97.5)


def regime_rows(win: str, model: str, c: pd.DataFrame) -> list[dict]:
    hours = c["m"].nunique() * 5 / 60
    out = []
    for rg in REGIMES:
        lv = level(c, rg)
        for k, name in enumerate(LEVELS):
            s = c[lv == k]
            share = len(s) / len(c)
            for lo in BINS:
                f = s[s["pred"] >= lo]
                r = {"win": win, "model": model, "regime": rg, "level": name, "row_share": share,
                     "pred_ge": lo, "n": len(f), "fire_per_mkt_h": len(f) / hours,
                     "pred_c": 100 * f["pred"].mean() if len(f) else np.nan}
                for t in ("r1", "r10"):
                    p, a, b = boot_ratio(f["m"].to_numpy(), f[t].to_numpy(), np.ones(len(f)))
                    g, ga, gb = boot_ratio(f["m"].to_numpy(), (f[t] - f["pred"]).to_numpy(), np.ones(len(f)))
                    r |= {f"{t}_c": 100 * p, f"{t}_lo": 100 * a, f"{t}_hi": 100 * b,
                          f"gap{t[1:]}_c": 100 * g, f"gap{t[1:]}_lo": 100 * ga, f"gap{t[1:]}_hi": 100 * gb}
                out.append(r)
    return out


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    txt, reg, slo = ["# Calibration of the frozen value models by regime\n"], [], []
    for model in MODELS:
        for win in WINS:
            c = chosen(win, model)
            if win in ("dev3", "ext") or (model == "v1_L0" and win in ("select", "final")):
                txt.append(f"\n## Deciles, {model}, {win} ({c['m'].nunique()} markets, {len(c)} rows)\n")
                txt.append(md(deciles(c), 2))
            reg += regime_rows(win, model, c)
            for rg in ("all", "busy", "bn60", "rv10", "pmtop10", "pmtr60"):
                lv = np.zeros(len(c), int) if rg == "all" else level(c, rg)
                for k in sorted(set(lv)):
                    s = c[lv == k]
                    b, lo, hi = slope(s)
                    slo.append({"model": model, "win": win, "regime": rg,
                                "level": "all" if rg == "all" else LEVELS[k], "n_pos": int((s["pred"] >= 0).sum()),
                                "slope": b, "lo": lo, "hi": hi})
            print(model, win, flush=True)
    reg, slo = pd.DataFrame(reg), pd.DataFrame(slo)
    reg.to_csv(OUT / "calib_regime.csv", index=False)
    slo.to_csv(OUT / "calib_slope.csv", index=False)
    txt.append("\n## Calibration slope (realised 1 s on pred, pred >= 0 rows; 1 = calibrated)\n")
    txt.append(md(slo, 3))
    f3 = reg[(reg["pred_ge"] == 0.03) & reg["regime"].isin(["busy", "bn60", "rv10", "pmtr60", "pmtop10"])]
    f3 = f3.assign(gap10=[fmt(a / 100, b / 100, c / 100) for a, b, c in zip(f3["gap10_c"], f3["gap10_lo"], f3["gap10_hi"])])
    txt.append("\n## Firing region pred >= 3 c by regime level (gap = realised - pred, c/sh)\n")
    txt.append(md(f3[["model", "win", "regime", "level", "row_share", "n", "fire_per_mkt_h", "pred_c", "r1_c",
                      "gap1_c", "r10_c", "gap10"]], 2))
    (OUT / "calib.md").write_text("\n".join(txt))


if __name__ == "__main__":
    main()
