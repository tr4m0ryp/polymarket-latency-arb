"""Reproduction check: the harness's frozen references against the report's own simulation
outputs, per market (agg-<tag>.pkl) and per table row (score-<tag>.csv, paired-<tag>.csv).

    python3 -m research.predict.improve.harness.check

Base fills vs sel1 / dev1 / final / ext; the 50 ms competition variant vs final_comp (L = 0,
test3r1 only: the only window and L the report ran it on)."""
from __future__ import annotations

import pickle

import numpy as np
import pandas as pd

from ... import OUT
from ...report.md import md
from . import windows as W
from .frozen import FROZEN
from .score.metrics import row
from .sim.frozen_cache import DIR, PREFIX

COLS = ("n", "cost", "pnl", "mk10v")
RUNS = [("select", "sel1", "base"), ("dev3", "dev1", "base"), ("test3r1", "final", "base"),
        ("ext", "ext", "base"), ("test3r1", "final_comp", "comp")]


def _frozen() -> pd.DataFrame:
    with open(DIR / "frozen.pkl", "rb") as fh:
        a = pickle.load(fh)["agg"]
    return a.assign(arm=a["arm"].str[len(PREFIX):])


def per_market(h: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for w, tag, var in RUNS:
        o = pd.read_pickle(OUT / f"agg-{tag}.pkl")
        ids = W.ids(w)
        for arm in FROZEN:
            for L in sorted(set(o["L"]) & {0, -40}):
                a = h[(h["arm"] == arm) & (h["L"] == L) & (h["var"] == var)].set_index("m").reindex(ids)
                b = o[(o["arm"] == arm) & (o["L"] == L)].set_index("m").reindex(ids)
                if b["n"].isna().all():
                    continue
                d = {c: float(np.nanmax(np.abs(a[c].fillna(0).to_numpy() - b[c].fillna(0).to_numpy())))
                     for c in COLS}
                rows.append({"window": w, "tag": tag, "arm": arm, "L": L, "mkts_traded": int(b["n"].notna().sum()),
                             **{f"max|d {c}|": d[c] for c in COLS}})
    return pd.DataFrame(rows)


def per_row(h: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for w, tag, var in RUNS:
        sc = pd.read_csv(OUT / f"score-{tag}.csv").set_index(["arm", "L"])
        pr = pd.read_csv(OUT / f"paired-{tag}.csv").set_index(["arm", "L"])
        ids = W.ids(w)
        for arm in FROZEN:
            for L in (0, -40):
                if (arm, L) not in sc.index:
                    continue
                sel = lambda x: x[(x["L"] == L) & (x["var"] == var) & x["m"].isin(ids)]  # noqa: E731
                r = row(sel(h[h["arm"] == arm]), {"micf": sel(h[h["arm"] == "micf"])}, ids)
                s = sc.loc[(arm, L)]
                p = pr.loc[(arm, L)] if (arm, L) in pr.index else None
                rows.append({"tag": tag, "arm": arm, "L": L,
                             "fills/day h|r": f"{r['fills_day']:.1f} | {s['fills_day']:.1f}",
                             "mk c/$ h|r": f"{r['mk10_c']:.2f} | {s['mk10_c']:.2f}",
                             "mk $/day h|r": f"{r['mk10_day']:.1f} | {s['mk10_day']:.1f}",
                             "gain vs micf h|r": "" if p is None else
                             f"{r['g_micf']:.1f} [{r['g_micf_lo']:.1f}, {r['g_micf_hi']:.1f}] | "
                             f"{p['mk10_gain_day']:.1f} [{p['lo']:.1f}, {p['hi']:.1f}]"})
    return pd.DataFrame(rows)


def main() -> None:
    h = _frozen()
    a, b = per_market(h), per_row(h)
    print(md(a, 6))
    print(md(b))
    out = OUT / "improve" / "baseline"
    out.mkdir(parents=True, exist_ok=True)
    (out / "reproduction.md").write_text("## Per market, harness vs report simulation\n\n" + md(a, 6)
                                         + "\n## Table rows, harness | report\n\n" + md(b))


if __name__ == "__main__":
    main()
