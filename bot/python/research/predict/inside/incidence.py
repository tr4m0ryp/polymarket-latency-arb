"""Test 1 of reports/fill-improve.md: how often fair -/+ 0.04 sat strictly inside the spread.

(a) On the dry run's logged quote rows (quotes-*.tsv.gz: every row carries pu, pdn, fair, bb,
    ba), rows per hour where the inside gate (pull -0.02) quotes a side.
(b) On every decision row of the run's own recording (predict tables + model v1_L50),
    inside-gate insert events per hour (a new nonzero target tick per side), h = 0 and 0.005,
    next to the frozen rule. Reads no fills or outcomes.

    BTCLAT_*=<run cache> python3 -m research.predict.inside.incidence --run <run>"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

TRADE = Path(__file__).resolve().parents[3] / "data" / "trade"


def _frame(q: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame({"t": q["t"], "pm_bb": q["bb"], "pm_ba": q["ba"], "pm_mid": q["mid"],
                         "secs_left": q["secs_left"], "fair_p": q["fair"]})


def logged(root: Path) -> pd.DataFrame:
    from recorder.live.sink import read_stream
    from ..sim import rules
    q = pd.DataFrame([json.loads(r) for _, r in read_stream("quotes", root=root)])
    d = _frame(q)
    _, b, a = rules.vinside(d, q["pu"].to_numpy(float), q["pdn"].to_numpy(float))
    q["hour"] = pd.to_datetime(q["t"], unit="s").dt.floor("h")
    q["inside"] = (b > 0) | (a > 0)
    return q.groupby("hour").agg(rows=("t", "size"), inside_rows=("inside", "sum"))


def inserts(tick: np.ndarray) -> np.ndarray:
    """Decision indices where a side gets a new nonzero target (an insert)."""
    chg = np.r_[True, tick[1:] != tick[:-1]]
    return np.flatnonzero(chg & (tick > 0))


def replay() -> pd.DataFrame:
    from ..model.data import TAB
    from ..model.store import load_model, predict_sides
    from ..sim import rules
    mdl, rows = load_model("v1_L50"), []
    for p in sorted(TAB.glob("*.npz")):
        with np.load(p) as z:
            tab = pd.DataFrame({k: z[k] for k in z.files})
        if not len(tab):
            continue
        pu, pdn = predict_sides(tab, mdl)
        t = tab["t"].to_numpy()
        arms = {"frozen": rules.vmaker(tab, pu, pdn, half=0.03, pull=-0.03),
                "inside": rules.vinside(tab, pu, pdn), "inside_h0.005": rules.vinside(tab, pu, pdn, h=0.005)}
        for name, (_, b, a) in arms.items():
            for side, k in (("bid", b), ("ask", a)):
                ins = inserts(k)
                live = np.diff(np.r_[t, t[-1]]) * (k > 0)
                for hr, n in pd.Series(1, index=pd.to_datetime(t[ins], unit="s").floor("h")).groupby(level=0).sum().items():
                    rows.append({"arm": name, "side": side, "hour": hr, "inserts": n, "live_s": 0.0})
                for hr, s in pd.Series(live, index=pd.to_datetime(t, unit="s").floor("h")).groupby(level=0).sum().items():
                    rows.append({"arm": name, "side": side, "hour": hr, "inserts": 0, "live_s": s})
    d = pd.DataFrame(rows).groupby(["arm", "hour"])[["inserts", "live_s"]].sum().reset_index()
    return d.pivot(index="hour", columns="arm", values=["inserts", "live_s"])


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    a = ap.parse_args()
    pd.set_option("display.width", 200)
    print(logged(TRADE / a.run).to_string())
    print(replay().round(0).to_string())


if __name__ == "__main__":
    main()
