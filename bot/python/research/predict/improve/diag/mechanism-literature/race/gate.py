"""A surprise gate on the deployed arms' own frozen fills (no re-simulation: fills are only
dropped, so depth and competition are as simulated). Surprise at the decision = side-signed
staleness in cents / 30 s fair churn (race/surprise.py). Reported on select (the selection
window, where a threshold could legitimately be chosen) and on the unseen windows (dev3 +
test3r1 + ext, labelled post hoc). micf stays ungated in the paired gain.

    python3 research/predict/improve/diag/mechanism-literature gate"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.special import ndtri

from research.predict.report.md import md
from .. import OUT, PCACHE, WORK
from ..data.guard import assert_allowed, market_ids

DIR = OUT / "diag-mechanism-literature"
ARMS = ("vt_v1_m0.03_any", "vt_v1_m0.02_trigger")
GATES = {"none (frozen)": None, "surprise >= 0.05": 0.05, "surprise >= 0.25": 0.25, "surprise >= 0.5": 0.5}


def with_surprise(f: pd.DataFrame) -> pd.DataFrame:
    parts = []
    for i, g in f.groupby("m"):
        with np.load(PCACHE / "tab" / f"{i}.npz") as z:
            t, ps, mid = z["t"], z["pm_stale"], z["pm_mid"]
        j = np.clip(np.searchsorted(t, g["t"].to_numpy(), side="right") - 1, 0, None)
        zq = ndtri(np.clip(mid[j], 0.02, 0.98))
        c = 100 * np.exp(-zq ** 2 / 2) / np.sqrt(2 * np.pi) * ps[j] * g["side"].to_numpy()
        parts.append(pd.Series(c / np.maximum(g["cvol30"].to_numpy(), 0.5), index=g.index))
    return f.assign(sur=pd.concat(parts))


def _boot(a: pd.DataFrame, b: pd.DataFrame, ids, days, rng, B=1000):
    va = a.groupby("m")["mk10v"].sum().reindex(ids).fillna(0).to_numpy()
    ca = a.groupby("m")["cost"].sum().reindex(ids).fillna(0).to_numpy()
    vb = b.groupby("m")["mk10v"].sum().reindex(ids).fillna(0).to_numpy()
    k = rng.integers(0, len(ids), (B, len(ids)))
    cpd = 100 * va[k].sum(1) / np.maximum(ca[k].sum(1), 1e-9)
    gain = (va - vb)[k].sum(1) / days
    return (f"{100 * va.sum() / max(ca.sum(), 1e-9):+.1f} [{np.percentile(cpd, 2.5):+.1f}, {np.percentile(cpd, 97.5):+.1f}]",
            f"{(va - vb).sum() / days:+.0f} [{np.percentile(gain, 2.5):+.0f}, {np.percentile(gain, 97.5):+.0f}]")


def table(f: pd.DataFrame, ids, label: str, busy_only: bool = False) -> list[dict]:
    days, rng, rows = len(ids) / 288, np.random.default_rng(17), []
    u = f[f["m"].isin(ids)]
    if busy_only:
        u = u[u["pmsg10"] > 313]
    for L in (0, -40):
        base = u[(u["arm"] == "micf") & (u["L"] == L)]
        for arm in ARMS:
            g = u[(u["arm"] == arm) & (u["L"] == L)]
            for name, thr in GATES.items():
                k = g if thr is None else g[g["sur"] >= thr]
                cpd, gain = _boot(k, base, ids, days, rng)
                rows.append({"window": label + (" (fills > 313 msgs/s only)" if busy_only else ""), "arm": arm, "L": L,
                             "gate": name, "fills": len(k), "mk10 c/$ [CI]": cpd,
                             "mk10 $/day": round(k["mk10v"].sum() / days), "gain vs micf $/day [CI]": gain})
    return rows


def main() -> None:
    np.seterr(all="ignore")
    f = pd.read_pickle(WORK / "fills_state.pkl")
    assert_allowed(f["start"], "fills")
    f = with_surprise(f)
    mi = market_ids()
    unseen = sorted(i for w in ("dev3", "test3r1", "ext") for i in mi[w])
    rows = table(f, sorted(mi["select"]), "select") + table(f, unseen, "unseen, post hoc")
    rows += table(f, unseen, "unseen, post hoc", busy_only=True)
    t = pd.DataFrame(rows)
    DIR.mkdir(parents=True, exist_ok=True)
    t.to_csv(DIR / "gate_surprise.csv", index=False)
    print(md(t, 3))
    q = f[f["arm"].isin(ARMS)].groupby(["window", "arm"])["sur"].describe(percentiles=[.1, .25, .5]).round(3)
    print(q.to_string())


if __name__ == "__main__":
    main()
