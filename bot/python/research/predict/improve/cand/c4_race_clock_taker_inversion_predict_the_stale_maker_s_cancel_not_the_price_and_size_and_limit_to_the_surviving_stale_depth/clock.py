"""The race clock: P(the seen stale level is still resting at our L = 0 match).

    P_alive = sigmoid(b0 + b1 log(1 + q_seen) + b2 log(1 + pm_tsc) + b3 (a_hat - prior) + b4 log(1 + pm60))

q_seen = receipt-clock size at the level we would take; pm_tsc = seconds since our Polymarket
top last changed (tab); pm60 = Polymarket book msgs/s over 60 s (calibration ctx, causal);
a_hat = per-market EWMA (span 8) of past stale-level outcomes, each usable only from
t_e + KNOWN on (prior = run 2 train base rate). Two fits, both on run 2 TRAIN only, so the
rule is fold-invariant:
  E  (spec) fair-value-jump events, label alive at match (depth.py events);
  R  firing-like rows (v1_L0 prediction >= 2 c on a side), label = that side's seen level
     alive at match (depth.py y_alive_*): the population the arms actually decide on.
Each has a size-only control (log q_seen alone) for kill test (1).

    OMP_NUM_THREADS=2 nice -n 10 python3 -m research.predict.improve.cand.<c4 package>.clock"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from ...diag.calibration.ctx.load import ctx
from ...harness import windows as W
from ...harness.api import Market
from . import KNOWN, OUT, SPAN, assert_open, depth

FEATS = ("lq", "ltsc", "am", "lpm")
PATH = OUT / "clock.json"


def ahat(dep: dict, times, prior: float) -> np.ndarray:
    """Market memory at each time: EWMA of the outcomes of events known by then."""
    te = dep["t_e"]
    a = np.empty(len(te) + 1)
    a[0], al = prior, 2.0 / (SPAN + 1)
    for k, o in enumerate(dep["ealive"].astype(float)):
        a[k + 1] = a[k] + al * (o - a[k])
    return a[np.searchsorted(te + KNOWN, np.asarray(times, float), "right")]


def market(i: int) -> Market:
    mk = W._markets()
    assert_open(mk.start[i])
    return Market(i, {"start": float(mk.start[i]), "end": float(mk.end[i])})


def row_inputs(mk: Market, dep: dict | None = None) -> dict:
    """Decision-time inputs of every tab row (no label is read here)."""
    dep = dep if dep is not None else depth.load(mk.id)
    tab = mk.tab
    t = tab["t"].to_numpy(float)
    dep = dict(dep, t_e=t[dep["ek"]])
    c = ctx(mk.id, len(tab))
    return {"t": t, "dep": dep, "ltsc": np.log1p(np.clip(tab["pm_tsc"].to_numpy(float), 0, 600)),
            "lpm": np.log1p(np.asarray(c["pm60"], float)),
            "qa": dep["qa"].astype(float), "qa2": dep["qa2"].astype(float),
            "qb": dep["qb"].astype(float), "qb2": dep["qb2"].astype(float)}


def design(lq, ltsc, am, lpm) -> np.ndarray:
    return np.column_stack([lq, np.nan_to_num(ltsc), am, np.nan_to_num(lpm)])


def p_alive(coef: dict, X: np.ndarray, size_only: bool = False) -> np.ndarray:
    if size_only:
        z = coef["s0"] + coef["s1"] * X[:, 0]
    else:
        mu, sd = np.array(coef["mu"]), np.array(coef["sd"])
        z = coef["b0"] + ((X - mu) / sd) @ np.array(coef["b"])
    return 1.0 / (1.0 + np.exp(-z))


def frames(i: int, prior: float) -> tuple[pd.DataFrame, pd.DataFrame]:
    """(events, firing-like rows) of market i with inputs and labels, for fitting / AUC."""
    mk = market(i)
    r = row_inputs(mk)
    dep, k = r["dep"], r["dep"]["ek"]
    sz = np.where(dep["edir"] > 0, r["qa"][k], r["qb"][k])
    ev = pd.DataFrame({"m": i, "y": dep["ealive"], "egap": dep["egap"],
                       "lq": np.log1p(sz), "ltsc": r["ltsc"][k], "lpm": r["lpm"][k],
                       "am": ahat(dep, dep["t_e"] - 1e-6, prior) - prior})
    ev = ev[dep["esize"] > 0]
    pu, pdn = mk.pred("v1", 0)
    side = np.where(pu >= pdn, 1, -1)
    w = np.flatnonzero(np.maximum(pu, pdn) >= 0.02)
    q = np.where(side > 0, r["qa"], r["qb"])[w]
    y = np.where(side > 0, dep["y_alive_a"], dep["y_alive_b"])[w]
    rows = pd.DataFrame({"m": i, "y": y, "edge": np.maximum(pu, pdn)[w], "lq": np.log1p(q),
                         "ltsc": r["ltsc"][w], "lpm": r["lpm"][w],
                         "am": ahat(dep, r["t"][w], prior) - prior})
    return ev, rows[q > 0]


def _auc(y, s) -> float:
    from sklearn.metrics import roc_auc_score
    return float(roc_auc_score(y, s)) if 0 < np.mean(y) < 1 else np.nan


def _fit(df: pd.DataFrame) -> dict:
    from sklearn.linear_model import LogisticRegression
    X = design(df["lq"], df["ltsc"], df["am"], df["lpm"])
    mu, sd = X.mean(0), X.std(0) + 1e-9
    m = LogisticRegression(C=10.0, max_iter=1000).fit((X - mu) / sd, df["y"])
    s = LogisticRegression(C=10.0, max_iter=1000).fit(X[:, :1], df["y"])
    return {"b0": float(m.intercept_[0]), "b": m.coef_[0].tolist(), "mu": mu.tolist(), "sd": sd.tolist(),
            "s0": float(s.intercept_[0]), "s1": float(s.coef_[0][0]), "n": int(len(df)), "rate": float(df["y"].mean())}


def _score(coef: dict, df: pd.DataFrame) -> dict:
    X = design(df["lq"], df["ltsc"], df["am"], df["lpm"])
    p, ps = p_alive(coef, X), p_alive(coef, X, True)
    return {"n": int(len(df)), "rate": float(df["y"].mean()), "auc": _auc(df["y"], p), "auc_size": _auc(df["y"], ps),
            "share_p_lt_0.3": float((p < 0.3).mean())}


def main() -> None:
    wins = ("train", "select", "dev3", "test3r1", "ext")
    pre = pd.concat([frames(i, 0.5)[0] for i in W.ids("train")])      # base rate for the prior
    prior = float(pre["y"].mean())
    got = {w: [frames(i, prior) for i in W.ids(w)] for w in wins}
    E = {w: pd.concat([a for a, _ in v]) for w, v in got.items()}
    R = {w: pd.concat([b for _, b in v]) for w, v in got.items()}
    out = {"prior": prior, "known_s": KNOWN, "span": SPAN}
    for tag, D in (("E", E), ("R", R)):
        coef = _fit(D["train"])
        sc = {w: _score(coef, D[w]) for w in wins}
        sc["select+dev3"] = _score(coef, pd.concat([D["select"], D["dev3"]]))
        sc["test3r1+ext"] = _score(coef, pd.concat([D["test3r1"], D["ext"]]))
        out[tag] = {"coef": coef, "scores": sc}
        print(tag, json.dumps({k: v for k, v in sc.items()}, indent=0), flush=True)
    OUT.mkdir(parents=True, exist_ok=True)
    PATH.write_text(json.dumps(out, indent=1))


def load() -> dict:
    return json.loads(PATH.read_text())


if __name__ == "__main__":
    main()
