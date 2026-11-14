"""Which side do the 5m leaders buy? Held-out (by time) side models on ms-attributed fills,
by feature group, on all fills and on the no-move fills (|spot 3 s move| < 0.2 bp at ms
resolution) that the forensic study could not explain.

    python3 study/hidden/side.py

Features are rebuilt in the Up frame (feature * d), label = bought Up. Train on the first 2/3
of the hours with perp data, test on the last 1/3. Also single-rule accuracy (sign of one
feature, on fills where it is non-zero) with its coverage. 'rule' = sign of perp + spot microprice
change in the trigger window, else the last own side if the previous fill was < 0.6 s ago. Writes data/out/hidden/side.md."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from attrib import A, CACHE, ROOT  # noqa: E402

W = ("0.05", "0.1", "0.25", "0.5", "1.0", "2.0", "3.0", "5.0", "10.0")
GROUPS = {
    "forensic (block time, 1 s closes)": ["blk_r3"],
    "spot trades, ms-aligned": [f"spot_r{w}" for w in W],
    "+ spot book and taker flow": ["spot_micro_trig", "spot_mid_trig", "spot_flow_trig", "spot_micro_pre",
                                   "spot_flow_pre", "spot_micro_wide"],
    "perp book only": ["perp_micro_trig", "perp_mid_trig", "perp_imb_trig", "perp_imb_chg",
                       "perp_micro_pre", "perp_micro_post", "perp_micro_wide"] + [f"perp_r{w}" for w in W],
    "Polymarket only (book, flow, state)": [f"book_r{w}" for w in W] + [
        f"flow{w}_other" for w in ("0.1", "0.25", "0.5", "1.0", "3.0")] + ["mid", "spread", "secs_left"],
    "own burst state (gap, last side)": ["gap", "prev_side"],
    "peers (other leader's fills)": ["flow0_A", "flow0_B"] + [f"flow{w}_{p}" for w in ("0.25", "1.0", "3.0")
                                                            for p in "AB"],
}
SINGLE = ["rule", "blk_r3", "spot_r3.0", "spot_r0.5", "perp_mid_trig", "perp_micro_trig", "perp_micro_wide",
          "perp_micro_pre", "perp_micro_post", "spot_micro_post",
          "perp_imb_chg", "spot_micro_trig", "spot_flow_trig", "book_r0.5", "flow0.5_other", "flow0_B"]


def up_frame(f: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    keep = [c for c in cols if c in f]
    unsigned = {"mid", "spread", "secs_left", "gap", "prev_side"}
    return pd.DataFrame({c: f[c] if c in unsigned else f[c] * f["d"] for c in keep}, index=f.index)


def fit_eval(tr: pd.DataFrame, te: pd.DataFrame, cols: list[str]) -> tuple[float, float]:
    clf = HistGradientBoostingClassifier(max_iter=300, learning_rate=0.05, max_leaf_nodes=15,
                                         l2_regularization=1.0, random_state=0)
    clf.fit(up_frame(tr, cols), (tr["d"] > 0).astype(int))
    p = clf.predict_proba(up_frame(te, cols))[:, 1]
    y = (te["d"] > 0).astype(int)
    return roc_auc_score(y, p), float(((p > 0.5) == y).mean())


def main() -> None:
    f = pd.read_pickle(CACHE / "feat.pkl")
    f = f[f["perp_micro_trig"].notna()].copy()
    f["who"] = np.where(f["wallet"] == A, "A", "B")
    f["nomove"] = f["spot_r3.0"].abs() < 0.2
    f = f.sort_values("ts")
    grp = f.groupby(["who", "market"])
    f["gap"] = (f["ts"] - grp["ts"].shift()).fillna(999.0)
    f["prev_side"] = grp["d"].shift().fillna(0.0)
    comb = np.sign(f["perp_micro_trig"]) + np.sign(f["spot_micro_trig"].fillna(0))
    burst = np.where(f["gap"] < 0.6, f["prev_side"] * f["d"], 0)  # repeat the last side inside a burst
    f["rule"] = np.where(comb != 0, np.sign(comb), burst)  # features are already signed by d
    hours = sorted(f["hour"].unique())
    cut = hours[int(len(hours) * 2 / 3)]
    lines = [f"# Side models, ms-attributed fills (hours with perp data: {len(hours)}; test = last "
             f"{len(hours) - hours.index(cut)} h)\n"]
    for who, g in f.groupby("who"):
        tr, te = g[g["hour"] < cut], g[g["hour"] >= cut]
        lines.append(f"\n## Leader {who}: {len(g)} fills, no-move share {g['nomove'].mean():.3f}\n")
        lines.append("| features | AUC all | acc all | AUC no-move | acc no-move |\n|---|---|---|---|---|")
        groups = dict(GROUPS)
        groups["perp + spot + Polymarket"] = (GROUPS["perp book only"] + GROUPS["spot trades, ms-aligned"]
                                              + GROUPS["+ spot book and taker flow"]
                                              + GROUPS["Polymarket only (book, flow, state)"])
        groups["perp + spot + own burst state"] = (GROUPS["perp book only"] + GROUPS["+ spot book and taker flow"]
                                                   + GROUPS["own burst state (gap, last side)"])
        groups["all but peers"] = groups["perp + spot + Polymarket"] + GROUPS["own burst state (gap, last side)"]
        groups["everything"] = sum(GROUPS.values(), [])
        for name, cols in groups.items():
            a_all = fit_eval(tr, te, cols)
            a_nm = fit_eval(tr[tr["nomove"]], te[te["nomove"]], cols)
            lines.append(f"| {name} | {a_all[0]:.3f} | {a_all[1]:.3f} | {a_nm[0]:.3f} | {a_nm[1]:.3f} |")
        lines.append("\nsingle rules (sign of feature = side), test hours, accuracy / coverage:\n")
        lines.append("| feature | all | no-move |\n|---|---|---|")
        for c in SINGLE:
            cells = []
            for sub in (te, te[te["nomove"]]):
                v = sub[c].dropna()
                nz = v[v != 0]
                cells.append(f"{(nz > 0).mean():.3f} / {len(nz) / max(len(v), 1):.2f}")
            lines.append(f"| {c} | {cells[0]} | {cells[1]} |")
    lines.append("\n## Side accuracy by |perp microprice change| in the trigger window, no-move fills, all hours\n")
    lines += ["| change (bp) | A | B |", "|---|---|---|"]
    nm = f[f["nomove"]]
    b = pd.cut(nm["perp_micro_trig"].abs(), [-1, 1e-6, 1e-4, 5e-4, 2e-3, 1e-2, 100])
    t = nm.groupby([b, "who"], observed=True)["perp_micro_trig"].agg(lambda v: f"{(v > 0).mean():.3f} (n {len(v)})")
    for k in t.index.get_level_values(0).unique():
        lines.append(f"| {k} | {t.get((k, 'A'), '')} | {t.get((k, 'B'), '')} |")
    out = ROOT / "data" / "out" / "hidden" / "side.md"
    out.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
