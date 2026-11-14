"""Score the recalibration simulator run: per window and pooled (dev3 + final + ext), every
arm's fills/day, 10 s markout c/$ and $/day, and the paired 10 s markout $/day gain vs micf
and vs the frozen arm (taker: vt_v1_m3, veto: vt_v1_trig_m3), market-bootstrap CIs. Also checks that the rebuilt frozen arm
reproduces the frozen agg files.

    python3 -m research.predict.improve.diag.calibration.recal.score [--tag recal]"""
from __future__ import annotations

import argparse

import numpy as np
import pandas as pd

from ...... import predict
from ......strategy.eval.metrics import paired, table
from .....report.md import md
from .. import OUT
from ..safe import TAGS, check, start_of

REPRO = {"vt_v1_m3": "vt_v1_m0.03_any", "vt_v1_trig_m3": "vt_v1_m0.02_trigger"}
POOLS = {"select": ("select",), "dev3": ("dev3",), "final": ("final",), "ext": ("ext",),
         "unseen (dev3+final+ext)": ("dev3", "final", "ext"), "test3 (final+ext)": ("final", "ext")}


def load(tag: str, wins) -> tuple[pd.DataFrame, np.ndarray, pd.DataFrame]:
    parts, mk, ref = [], [], []
    for w in wins:
        a = pd.read_pickle(OUT / "sim" / f"agg-{tag}-{w}.pkl")
        f = pd.read_pickle(predict.OUT / f"agg-{TAGS[w]}.pkl")
        m = pd.read_csv(predict.OUT / f"markets-{TAGS[w]}.csv")["m"].to_numpy()
        check(start_of(m))
        parts += [a, f[f["arm"] == "micf"]]
        ref.append(f[f["arm"].isin(list(REPRO.values()))])
        mk.append(m)
    return pd.concat(parts, ignore_index=True), np.concatenate(mk), pd.concat(ref, ignore_index=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="recal")
    a = ap.parse_args()
    rows, txt = [], [f"# Recalibrated arms in the simulator ({a.tag})\n"]
    for pool, wins in POOLS.items():
        try:
            agg, mk, ref = load(a.tag, wins)
        except FileNotFoundError:
            continue
        t = table(agg, mk)
        days = len(mk) / 288
        t["mk10_day"] = [agg[(agg["arm"] == x) & (agg["L"] == L)]["mk10v"].sum() / days for x, L in zip(t["arm"], t["L"])]
        for _, r in t.iterrows():
            arm, L = r["arm"], r["L"]
            g = agg[(agg["arm"] == arm) & (agg["L"] == L)]
            out = {"pool": pool, "arm": arm, "L": L, "fills_day": r["fills_day"], "mk10_c": r["mk10_c"],
                   "mk10_day": r["mk10_day"]}
            if arm != "micf":
                p = paired(g, agg[(agg["arm"] == "micf") & (agg["L"] == L)], mk, col="mk10v")
                fz = "vt_v1_trig_m3" if arm.startswith("vt_v1_trig_") else "vt_v1_m3"
                q = paired(g, agg[(agg["arm"] == fz) & (agg["L"] == L)], mk, col="mk10v")
                out |= {"gain_micf": p["diff_day"], "gm_lo": p["lo"], "gm_hi": p["hi"],
                        "gain_frozen": q["diff_day"], "gf_lo": q["lo"], "gf_hi": q["hi"], "p_le0_frozen": q["p_le0"]}
            if arm in REPRO:
                out["repro_frozen_mk10_day"] = ref[(ref["arm"] == REPRO[arm]) & (ref["L"] == L)]["mk10v"].sum() / days
            rows.append(out)
        print(pool, flush=True)
    r = pd.DataFrame(rows)
    r.to_csv(OUT / f"sim_{a.tag}.csv", index=False)
    for pool in r["pool"].unique():
        txt.append(f"\n## {pool}\n")
        txt.append(md(r[r["pool"] == pool].drop(columns=["pool"]).sort_values(["L", "arm"]), 1))
    (OUT / f"sim_{a.tag}.md").write_text("\n".join(txt))


if __name__ == "__main__":
    main()
