"""Summarise a paper run per arm and compare it with the replay simulator on the same markets.

    python3 -m btclat.paper.report --run <run> [--raw] [--no-sim]

Per arm: orders and fills per hour, fills/day, resolution c/$, 10 s markout c/$ and $/day,
paired 10 s markout gain vs micf with a 95% market-bootstrap CI (research/strategy/eval/
metrics.py). Against the simulator: fills, mean fill price and shares per arm, ratio paper /
sim (target within 25%), and fills matched one to one (same market, side, decision within
5 ms). Writes data/paper/<run>/report.md."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys

import numpy as np
import pandas as pd

from research.predict.report.md import md
from research.strategy.eval.metrics import paired, table

from . import load
from .sim import PAPER


def summary(f: pd.DataFrame, df: pd.DataFrame, mk: np.ndarray) -> tuple[pd.DataFrame, pd.DataFrame]:
    agg = load.aggregate(f)
    t = table(agg, mk)
    hours = len(mk) * 300 / 3600
    n_ord = df.groupby("arm").size()
    t["orders_h"] = [n_ord.get(a, 0) / hours for a in t["arm"]]
    t["fills_h"] = t["fills_day"] / 24
    t["mk10_day"] = [agg[agg["arm"] == a]["mk10v"].sum() / (len(mk) / 288) for a in t["arm"]]
    rows = []
    base = agg[agg["arm"] == "micf"]
    for arm, g in agg.groupby("arm"):
        if arm != "micf" and len(base):
            p = paired(g, base, mk, col="mk10v")
            rows.append({"arm": arm, "mk10_gain_day": p["diff_day"], "lo": p["lo"], "hi": p["hi"]})
    cols = ["arm", "orders_h", "fills_h", "fills_day", "c_per_usd", "mk10_c", "mk10_day", "win"]
    return t[cols], pd.DataFrame(rows)


def versus(f: pd.DataFrame, s: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for arm in sorted(set(f["arm"]) | set(s.get("arm", pd.Series(dtype=str)))):
        a, b = f[f["arm"] == arm], s[s["arm"] == arm] if len(s) else s
        n_match, dpx = 0, []
        for (slug, side), g in a.groupby(["slug", "side"]):
            h = b[(b["slug"] == slug) & (b["side"] == side)] if len(b) else b
            for t, px in zip(g["t"], g["px"]):
                j = np.flatnonzero(np.abs(h["t"].to_numpy() - t) < 0.005) if len(h) else []
                if len(j):
                    n_match += 1
                    dpx.append(100 * (px - h["px"].to_numpy()[j[0]]))
        r = {"arm": arm, "paper_fills": len(a), "sim_fills": len(b),
             "fills_ratio": len(a) / len(b) if len(b) else np.nan,
             "paper_px": a["px"].mean(), "sim_px": b["px"].mean() if len(b) else np.nan,
             "paper_sh": a["shares"].mean(), "sim_sh": b["shares"].mean() if len(b) else np.nan,
             "matched": n_match, "matched_dpx_c": float(np.mean(np.abs(dpx))) if dpx else np.nan}
        r["px_ratio"] = r["paper_px"] / r["sim_px"] if r["sim_px"] else np.nan
        r["within_25pct"] = bool(abs(r["fills_ratio"] - 1) <= 0.25 and abs(r["px_ratio"] - 1) <= 0.25)
        rows.append(r)
    return pd.DataFrame(rows)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    ap.add_argument("--raw", action="store_true", help="simulate from the run's own recording")
    ap.add_argument("--no-sim", action="store_true")
    a = ap.parse_args()
    root = PAPER / a.run
    df_all = load.orders(root)
    df = df_all[df_all["outcome"].notna()]          # markets not yet resolved are left out
    f = load.fills(df)
    f["L"] = (f["L"] * 1000).round().astype(int)
    mk = np.array(sorted(df.loc[df["outcome"].notna(), "slug"].unique()))
    (root / "slugs.json").write_text(json.dumps(list(mk)))
    t, p = summary(f, df, mk)
    out = [f"# Paper run {a.run}", "", f"markets {len(mk)} ({len(mk) * 5 / 60:.1f} h), orders {len(df)}, "
           f"fills {len(f)}, gap-skipped {int(df['gap'].sum())}, unresolved orders {len(df_all) - len(df)}", "", md(t, 2), "",
           "Paired 10 s markout gain vs micf ($/day, 95% market bootstrap):", "", md(p, 1) if len(p) else "(none)"]
    if not a.no_sim:
        L = int(f["L"].iloc[0]) if len(f) else 0
        cmd = [sys.executable, "-m", "btclat.paper.report.sim", "--run", a.run, "--L", str(L)]
        subprocess.run(cmd + (["--raw"] if a.raw else []), check=True)
        s = pd.read_pickle(root / "sim-fills.pkl")
        v = versus(f, s)
        out += ["", f"Paper vs replay simulator, same markets, L = {L} ms:", "", md(v, 3)]
    text = "\n".join(out) + "\n"
    (root / "report.md").write_text(text)
    print(text)


if __name__ == "__main__":
    main()
