"""Tables and the pre-registered verdict from run.py's per-market rows.

    python3 -m research.predict.inside.report      # data/out/predict/inside/{summary.csv,summary.md,verdict.json}

Per set (dublin, dry, pooled) x size x L x arm x haircut: fill events / h, inserts / h, 10 s
markout c/$ with a 95% market bootstrap CI, $ / day, rebate c/$, resolution $ / day, the
paired 10 s markout $ / day gain vs the baseline arm (no haircut) with its CI, and drop-top-5
(the 5 markets with the largest paired gain removed)."""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from ..report.md import md
from .run import OUTD

DAY = 288           # 5m markets per day


def _boot(n: int, B: int, seed: int) -> np.ndarray:
    return np.random.default_rng(seed).integers(0, n, (B, n))


def rows(agg: pd.DataFrame, cfg: dict, setname: str) -> list[dict]:
    an = cfg["analysis"]
    B, base = an["boot"], an["baseline"]
    out = []
    for (size, L), g in agg.groupby(["size", "L"]):
        ms = np.sort(g["m"].unique())
        n, days = len(ms), len(ms) / DAY
        idx = _boot(n, B, an["seed"])
        bas = g[(g["arm"] == base["arm"]) & (g["hc"] == base["hc"])].set_index("m").reindex(ms)
        for (arm, hc), a in g.groupby(["arm", "hc"]):
            a = a.set_index("m").reindex(ms).fillna(0)
            v, c = a["mk10v"].to_numpy(), a["cost"].to_numpy()
            d = v - bas["mk10v"].fillna(0).to_numpy()
            keep = np.setdiff1d(np.arange(n), np.argsort(d)[::-1][:5])
            kv = np.setdiff1d(np.arange(n), np.argsort(v)[::-1][:5])
            vc = 100 * v[idx].sum(1) / np.maximum(c[idx].sum(1), 1e-9)
            out.append({"set": setname, "size": size, "L": L, "arm": arm, "hc": bool(hc), "markets": n,
                        "fills_h": a["n"].sum() / (n / 12), "ins_h": a["ins"].sum() / (n / 12),
                        "cost_day": c.sum() / days, "mk10_cpd": 100 * v.sum() / max(c.sum(), 1e-9),
                        "lo": np.percentile(vc, 2.5), "hi": np.percentile(vc, 97.5), "usd_day": v.sum() / days,
                        "rebate_cpd": 100 * a["rebate"].sum() / max(c.sum(), 1e-9), "res_day": a["pnl"].sum() / days,
                        "gain_day": d.sum() / days, "g_lo": np.percentile(d[idx].sum(1) / days, 2.5),
                        "g_hi": np.percentile(d[idx].sum(1) / days, 97.5),
                        "gain_drop5": d[keep].sum() / (len(keep) / DAY),
                        "cpd_drop5": 100 * v[kv].sum() / max(c[kv].sum(), 1e-9),
                        "through_share": a["n_src1"].sum() / max(a["n"].sum(), 1)})
    return out


def verdict(t: pd.DataFrame, cfg: dict) -> dict:
    out = {}
    for name, crit in cfg["criteria"].items():
        r = t[(t["set"] == crit["set"]) & (t["size"] == crit["size"]) & (t["L"] == crit["L"])
              & (t["arm"] == crit["arm"]) & (t["hc"] == crit["hc"])]
        if not len(r):
            out[name] = {"pass": None, "why": "no row"}
            continue
        r = r.iloc[0]
        val = float(r[crit["col"]])
        out[name] = {"col": crit["col"], "value": round(val, 3), "threshold": crit["gt"], "pass": bool(val > crit["gt"])}
    prim = [k for k, c in cfg["criteria"].items() if c.get("primary")]
    out["primary_pass"] = all(out[k]["pass"] for k in prim)
    return out


def main() -> None:
    from .prereg import load
    cfg = load()
    parts = {}
    for s in ("dublin", "dry"):
        p = OUTD / f"agg-{s}.pkl"
        if p.exists():
            parts[s] = pd.read_pickle(p)
    r = []
    for s, a in parts.items():
        r += rows(a, cfg, s)
    if len(parts) == 2:   # market ids index each set's own markets.csv: offset the dry run's
        pool = [a.assign(m=a["m"] + 100000 * j) for j, a in enumerate(parts.values())]
        r += rows(pd.concat(pool, ignore_index=True), cfg, "pooled")
    t = pd.DataFrame(r)
    t.to_csv(OUTD / "summary.csv", index=False)
    v = verdict(t, cfg)
    (OUTD / "verdict.json").write_text(json.dumps(v, indent=1))
    cols = ["set", "size", "L", "arm", "hc", "markets", "fills_h", "ins_h", "mk10_cpd", "lo", "hi", "usd_day",
            "gain_day", "g_lo", "g_hi", "gain_drop5", "cpd_drop5", "rebate_cpd", "res_day", "through_share"]
    (OUTD / "summary.md").write_text(md(t[cols], 2) + "\n")
    print(json.dumps(v, indent=1))


if __name__ == "__main__":
    main()
