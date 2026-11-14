"""(a) Same Binance id on several connections: per-stream arrival delay vs the first arrival.

Clock-free: all stamps are CLOCK_MONOTONIC on one box. Only ids every stream in the group saw
are compared (both connections up). Also the depth@100ms diff vs the bookTicker carrying the same
last update id, and the gain of fanning in N connections over one."""
from __future__ import annotations

import numpy as np

from parse import load

GROUPS = {
    "spot trade id": (0, ["spot_comb_a", "spot_comb_b", "spot_trade_a", "spot_trade_b",
                          "spot_vision", "spot_443"]),
    "spot bookTicker u": (1, ["spot_comb_a", "spot_comb_b", "spot_book_a", "spot_book_b",
                              "spot_vision", "spot_443"]),
    "perp trade id": (0, ["perp_pub_a", "perp_pub_b"]),
    "perp bookTicker u": (1, ["perp_pub_a", "perp_pub_b", "perp_book"]),
}
BASE = "spot_comb_a"


def q(x, ps=(50, 90, 99)) -> dict:
    x = np.asarray(x, float)
    if not len(x):
        return {"n": 0}
    return {"n": int(len(x)), "mean": round(float(x.mean()), 3),
            **{f"p{p}": round(float(np.percentile(x, p)), 3) for p in ps}}


def first_arrival(run, names: list[str], kind: int) -> dict[str, dict[int, int]]:
    out = {}
    for n in names:
        d = load(run, n)
        m = d["kind"] == kind
        k, t = d["key"][m], d["mono"][m]
        o = np.argsort(t, kind="stable")[::-1]  # dict keeps the earliest per id
        out[n] = dict(zip(k[o].tolist(), t[o].tolist()))
    return out


def matrix(run, names: list[str], kind: int) -> tuple[np.ndarray, np.ndarray]:
    fa = first_arrival(run, names, kind)
    common = set.intersection(*(set(v) for v in fa.values())) if fa else set()
    ids = np.array(sorted(common), dtype=np.int64)
    T = np.array([[fa[n][i] for i in ids] for n in names], dtype=np.int64).reshape(len(names), -1)
    return ids, T


def group_stats(run, names: list[str], kind: int) -> dict:
    ids, T = matrix(run, names, kind)
    if T.shape[1] == 0:
        return {"n": 0}
    first = T.min(0)
    res = {"n": int(T.shape[1]), "streams": {}}
    for i, n in enumerate(names):
        lag = (T[i] - first) / 1e6
        res["streams"][n] = {"lag_vs_first_ms": q(lag), "first_share": round(float(
            (T[i] == first).mean()), 3), "late_10ms_share": round(float((lag > 10).mean()), 4)}
    if BASE in names:  # what fanning in all connections buys over the bot's one connection
        res["fanin_gain_vs_" + BASE + "_ms"] = q((T[names.index(BASE)] - first) / 1e6)
    return res


def depth_vs_book(run) -> dict:
    """depth@100ms diff (last id u) vs the earliest bookTicker with the same u."""
    fa = first_arrival(run, ["spot_book_a", "spot_book_b", "spot_comb_a", "spot_comb_b"], 1)
    best: dict[int, int] = {}
    for v in fa.values():
        for k, t in v.items():
            if t < best.get(k, 1 << 62):
                best[k] = t
    d = load(run, "spot_depth")
    lag = [(t - best[u]) / 1e6 for u, t in zip(d["key"].tolist(), d["mono"].tolist()) if u in best]
    return {"depth_minus_bookticker_ms": q(lag, (10, 50, 90, 99))}


def run_all(run) -> dict:
    out = {g: group_stats(run, names, kind) for g, (kind, names) in GROUPS.items()}
    out["spot depth vs bookTicker"] = depth_vs_book(run)
    return out
