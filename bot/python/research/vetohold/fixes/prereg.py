"""Fit, select and freeze the fixes on SELECTION hours only (before 2026-10-13 00:00 UTC).

Parameters are chosen on out-of-fold predictions (5 folds grouped by market) by the highest
selection $/day with at least 5% of orders sent; the models are then refit on all selection
orders and frozen with their sha256. Test rows are never read here.

    PYTHONPATH=. python3 -m research.vetohold.fixes.prereg -> data/out/vetohold/prereg.{json,pkl}"""
from __future__ import annotations

import hashlib
import json
import pickle
import time
from itertools import product

import numpy as np
import pandas as pd
from sklearn.model_selection import GroupKFold

from .. import OUT, SPLIT, VETO
from .models import feats, fit, predict
from .rules import apply

GRID = {
    "surv": [{"tau": x} for x in np.round(np.linspace(-0.02, 0.05, 15), 4)],
    "fixed": [{"i": i} for i in range(11)],
    "istar": [{"tau": x, "pad": p} for x, p in product(np.round(np.arange(-0.06, 0.041, 0.01), 2), (0, 1, 2, 3))],
    "size": [{"frac": f} for f in (0.25, 0.5, 1.0)],
    "fresh": [{"tau": x} for x in (0.02, 0.05, 0.1, 0.2, 0.5)],
    "ev": [{"tau": x} for x in np.round(np.linspace(-0.05, 0.10, 16), 3)],
}
MIN_SENT = 0.05


def selection() -> pd.DataFrame:
    d = pd.read_pickle(OUT / "rows.pkl")
    return d[(d["arm"] == VETO) & (d["scen"] == "real") & (d["t"] < SPLIT)].reset_index(drop=True)


def oof(d: pd.DataFrame, cols: list[str]) -> dict:
    pr = {}
    for tr, te in GroupKFold(5).split(d, groups=d["slug"]):
        p = predict(fit(d.iloc[tr], cols), d.iloc[te], cols)
        for k, v in p.items():
            pr.setdefault(k, np.zeros(len(d)))[te] = v
    return pr


def main():
    d = selection()
    cols = feats(d)
    pr = oof(d, cols)
    days = d["slug"].nunique() / 288
    chosen, table = {}, []
    for rule, grid in GRID.items():
        best = None
        for par in grid:
            r = apply(rule, d, pr, par)
            usd, sent = r["pnl"].sum() / days, r["sent"].mean()
            table.append({"rule": rule, **{k: float(v) for k, v in par.items()}, "sel_usd_day": usd, "sent": sent})
            if sent >= MIN_SENT and (best is None or usd > best[0]):
                best = (usd, par)
        chosen[rule] = {k: float(v) for k, v in best[1].items()}
    chosen["surv_size"] = {**chosen["surv"], **chosen["size"]}
    models = fit(d, cols)
    blob = pickle.dumps({"models": models, "cols": cols})
    (OUT / "prereg.pkl").write_bytes(blob)
    plain = apply("plain", d, pr, {})
    meta = {"frozen_utc": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()), "split": SPLIT,
            "selection_orders": len(d), "selection_markets": int(d["slug"].nunique()),
            "plain_sel_usd_day": plain["pnl"].sum() / days, "params": chosen, "min_sent": MIN_SENT,
            "features": cols, "models_sha256": hashlib.sha256(blob).hexdigest(),
            "scoring": "test hours (t >= split), veto orders, real hold, paired market bootstrap vs plain"}
    (OUT / "prereg.json").write_text(json.dumps(meta, indent=1))
    pd.DataFrame(table).to_csv(OUT / "prereg-grid.csv", index=False)
    print(json.dumps({k: meta[k] for k in ("selection_orders", "plain_sel_usd_day", "params")}, indent=1))


if __name__ == "__main__":
    main()
