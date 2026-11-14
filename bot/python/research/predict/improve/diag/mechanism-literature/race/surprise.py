"""Is the frozen 1 s model's busy-hour over-prediction an information-dilution failure?

Rows = WORK/calib.pkl (frozen v1_L0 rows with pred >= 2 c on dev3 / test3r1 / ext, built by
`calib`). Row surprise = side-signed staleness in cents (pm_stale is the perp microprice move
since our book view last changed, in settlement z-units; x 100 phi(z) = cents) over the 30 s
fair-value churn (cvol30, cents). Realized 1 s value vs prediction per perp msgs/s bin x
surprise bin (fixed round edges: 100 / 300 msgs/s, surprise 0.05 / 0.5, near the pooled
tercile edges). Post hoc on windows that were tests: diagnostic only.

    python3 research/predict/improve/diag/mechanism-literature surprise"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.special import ndtri

from research.predict.report.md import md
from .. import OUT, WORK
from ..analyze.stats import boot_ratio, fmt
from ..data.guard import assert_allowed

DIR = OUT / "diag-mechanism-literature"


def rows(tag: str = "calib") -> pd.DataFrame:
    r = pd.read_pickle(WORK / f"{tag}.pkl")
    assert_allowed(r["start"], "calib rows")
    r = r[np.isfinite(r["y1"]) & np.isfinite(r["pred"]) & np.isfinite(r["cvol30"])].copy()
    zq = ndtri(np.clip(r["pm_mid"].to_numpy(float), 0.02, 0.98))
    r["stale_c"] = 100 * np.exp(-zq ** 2 / 2) / np.sqrt(2 * np.pi) * r["pm_stale"] * r["side"]
    r["sur"] = r["stale_c"] / np.maximum(r["cvol30"], 0.5)
    r["busy"] = pd.cut(r["pmsg10"], [-np.inf, 100, 300, np.inf], labels=["<=100", "100-300", ">300"])
    r["surp"] = pd.cut(r["sur"], [-np.inf, 0.05, 0.5, np.inf], labels=["<0.05", "0.05-0.5", ">=0.5"])
    return r


def table(r: pd.DataFrame) -> pd.DataFrame:
    out = []
    for (b, s), g in r.groupby(["busy", "surp"], observed=True):
        y = boot_ratio(g, "y1")
        f = g[g["pred"] >= 0.03]
        yf = boot_ratio(f, "y1") if len(f) > 30 else (np.nan,) * 3
        out.append({"perp msgs/s": b, "surprise": s, "rows": len(g), "mkts": g["m"].nunique(),
                    "surprise range": f"{g['sur'].min():.2g}..{g['sur'].max():.2g}",
                    "pred c": round(100 * g["pred"].mean(), 2), "real 1s c [CI]": fmt(y[0], y[1], y[2], 2, 100),
                    "real/pred": round(g["y1"].mean() / g["pred"].mean(), 2),
                    "fire rows (pred >= 3 c)": len(f), "fire real 1s c [CI]": fmt(yf[0], yf[1], yf[2], 2, 100)})
    return pd.DataFrame(out)


def main() -> None:
    np.seterr(all="ignore")
    DIR.mkdir(parents=True, exist_ok=True)
    for tag, label in (("calib", "unseen dev3 + test3r1 + ext (post hoc)"), ("calib_select", "select (selection window)")):
        if not (WORK / f"{tag}.pkl").exists():
            continue
        r = rows(tag)
        t = table(r)
        t.to_csv(DIR / f"{tag}_busy_x_surprise.csv", index=False)
        print(f"\n### frozen v1_L0 rows, {label}: realized vs predicted by msgs/s x surprise bin\n")
        print(md(t, 3))
        print("Spearman(sur, pmsg10) =", round(r[["sur", "pmsg10"]].corr(method="spearman").iloc[0, 1], 2),
              "| share of rows with surprise < 0.05:", round(float((r["sur"] < 0.05).mean()), 2))


if __name__ == "__main__":
    main()
