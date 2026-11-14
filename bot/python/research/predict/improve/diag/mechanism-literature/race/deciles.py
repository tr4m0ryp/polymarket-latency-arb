"""Decile tables of the race on a stale Polymarket quote (events.pkl from `build`).

    python3 research/predict/improve/diag/mechanism-literature deciles

Activity index = perp bookTicker msgs/s over the 10 s before the event (cut points from the
events; placebos get the same cuts). Also by Polymarket's own book-message rate, fair-value
churn and surprise (move / 30 s churn), and calm (D1-3) vs busy (D8-10) at a fixed stale-level
size tercile, since level size drives requote time (ols_lag_q.csv). Market bootstrap CIs."""
from __future__ import annotations

import numpy as np
import pandas as pd

from research.predict.report.md import md
from .. import OUT, SEALED, WORK
from ..data.guard import assert_allowed
from .cause import prep, race_row, requote_row, value_row
from .memory import memory_ols, memory_table
from .selection import selection_ols, survival_table

DIR = OUT / "diag-mechanism-literature"
INDEX = {"pmsg10": "perp msgs/s", "pmupd10": "Polymarket book msgs/s", "cvol30": "fair churn c/30s",
         "surprise": "move / 30 s churn"}


def cut(ev: pd.DataFrame, pl: pd.DataFrame, col: str, q: int = 10):
    e = np.quantile(ev[col].dropna(), np.linspace(0, 1, q + 1))
    e[0], e[-1] = -np.inf, np.inf
    lab = lambda x: pd.cut(x, np.unique(e), labels=False)  # noqa: E731
    rng = [f"D{k + 1} {ev.loc[lab(ev[col]) == k, col].min():.3g}-{ev.loc[lab(ev[col]) == k, col].max():.3g}"
           for k in range(q)]
    return lab(ev[col]), lab(pl[col]), rng


def table(ev, pl, be, bp, rng, fn) -> pd.DataFrame:
    rows = []
    for k in range(len(rng)):
        g = ev[be == k]
        r = {"decile": rng[k]}
        r.update(fn(g, pl[bp == k]) if fn is race_row else fn(g))
        rows.append(r)
    return pd.DataFrame(rows)


def calm_busy(ev: pd.DataFrame, col: str, B: int = 600, seed: int = 11) -> list[dict]:
    """Median requote (ms) and P(alive at our match), busy D8-10 minus calm D1-3, per size tercile."""
    e = ev.dropna(subset=[col]).copy()
    q = np.quantile(e[col], [0.3, 0.7])
    e["st"] = np.where(e[col] <= q[0], 0, np.where(e[col] > q[1], 1, -1))
    e = e[e["st"] >= 0]
    st = np.quantile(ev["size0"].dropna(), [1 / 3, 2 / 3])
    e["sz"] = np.where(e["size0"] <= st[0], "S", np.where(e["size0"] <= st[1], "M", "L"))
    rows, rng = [], np.random.default_rng(seed)
    for sz in ("S", "M", "L", "all"):
        g = e if sz == "all" else e[e["sz"] == sz]
        lq = g["lag_q"].clip(upper=10.0).fillna(10.0).to_numpy()
        al, st_, ms = g["c_alive"].to_numpy(), g["st"].to_numpy(), g["m"].to_numpy()
        um = np.unique(ms)
        groups = [np.flatnonzero(ms == m) for m in um]

        def stat(ix):
            c, b = ix[st_[ix] == 0], ix[st_[ix] == 1]
            return 1000 * (np.median(lq[b]) - np.median(lq[c])), al[b].mean() - al[c].mean()
        pt = stat(np.arange(len(g)))
        bs = np.array([stat(np.concatenate([groups[j] for j in rng.integers(0, len(um), len(um))])) for _ in range(B)])
        lo, hi = np.nanpercentile(bs, 2.5, 0), np.nanpercentile(bs, 97.5, 0)
        c, b = g[g["st"] == 0], g[g["st"] == 1]
        rows.append({"index": INDEX[col], "level size": sz, "calm n": len(c), "busy n": len(b),
                     "calm requote ms": round(1000 * c["lag_q"].median()), "busy requote ms": round(1000 * b["lag_q"].median()),
                     "busy - calm ms [CI]": f"{pt[0]:+.0f} [{lo[0]:+.0f}, {hi[0]:+.0f}]",
                     "calm alive": round(c["c_alive"].mean(), 2), "busy alive": round(b["c_alive"].mean(), 2),
                     "alive diff [CI]": f"{pt[1]:+.2f} [{lo[1]:+.2f}, {hi[1]:+.2f}]"})
    return rows


def show(title: str, t: pd.DataFrame, name: str) -> None:
    t.to_csv(DIR / f"{name}.csv", index=False)
    print(f"\n### {title}\n")
    print(md(t, 3))


def main() -> None:
    np.seterr(all="ignore")
    raw = pd.read_pickle(WORK / "events.pkl")
    assert_allowed(raw["start"], "events")
    assert raw["start"].max() < SEALED and raw["T0"].max() < SEALED
    d = prep(raw)
    d["surprise"] = d["c0"].abs() / np.maximum(d["cvol30"], 0.5)
    ev, pl = d[d["placebo"] == 0], d[d["placebo"] == 1]
    print("events", len(ev), "placebos", len(pl), "markets", ev["m"].nunique())
    DIR.mkdir(parents=True, exist_ok=True)
    be, bp, rng = cut(ev, pl, "pmsg10")
    show("maker requote by perp msgs/s decile", table(ev, pl, be, bp, rng, requote_row), "dec_requote_pmsg10")
    show("race on the stale quote by perp msgs/s decile", table(ev, pl, be, bp, rng, race_row), "dec_race_pmsg10")
    show("our L = 0 value and survival selection by perp msgs/s decile", table(ev, pl, be, bp, rng, value_row),
         "dec_value_pmsg10")
    for col in ("pmupd10", "cvol30", "surprise"):
        be, bp, rng = cut(ev, pl, col)
        show(f"maker requote by {INDEX[col]} decile", table(ev, pl, be, bp, rng, requote_row), f"dec_requote_{col}")
        p_, bp_ = (pl.iloc[:0], bp.iloc[:0]) if col == "surprise" else (pl, bp)   # placebo surprise ~0 by construction
        show(f"race by {INDEX[col]} decile", table(ev, p_, be, bp_, rng, race_row), f"dec_race_{col}")
    rows = [r for col in INDEX for r in calm_busy(ev, col)]
    show("busy (D8-10) minus calm (D1-3) at fixed stale-level size tercile", pd.DataFrame(rows), "calm_busy_by_size")
    show("hold as last look: alive vs gone at our match, by perp msgs/s tercile", survival_table(ev),
         "selection_alive_gone")
    show("OLS of value at the seen price (c) on survival x busy (market-bootstrap CI)", selection_ols(ev),
         "selection_ols")
    show("maker-speed memory: previous event's survival in the same market", memory_table(ev), "memory_pairs")
    show("LPM of alive at our match on previous survival (market-bootstrap CI)", memory_ols(ev), "memory_ols")
    sp = ev[["pmsg10", "pmupd10", "cvol30", "surprise", "size0", "spr0", "abs_c0" if "abs_c0" in ev else "c0"]]
    print("\nSpearman between activity indices\n", sp.corr(method="spearman").round(2).to_string())


if __name__ == "__main__":
    main()
