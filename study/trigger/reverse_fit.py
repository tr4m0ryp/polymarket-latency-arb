"""Fit and report for reverse.py (kept separate to stay under ~200 lines)."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from reverse import FEATS, ROOT, WALLETS, build  # noqa: E402
from reverse import (DecisionTreeClassifier, HistGradientBoostingClassifier,  # noqa: E402
                     export_text, permutation_importance, roc_auc_score)


def split(g: pd.DataFrame):
    mk = np.sort(g["condition_id"].unique())
    test = set(mk[::4])  # every 4th market held out
    t = g["condition_id"].isin(test).to_numpy()
    return g[~t], g[t]


def fit(g: pd.DataFrame, target: str, rows) -> list[str]:
    d = g[rows].dropna(subset=["r1", "r3", "gap"])
    tr, te = split(d)
    y_tr, y_te = tr[target].to_numpy(), te[target].to_numpy()
    if target == "side":
        y_tr, y_te = (y_tr > 0).astype(int), (y_te > 0).astype(int)
    m = HistGradientBoostingClassifier(max_iter=300, learning_rate=0.05, max_leaf_nodes=31)
    m.fit(tr[FEATS], y_tr)
    p = m.predict_proba(te[FEATS])[:, 1]
    lines = [f"rows train {len(tr):,} test {len(te):,}; base rate {y_te.mean():.3f}",
             f"held-out AUC {roc_auc_score(y_te, p):.3f}, accuracy {((p > 0.5) == y_te).mean():.3f}"]
    sub = te.sample(min(len(te), 40000), random_state=0)
    ys = (sub[target] > 0).astype(int) if target == "side" else sub[target]
    imp = permutation_importance(m, sub[FEATS], ys, scoring="roc_auc", n_repeats=3, random_state=0)
    order = np.argsort(-imp.importances_mean)
    lines.append("importance (AUC drop): " + ", ".join(
        f"{FEATS[i]} {imp.importances_mean[i]:.3f}" for i in order[:8]))
    tree = DecisionTreeClassifier(max_depth=3, min_samples_leaf=500)
    tree.fit(tr[FEATS].fillna(-999), y_tr)
    lines += ["depth-3 tree (class 1 = " + ("Up" if target == "side" else "fires") + "):",
              "```", export_text(tree, feature_names=FEATS, decimals=2).rstrip(), "```"]
    return lines


def rules(g: pd.DataFrame) -> list[str]:
    f = g[g["fire"] == 1].dropna(subset=["r1", "r3", "gap"])
    up = f["side"] > 0
    out = ["single-rule side accuracy on fires (share where the rule picks the side bought):"]
    for name, s in [("sign r1", f["r1"]), ("sign r3", f["r3"]), ("sign r10", f["r10"]),
                    ("sign gap (fair - book)", f["gap"]), ("against position", -f["pos"]),
                    ("same as last side", f["last_side"]), ("better pair gain", f["pair_up"] - f["pair_dn"])]:
        ok = s != 0
        out.append(f"- {name}: {((s[ok] > 0) == up[ok]).mean():.3f} on {ok.mean():.0%} of fires")
    nm = f[f["r3"].abs() < 0.2]
    out.append(f"no-move fires (|r3| < 0.2 bp, {len(nm) / len(f):.0%}):")
    for name, s in [("sign gap", nm["gap"]), ("against position", -nm["pos"]),
                    ("same as last side", nm["last_side"]), ("better pair gain", nm["pair_up"] - nm["pair_dn"])]:
        ok = s != 0
        out.append(f"- {name}: {((s[ok] > 0) == (nm['side'][ok] > 0)).mean():.3f}")
    return out


def main() -> None:
    parts = ["# Reverse-engineered triggers, 5m leaders (taker buys, block-time resolution)\n"]
    for name in WALLETS:
        g = build(name)
        g.to_pickle(ROOT / "data" / "cache" / f"reverse_{name}.pkl")
        parts += [f"\n## Leader {name}\n", "### Does it fire this second?"]
        parts += fit(g, "fire", g["fire"].notna())
        parts += ["\n### Which side, given it fires?"]
        parts += fit(g, "side", g["fire"] == 1)
        parts += ["\n### Simple rules"] + rules(g)
        print("\n".join(parts[-40:]), flush=True)
    (ROOT / "data" / "out" / "latency" / "reverse.md").write_text("\n".join(parts) + "\n")


if __name__ == "__main__":
    main()
