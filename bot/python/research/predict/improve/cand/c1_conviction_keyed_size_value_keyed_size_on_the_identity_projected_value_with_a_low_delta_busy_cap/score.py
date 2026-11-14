"""Offline scoring of C1 runs from run.py's per-market dumps, with the harness estimators.

- variants(): every variant on every set (fixed variant, no fold choice: a diagnostic).
- cv(): the harness fold protocol re-applied to any subset of variants and any choice
  column (e.g. the 2.5% bound of the gain vs the frozen veto), so a veto-type arm is chosen
  and judged against the frozen veto. Same market bootstrap (paired: 2000 draws, seed 2);
  the gain vs the veto is the paired per-market difference re-bootstrapped."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from ...harness import windows as W
from ...harness.guard import SEALED, assert_allowed
from ...harness.score import metrics, sets

VT, VETO, MICF = "vt_v1_m0.03_any", "vt_v1_m0.02_trigger", "micf"
F = "F|"


def load(d: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    pm, act = pd.read_pickle(d / "per_market.pkl"), pd.read_pickle(d / "activity.pkl")
    assert_allowed(act["start"], "c1 score")
    assert act["start"].max() < SEALED
    return pm, act


def merge(dirs) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Several runs' dumps as one (frozen references taken once)."""
    pms, act = [], None
    for d in dirs:
        pm, a = load(Path(d))
        pms.append(pm if not pms else pm[~pm["arm"].str.startswith(F)])
        act = a if act is None else act
    pm = pd.concat(pms, ignore_index=True).drop_duplicates(["arm", "L", "var", "m"])
    return pm, act


def refs(pm: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Frozen references renamed so metrics.row tags them g_vt, g_micf, g_veto."""
    out = {}
    for name, tag in ((VT, VT), (MICF, MICF), (VETO, "veto")):
        r = pm[pm["arm"] == F + name].copy()
        r["arm"] = tag
        out[tag] = r
    return out


def arm(pm: pd.DataFrame, name: str, ids=None) -> pd.DataFrame:
    keys = [k for k in pm["arm"].unique() if k.split("|", 1)[-1] == name and not k.startswith(F)]
    assert len(keys) == 1, f"variant {name}: keys {keys}"
    a = pm[pm["arm"] == keys[0]]
    return (a if ids is None else a[a["m"].isin(set(ids))]).assign(arm=name)


def names(pm: pd.DataFrame) -> list[str]:
    return sorted(k.split("|", 1)[-1] for k in pm["arm"].unique() if not k.startswith(F))


def frozen_rows(pm, act, Ls=(0, -40), variants=("base", "comp")) -> pd.DataFrame:
    """The three frozen arms on every set, same estimators (the comparison rows)."""
    R = refs(pm)
    arms = {n: pm[pm["arm"] == F + n].assign(arm=n) for n in (VT, VETO, MICF)}
    return metrics.table(arms, R, sets.build(act), Ls=Ls, variants=variants)


def variants(pm, act, which=None, Ls=(0, -40), vars_=("base", "comp"), only=None) -> pd.DataFrame:
    S = sets.build(act)
    S = {k: v for k, v in S.items() if only is None or k in only}
    arms = {n: arm(pm, n) for n in (which or names(pm))}
    return metrics.table(arms, refs(pm), S, Ls=Ls, variants=vars_)


def choose(tab: pd.DataFrame, col: str) -> str:
    """Harness rule (score/select.py) on any column: markout > 0 and >= 100 fills/day floor."""
    ok = (tab["mk10_c"] > 0) & (tab["fills_day"] >= 100)
    pool = tab[ok] if ok.any() else tab
    return str(pool.sort_values([col, "arm"], ascending=[False, True]).iloc[0]["arm"])


def cv(pm, act, which, col="g_vt_lo", sel_L=0, Ls=(0, -40), vars_=("base", "comp"), label="candidate",
       sel_var="base", only=None):
    """Per fold: choose among `which` on the choose windows (L = sel_L, base) by `col`, score the
    pick on the evaluate windows; every market judged by a variant chosen without it."""
    R = refs(pm)
    parts, picks = [], {}
    for f, (ch, ev) in W.FOLDS.items():
        cid = sorted(i for w in ch for i in W.ids(w))
        eid = sorted(i for w in ev for i in W.ids(w))
        t = metrics.table({n: arm(pm, n, cid) for n in which}, R, {f"{f}:choose": cid},
                          Ls=(sel_L,), variants=(sel_var,))
        picks[f] = choose(t, col)
        parts.append(arm(pm, picks[f], eid).assign(arm=label))
    St = {k: v for k, v in sets.build(act).items() if only is None or k in only}
    tab = metrics.table({label: pd.concat(parts, ignore_index=True)}, R, St, Ls=Ls, variants=vars_)
    return tab, picks


def pair(pm, act, a: str, b: str, sets_=("CV:all", "A:eval", "B:eval", "CV:busyQ", "A:busy15"),
         Ls=(0, -40), vars_=("base", "comp")) -> pd.DataFrame:
    """Paired gain of fixed variant a over fixed variant b (or a frozen arm name), per set."""
    S_ = sets.build(act)
    fz = {VT, VETO, MICF}
    get = lambda n: pm[pm["arm"] == F + n].assign(arm=n) if n in fz else arm(pm, n)  # noqa: E731
    A, B = get(a), get(b)
    rows = []
    for s in sets_:
        ids = S_[s]
        for L in Ls:
            for v in vars_:
                sel = lambda x: x[(x["L"] == L) & (x["var"] == v) & x["m"].isin(set(ids))]  # noqa: E731
                p = metrics._paired_safe(sel(A), sel(B), np.asarray(sorted(ids)))
                rows.append({"a": a, "b": b, "set": s, "L": L, "var": v, "gain": p["diff_day"],
                             "lo": p["lo"], "hi": p["hi"], "p_le0": p["p_le0"]})
    return pd.DataFrame(rows)
