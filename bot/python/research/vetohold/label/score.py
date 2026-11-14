"""Score the frozen hold-aware veto models ONCE on test hours (t >= 2026-10-13 00:00 UTC).

Each model's decisions on the test label rows (trigger + gates, pred >= its frozen tau,
0.2 s refractory) become orders that replay through the measured hold with own-take memory
(replay/market.py); scored at i = 0 (limit = seen), 60 sh, against the frozen v1 veto
(v1's rule: best side = trigger side, value >= 2 c) on the same rows and replay.

    PYTHONPATH=. python3 -m research.vetohold.label.score --workers 30
    -> data/out/vetohold/vmodels/{rows-test.pkl, score.md}"""
from __future__ import annotations

import argparse
import hashlib
import json
import pickle
from multiprocessing import Pool

import numpy as np
import pandas as pd

from research.predict.report.md import md

from ..data.orders import live_hold
from ..replay.market import run_market
from ..tables.common import ci, paired, stats
from .data import design, load, refractory, v1_pred
from .train import VM

_st = _o = _h = None


def _do(ids):
    global _st
    from research.strategy.ingest.load import Store
    _st = _st or Store(keep=2)
    out = []
    for i in ids:
        o = _o[_o["m"] == i]
        m = _st.market(i)
        if len(o) and m is not None and m["outcome"] is not None:
            out += run_market(m, o, _h, seed=i)
    return out


def _init(o, h):
    global _o, _h
    _o, _h = o, h


def decisions(d, X, meta) -> pd.DataFrame:
    from research.strategy.ingest.load import Store
    mk = Store().mk
    preds = {"v1_frozen": (v1_pred(d), 0.02), "v1_remargin": (v1_pred(d), meta["variants"]["v1_remargin"]["tau"])}
    for name, v in meta["variants"].items():
        if "sha256" not in v:
            continue
        blob = (VM / f"{name}.pkl").read_bytes()
        assert hashlib.sha256(blob).hexdigest() == v["sha256"], name
        M, reg = design(name, X, d)
        p = np.full(len(d), -np.inf)
        p[reg] = pickle.loads(blob).predict(M[reg])
        preds[name] = (p, v["tau"])
    parts = []
    for arm, (p, tau) in preds.items():
        k = refractory(d, p >= tau)
        o = d[k].copy()
        o["arm"], o["edge"] = arm, np.where(np.isfinite(p[k]), p[k], 0.0)
        parts.append(o)
    o = pd.concat(parts, ignore_index=True)
    o["slug"], o["end"] = mk["slug"].to_numpy()[o["m"]], mk["end"].to_numpy()[o["m"]]
    o["outcome"] = np.where(o["side"] > 0, o["won"], 1 - o["won"])
    o = o.rename(columns={"pu": "pred_up", "pd": "pred_dn"})
    o["value"], o["src"], o["t_venue"] = o["edge"], "tab", np.nan
    o["fill_sh"], o["cost"], o["mk10"] = 0.0, 0.0, np.nan
    return o.sort_values(["m", "t"]).reset_index(drop=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=3)
    a = ap.parse_args()
    meta = json.loads((VM / "prereg.json").read_text())
    d, X = load()
    te = d["test"].to_numpy()
    d, X = d[te].reset_index(drop=True), X[te]
    o = decisions(d, X, meta)
    ids = sorted(o["m"].unique())
    chunks = [ids[k:k + 4] for k in range(0, len(ids), 4)]
    with Pool(a.workers, _init, (o, live_hold())) as p:
        rows = pd.DataFrame([r for part in p.imap(_do, chunks) for r in part])
    rows.to_pickle(VM / "rows-test.pkl")
    report(rows, meta, sorted(d["m"].unique()))


def report(rows: pd.DataFrame, meta: dict, mids) -> None:
    from research.strategy.ingest.load import Store
    mk = list(Store().mk["slug"].to_numpy()[mids])
    hours = len(mk) / 12
    out = [f"# Hold-aware veto models on test hours ({len(mk)} markets, frozen {meta['frozen_utc']} UTC)\n",
           f"pre-registered winner: {meta['winner']} (exported as {meta['export']['name']})\n"]
    for sc in ("real", "q50", "paper"):
        r = rows[rows["scen"] == sc]
        base = r[r["arm"] == "v1_frozen"]
        t = []
        for arm, g in r.groupby("arm", sort=False):
            s, sr = stats(g, "pnl_k0_60", "cost_k0_60", mk), stats(g, "res_k0_60", "cost_k0_60", mk)
            p = paired(g, "pnl_k0_60", base, "pnl_k0_60", mk)
            t.append({"model": arm, "tau": meta["variants"].get(arm, {}).get("tau", 0.02), "orders/h": len(g) / hours,
                      "fills/h": g["fillp_k0"].sum() / hours, "mk10 c/$": ci(s, "c_per_$", "c_lo", "c_hi"),
                      "res c/$": ci(sr, "c_per_$", "c_lo", "c_hi"), "$/day": ci(s, "usd_day", "d_lo", "d_hi", 0),
                      "gain vs v1 $/day": ci(p, "gain_day", "g_lo", "g_hi", 0)})
        out += [f"\n## hold `{sc}`, i = 0, 60 sh\n", md(pd.DataFrame(t), 1)]
    (VM / "score.md").write_text("\n".join(out) + "\n")
    print("\n".join(out))


if __name__ == "__main__":
    main()
