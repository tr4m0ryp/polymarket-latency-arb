"""What the frozen value model (v3p, L = 0) reads: grouped permutation importance on run 2
select rows that pass its prefilter (drop in the top-2% realized 10 s value when a feature
group is shuffled), and how many of its firing rows had no leaders' trigger yet
(anticipation share).

    nice -n 10 python3 -m research.predict.model.importance"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .. import OUT
from ..report.md import md
from .data import load
from .learners import clean
from .stack import stacked
from .store import load_model
from .value_sweep import prefilter

GROUPS = {"perp microprice change": ("p_dmic",), "perp queue / imbalance": ("p_imb", "p_micoff", "p_lq"),
          "perp OFI (CKS)": ("p_ofi",), "perp depletion / time-to-depletion": ("p_dep", "p_ttd"),
          "perp intensities / last tick": ("p_up", "p_dn", "p_lam", "p_tsm", "p_lastdir", "p_dmid", "p_spr"),
          "spot book": ("s_",), "spot trades": ("st_",), "perp-spot basis": ("basis_dev", "mic_dev"),
          "Polymarket state": ("tok_mid", "seen", "half_spread", "pm_", "bk", "secs_left", "lzs", "sigma", "delta"),
          "fair value (pzm, gap)": ("fair_", "gap"), "delta-scaled Binance": ("_c",)}


def main() -> None:
    mdl = load_model("v3p_L0")
    st, _ = stacked(load("select", frac=0.25, seed=7))
    st = st[(st["bad0"] == 0) & prefilter(st)]
    vf = mdl["vf"]
    X = clean(st[vf].to_numpy())
    real = st["v10_0"].to_numpy(float)
    p = mdl["model"].predict(X)
    n = max(int(0.02 * len(p)), 50)
    base = 100 * np.nanmean(real[np.argsort(-p)[:n]])
    fire = p >= 0.02
    trig = (np.abs(st["p_dmic0.1"]) >= 0.002).to_numpy() & ((st["p_dmic0.1"] + st["s_dmic0.1"]) > 0).to_numpy()
    rows = [{"group": "(none shuffled)", "top2pct_c_sh": base, "drop_c": 0.0}]
    rng = np.random.default_rng(0)
    for g, pre in GROUPS.items():
        cols = [i for i, c in enumerate(vf) if (c.endswith(pre) if pre == ("_c",) else c.startswith(pre))]
        Xs = X.copy()
        perm = rng.permutation(len(X))
        Xs[:, cols] = X[perm][:, cols]
        ps = mdl["model"].predict(Xs)
        v = 100 * np.nanmean(real[np.argsort(-ps)[:n]])
        rows.append({"group": g, "n_cols": len(cols), "top2pct_c_sh": v, "drop_c": base - v})
    out = pd.DataFrame(rows)
    txt = md(out, 2) + (f"\nfiring rows (pred >= 2 c): {int(fire.sum())}; share with the leaders' trigger "
                        f"toward the side at decision: {trig[fire].mean():.3f}; realized 10 s value "
                        f"with trigger {100 * np.nanmean(real[fire & trig]):.2f} c/sh, without "
                        f"{100 * np.nanmean(real[fire & ~trig]):.2f} c/sh\n")
    (OUT / "importance.md").write_text(txt)
    print(txt)


if __name__ == "__main__":
    main()
