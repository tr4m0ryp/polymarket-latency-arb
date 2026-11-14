"""Model-score and decision parity on replayed rows.

(1) `vector`: the pandas-free vectorizer + C trees on the *offline* rows vs the research
pipeline (model/store.py predict_sides, sklearn): isolates the model port.
(2) `live`: the same scorer on the *live* rows vs the research pipeline on the offline rows:
the end-to-end difference. (3) decisions of the two value arms (research/predict/sim/rules.py
vtaker) on both: share of offline orders reproduced (same time and side)."""
from __future__ import annotations

import numpy as np
import pandas as pd

from research.predict.model.store import predict_sides
from research.predict.sim import rules

from ..arms.defs import VT_ARMS
from ..model.load import ValueModel


def _orders(df, pu, pdn, params) -> set:
    d = rules.vtaker(df, pu, pdn, **params)
    return {(round(float(t), 6), int(s)) for t, s in zip(d["t"], d["side"])}


def score_parity(tabs: dict, rows: dict, model: str = "v1_L0", quirk: dict | None = None) -> dict:
    """quirk: slug -> bool mask of rows where the offline table reads the book one grid step
    early (replay/compare.py); score errors are reported on both groups."""
    vm = ValueModel(model)
    mdl = {"model": vm.sk, "vf": vm.vec.vf}
    e_vec, e_live, qk = [], [], []
    n_off = {a["name"]: 0 for a in VT_ARMS}
    n_live = dict(n_off)
    n_match = dict(n_off)
    for s, d in tabs.items():
        live = pd.DataFrame([r for r in rows[s] if r is not None])
        off = pd.DataFrame({k: v[:len(live)] for k, v in d.items()})
        pu, pdn = predict_sides(off, mdl)
        recs = off.to_dict("records")
        vu = np.array([vm(r) for r in recs])
        lu = np.array([vm(r) for r in live.to_dict("records")])
        e_vec.append(np.abs(vu - np.c_[pu, pdn]).max(1))
        e_live.append(np.abs(lu - np.c_[pu, pdn]).max(1))
        qk.append(quirk[s][:len(live)] if quirk else np.zeros(len(live), bool))
        for a in VT_ARMS:
            o = _orders(off, pu, pdn, a["params"])
            lv = _orders(live, lu[:, 0], lu[:, 1], a["params"])
            n_off[a["name"]] += len(o)
            n_live[a["name"]] += len(lv)
            n_match[a["name"]] += len(o & lv)
    ev, el, qk = np.concatenate(e_vec), np.concatenate(e_live), np.concatenate(qk)
    grp = {}
    for name, w in (("all", np.ones(len(el), bool)), ("clean", ~qk), ("quirk", qk)):
        if w.any():
            grp[name] = {"rows": int(w.sum()), "max_abs_c": 100 * float(el[w].max()),
                         "p99_abs_c": 100 * float(np.percentile(el[w], 99)),
                         "frac_gt_0.1c": float((el[w] > 1e-3).mean())}
    return {"model": model, "sha16": vm.sha16, "rows": int(len(ev)),
            "vector_max_abs_c": 100 * float(ev.max()), "live": grp,
            "orders": {k: {"offline": n_off[k], "live": n_live[k], "matched": n_match[k]} for k in n_off}}
