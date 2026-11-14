"""All orders of one market through every hold scenario.

Scenarios: `paper` (150 ms + 10 ms survival window, the research simulator's rule), `nohold`
(3 ms, decision -> send only), `q10..q90` (fixed quantiles of the live hold), `real` (each
order draws its own hold from the 195 live values; mean of NDRAW draws). Our own takes are
subtracted for 3 s per (arm, scenario, limit), as the paper bot does (60 sh takes; smaller
sizes reuse them). 10 s markout = side-frame venue mid at match + 10 s (capped at end + 2 s;
the outcome where the book has no mid) after the 0.07 p (1 - p) taker fee; `res` = held to
resolution."""
from __future__ import annotations

import numpy as np

from research.strategy import DT
from research.strategy.sim.grid import Book, _replay

from .. import LIMS, SIZES
from .feats import Ctx, features
from .ladder import fee, istar, ladder, limit_idx, sweep, takes

NDRAW, MEMORY = 16, 3.0
Q60 = SIZES.index(60.0)
K2 = LIMS.index("k2")


def scenarios(hold: np.ndarray) -> dict:
    q = {f"q{p}": float(np.percentile(hold, p)) for p in (10, 25, 50, 75, 90)}
    return {"paper": (0.150, 0.010), "nohold": (0.003, 0.0), **{k: (v, 0.0) for k, v in q.items()}}


def _side_mid(book: Book, g: int, side: int) -> float:
    m = float(book.mid(g))
    return m if side > 0 else 1 - m


def _one(book, c, o, lad, h, J, mem, won):
    """One order at hold h: (sh, cost, fee) per (limit, size), side-frame mark, extras."""
    cols, px, s_idx, lim = lad
    g0, g1 = int(book.g_ceil(o.t + h)), int(book.g_ceil(o.t + h + J))
    base = book.size[g0:g1 + 1, cols].min(axis=0).astype(float)
    sh, cost, fe = (np.zeros((len(LIMS), len(SIZES))) for _ in range(3))
    for li, hi in enumerate(lim):
        a = base.copy()
        mem[li] = [x for x in mem[li] if x[0] > o.t - MEMORY]
        for _, col, x in mem[li]:
            j = np.flatnonzero(cols == col)
            if len(j):
                a[j[0]] = max(0.0, a[j[0]] - x)
        s1, c1, f1 = sweep(a, px, lim[li:li + 1])
        sh[li], cost[li], fe[li] = s1[0], c1[0], f1[0]
        if hi >= 0:
            mem[li] += [(o.t, col, x) for col, x in takes(a, cols, hi, SIZES[Q60])]
    mid = _side_mid(book, int(book.g_ceil(min(o.t + h + 10, o.end + 2))), int(o.side))
    mk = mid if mid == mid else won
    gt = int(book.g_ceil(o.t))
    lc = cols[:s_idx + 3]
    d_t, d_m = book.size[gt, lc].astype(float), book.size[g0, lc].astype(float)
    rem = np.maximum(d_t - d_m, 0).sum()
    best_t = np.flatnonzero(book.size[gt, cols] > 0)
    i1, i60 = istar(base, s_idx)
    ex = {"dep_t": d_t.sum(), "dep_m": d_m.sum(), "removed": rem,
          "traded": min(c.trades_on(lc, o.t, o.t + h), rem),
          "ask_m": o.seen + i1 / 100 if i1 == i1 else np.nan,
          "ask_t": px[best_t[0]] if len(best_t) else np.nan,
          "mid_t": _side_mid(book, gt, int(o.side)), "mid_m": _side_mid(book, g0, int(o.side)),
          "mk": mk, "mk_inst": mk - o.seen - fee(o.seen), "istar1": i1, "istar60": i60}
    return sh, cost, fe, ex


def run_market(m: dict, orders, hold: np.ndarray, seed: int) -> list[dict]:
    meta = m["meta"]
    t0 = meta["start"] - 2
    book = Book(m["ev"], t0, meta["end"] + 2, m["gaps"])
    ev = m["ev"]
    rsz = _replay(ev["t"], ev["side"], ev["tick"].astype(np.int64), ev["size"], t0, book.n)
    c = Ctx(m, rsz, t0, DT)
    sc = scenarios(hold)
    rng = np.random.default_rng(seed)
    rows = []
    for arm, g in orders.groupby("arm"):
        mems = {s: [[] for _ in LIMS] for s in list(sc) + [f"r{i}" for i in range(NDRAW)]}
        for o in g.sort_values("t").itertuples():
            cols, px, s_idx = ladder(int(o.side), o.seen)
            lad = (cols, px, s_idx, limit_idx(o, len(cols), s_idx))
            won = o.outcome if o.side > 0 else 1 - o.outcome
            base = {"arm": arm, "slug": o.slug, "t": o.t, "side": int(o.side), "seen": o.seen, "edge": o.edge,
                    "paper_fill": o.fill_sh, "paper_cost": o.cost, "paper_mk10": o.mk10, "won": won,
                    **features(c, o, cols, s_idx)}
            for li, name in enumerate(LIMS):
                base[f"lim_{name}"] = px[lad[3][li]] if lad[3][li] >= 0 else 0.0
            res = {s: [_one(book, c, o, lad, h, J, mems[s], won)] for s, (h, J) in sc.items()}
            res["real"] = [_one(book, c, o, lad, h, 0.0, mems[f"r{i}"], won)
                           for i, h in enumerate(rng.choice(hold, NDRAW))]
            for s, rs in res.items():
                r = dict(base, scen=s)
                sh, cost, fe = (np.mean([x[j] for x in rs], axis=0) for j in range(3))
                mk = np.mean([x[3]["mk"] for x in rs])   # same order, marks differ only by hold
                mkv = np.mean([x[0] * x[3]["mk"] for x in rs], axis=0)
                for li, name in enumerate(LIMS):
                    for qi, q in enumerate(SIZES):
                        r[f"sh_{name}_{int(q)}"] = sh[li, qi]
                        r[f"cost_{name}_{int(q)}"] = cost[li, qi]
                        r[f"pnl_{name}_{int(q)}"] = mkv[li, qi] - cost[li, qi] - fe[li, qi]
                    r[f"res_{name}_60"] = sh[li, Q60] * won - cost[li, Q60] - fe[li, Q60]
                    r[f"fillp_{name}"] = float(np.mean([x[0][li, Q60] > 0 for x in rs]))
                for key in rs[0][3]:
                    v = [x[3][key] for x in rs]
                    r[key] = float(np.nanmean(v)) if any(z == z for z in v) else np.nan
                r["istar1_nan"] = float(np.mean([x[3]["istar1"] != x[3]["istar1"] for x in rs]))
                r["mk_mean"] = mk
                rows.append(r)
    return rows
