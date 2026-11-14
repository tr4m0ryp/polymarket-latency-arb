"""report.csv + final2.csv -> data/out/bankroll/caps.md (compact tables for reports/bankroll-caps.md).

    PYTHONPATH=. python3 -m research.bankroll.tables.write"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from .. import OUT

POOL = {"v1_frozen/old/selection": "v1, sel, old", "v1_frozen/old/test": "v1, test, old",
        "G_h250+x/old/test": "v1h, test, old", "G_h250+x/new/test": "v1h, test, new",
        "G_h250+x/fast50/test": "v1h, test, 50 ms", "v1_frozen/new/test": "v1, test, new",
        "G_h250+x/old/selection": "v1h, sel (in-sample), old", "G_h250+x/old/all": "v1h, 48 h, old"}


def row(r) -> dict:
    s = r["start"]
    return {"pool": POOL[r["pool"]], "24h median $": r["b_median"], "p10 $": r["b_p10"], "mean $": r["b_mean"],
            "P(<half) 24h": r["b_p_ruin"], "P(<half) rot": r["r_p_ruin"], "rot median $": r["r_median"],
            "maxDD p90": r["b_maxdd_p90"], "7d median $": r["w_med"], "7d p10 $": r["w_p10"],
            "P(<quarter) 7d": r["w_p_below_quarter"], "orders/h": r["b_orders_h"], "fills/h": r["b_fills_h"],
            "worst mkt % E": r["w_worst_mkt_frac"] * 100, "worst mkt $ p99": r["b_worst_mkt_p99_$"],
            "both sides": r["b_both_sides"], "pair locks": r["b_pair_locks"], "start": s}


def fmt(df: pd.DataFrame) -> str:
    cols = list(df.columns)
    out = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for _, r in df.iterrows():
        cells = []
        for c in cols:
            v = r[c]
            if isinstance(v, (float, np.floating)):
                cells.append(f"{v:.3f}" if abs(v) < 1 and v != 0 else f"{v:,.1f}" if abs(v) < 100 else f"{v:,.0f}")
            else:
                cells.append(str(v))
        out.append("| " + " | ".join(cells) + " |")
    return "\n".join(out)


def main():
    rep = pd.read_csv(OUT / "report.csv")
    pick = json.loads((OUT / "final2.json").read_text())
    md = [f"# Bankroll caps: tables\n\npick: {pick}\n"]
    for tag, g in rep.groupby("tag", sort=False):
        md += [f"\n## {tag}: {g.iloc[0]['label']}\n", fmt(pd.DataFrame([row(r) for _, r in g.iterrows()]))]
    f2 = pd.read_csv(OUT / "final2.csv")
    keep = ["label", "feasible", "b_median", "b_p10", "b_p_ruin", "r_p_ruin", "w_med", "w_p10", "w_p_below_quarter",
            "b_fills_h", "w_worst_mkt_frac"]
    md += ["\n## stage 2 finalists (selection hours, v1, old hold)\n", fmt(f2[keep].head(25))]
    (OUT / "caps.md").write_text("\n".join(md) + "\n")
    print("\n".join(md)[:6000])


if __name__ == "__main__":
    main()
