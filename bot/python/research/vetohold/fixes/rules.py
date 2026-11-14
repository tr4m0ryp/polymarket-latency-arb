"""The fix rules: each maps per-order predictions to (send mask, limit offset i, size) and
reads the order's expected PnL / cost under the real hold from the replay rows.

  plain     every veto order at i = 0 (limit = seen, the binding live rule), 60 sh
  fixed     every order at seen + i c, i chosen on selection hours
  surv      (i)  send iff P(fill at seen) x E[value per filled share] >= tau
  istar     (ii) predicted needed offset i*; limit seen + ceil(i* + pad) (<= 10 c),
                 send iff model edge - i* >= tau
  size      (iii) size = largest of 5/15/30/60 sh <= predicted surviving depth x frac
  fresh     (iv-a) send iff the venue-stamp lag of the last 50 book messages <= tau (s)
  ev        (iv-b) send iff a direct regression of PnL per $ under the hold >= tau
  surv_size (i) + (iii)"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .. import KS, SIZES


def take(d: pd.DataFrame, send: np.ndarray, k: np.ndarray, q: np.ndarray, kind: str = "pnl") -> pd.DataFrame:
    """Per order: pnl (10 s markout or `res` to resolution) / cost / fill under the chosen
    limit and size (0 when not sent)."""
    pnl, cost, fill = np.zeros(len(d)), np.zeros(len(d)), np.zeros(len(d))
    for kk in KS:
        for qq in SIZES:
            m = send & (k == kk) & (q == qq)
            if not m.any():
                continue
            col = f"{kind}_k{kk}_{int(qq)}" if kind == "pnl" or qq == 60 else None
            pnl[m] = d[col].to_numpy()[m] if col else np.nan
            cost[m] = d[f"cost_k{kk}_{int(qq)}"].to_numpy()[m]
            fill[m] = d[f"fillp_k{kk}"].to_numpy()[m]
    return pd.DataFrame({"slug": d["slug"].to_numpy(), "pnl": pnl, "cost": cost, "sent": send, "fill": fill})


def size_of(dep: np.ndarray, frac: float) -> np.ndarray:
    cap = dep * frac
    q = np.full(len(dep), SIZES[0])
    for s in SIZES:
        q = np.where(cap >= s, s, q)
    return q


def plan(rule: str, d: pd.DataFrame, pr: dict, par: dict):
    n = len(d)
    send, k, q = np.ones(n, bool), np.full(n, 0), np.full(n, 60.0)
    if rule == "fixed":
        k = np.full(n, int(par["i"]))
    if rule in ("surv", "surv_size"):
        send = pr["p_surv"] * pr["v_fill"] >= par["tau"]
    if rule == "istar":
        ih = pr["istar"]
        send = d["edge"].to_numpy() - ih / 100 >= par["tau"]
        k = np.clip(np.ceil(ih + par["pad"] - 1e-9), 0, max(KS)).astype(int)
    if rule in ("size", "surv_size"):
        q = size_of(pr["dep_m"], par["frac"])
    if rule == "fresh":
        send = d["f_rlag50"].to_numpy() <= par["tau"]
    if rule == "ev":
        send = pr["ev"] >= par["tau"]
    return send, k, q


def apply(rule: str, d: pd.DataFrame, pr: dict, par: dict, kind: str = "pnl") -> pd.DataFrame:
    return take(d, *plan(rule, d, pr, par), kind=kind)
