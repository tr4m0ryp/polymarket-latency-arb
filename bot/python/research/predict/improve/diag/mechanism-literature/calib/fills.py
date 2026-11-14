"""The deployed arms' own simulated fills (frozen runs, allowed windows) joined to the mechanism
state at their decision time: our perp feed lag, receipt compression, fair-value churn.

    OMP_NUM_THREADS=2 nice -n 10 python3 research/predict/improve/diag/mechanism-literature fills

Reads data/out/predict/fills-<tag>.pkl of sel1 / dev1 / final / ext (markets asserted before
SEALED and limited to those whose hour files end before SEALED); writes WORK/fills_state.pkl
and prints 10 s markout c/$ (market-bootstrap CI) and $/day per state bucket."""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.special import ndtri

from research.predict.report.md import md
from .. import OUT, PCACHE, POUT, SEALED, WINDOWS, WORK
from ..data.guard import assert_allowed, market_ids, meta, safe_hours
from ..data.load import Hours
from .rows import covariates

ARMS = ("vt_v1_m0.03_any", "vt_v1_m0.02_trigger", "micf")


def _delta(i: int, q: np.ndarray) -> np.ndarray:
    with np.load(PCACHE / "tab" / f"{i}.npz") as z:
        t, mid, zs = z["t"], z["pm_mid"], z["zs"]
    j = np.clip(np.searchsorted(t, q, side="right") - 1, 0, None)
    zq = ndtri(np.clip(mid[j], 0.02, 0.98))
    return 100 * np.exp(-zq ** 2 / 2) / np.sqrt(2 * np.pi) * zs[j] * 1e-4


def build() -> pd.DataFrame:
    ids = market_ids()
    win = {i: w for w, v in ids.items() for i in v}
    mt = meta(sorted(win))
    parts, hrs = [], Hours(keep=2)
    for w, tag in WINDOWS.items():
        f = pd.read_pickle(POUT / f"fills-{tag}.pkl")
        f = f[f["arm"].isin(ARMS) & f["m"].isin(ids[w])]
        for i, g in f.groupby("m"):
            s, e = float(mt.loc[i, "start"]), float(mt.loc[i, "end"])
            assert s < SEALED and e + 35 < SEALED
            perp = hrs.cat(safe_hours(s - 60, e + 35), "fb", lambda c: (c["t"] > s - 60) & (c["t"] < e + 35))
            q = g["t"].to_numpy(float)
            cov = covariates(perp, q, _delta(i, q))
            parts.append(g.assign(window=w, start=s, **cov))
    out = pd.concat(parts, ignore_index=True)
    assert_allowed(out["start"], "fills")
    return out


def table(f: pd.DataFrame, key: str, B: int = 1000) -> pd.DataFrame:
    rows, rng = [], np.random.default_rng(5)
    nm = {w: len(v) for w, v in market_ids().items()}
    days = sum(nm[w] for w in f["window"].unique()) / 288
    for (arm, L, k), g in f.groupby(["arm", "L", key], sort=True):
        a = g.groupby("m").agg(v=("mk10v", "sum"), c=("cost", "sum"))
        v, c = a["v"].to_numpy(), a["c"].to_numpy()
        kk = rng.integers(0, len(a), size=(B, len(a)))
        r = 100 * v[kk].sum(1) / c[kk].sum(1)
        rows.append({"arm": arm, "L": L, key: k, "fills": len(g),
                     "mk10 c/$": f"{100 * v.sum() / c.sum():+.1f} [{np.percentile(r, 2.5):+.1f}, {np.percentile(r, 97.5):+.1f}]",
                     "mk10 $/day": f"{v.sum() / days:+,.0f}"})
    return pd.DataFrame(rows)


def main() -> None:
    import sys
    np.seterr(all="ignore")
    if "--reuse" in sys.argv and (WORK / "fills_state.pkl").exists():
        f = pd.read_pickle(WORK / "fills_state.pkl")
        assert_allowed(f["start"], "fills")
    else:
        f = build()
        WORK.mkdir(parents=True, exist_ok=True)
        f.to_pickle(WORK / "fills_state.pkl")
    f["feed"] = pd.cut(f["lag_feed"], [-1, 0.13, 0.2, 0.5, 1e9], labels=["<=130ms", "130-200", "200-500", ">500ms"])
    f["compressed"] = np.where(f["compress"] > 1.5, "compressed", "normal")
    cut = np.quantile(f["cvol30"].dropna(), [0, .2, .4, .6, .8, 1])
    f["cvol_q"] = pd.cut(f["cvol30"], np.r_[-np.inf, cut[1:-1], np.inf], labels=[f"Q{k}" for k in range(1, 6)])
    u = f[f["window"] != "select"]
    pc = np.quantile(u["pmsg10"].dropna(), [.2, .4, .6, .8])
    f["pmsg_q"] = pd.cut(f["pmsg10"], np.r_[-np.inf, pc, np.inf], labels=[f"Q{k}" for k in range(1, 6)])
    f["busy"] = np.where(f["pmsg10"] > 313, ">313 msg/s", "<=313 msg/s")   # calib quintile edge (post hoc)
    d = OUT / "diag-mechanism-literature"
    d.mkdir(parents=True, exist_ok=True)
    unseen = f[f["window"] != "select"]
    for key in ("feed", "compressed", "cvol_q", "pmsg_q", "busy"):
        t = table(unseen, key)
        t.to_csv(d / f"fills_{key}.csv", index=False)
        print(f"\n### deployed arms' fills (dev3 + test3r1 + ext), 10 s markout by {key}\n")
        print(md(t, 2))
    print("share of fills with feed lag > 130 ms by window:",
          f.assign(x=f["lag_feed"] > 0.13).groupby("window")["x"].mean().round(3).to_dict())


if __name__ == "__main__":
    main()
