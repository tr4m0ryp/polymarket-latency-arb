"""Tables of the probe: gain vs frozen by fill model, clean vs quirk rows, quirk-neutral C1."""
import numpy as np
import pandas as pd

from ...harness import windows as W
from .probe import OUT

ids = np.array(W.all_eval_ids())
days = len(ids) / 288
f = pd.read_pickle(OUT / "fills.pkl")
rng = np.random.default_rng(0)
B = rng.integers(0, len(ids), (2000, len(ids)))


def pm(arm, fm, mask=None):
    g = f[(f["arm"] == arm) & (f["fm"] == fm)]
    if mask is not None:
        g = g[g["quirk"] == mask]
    return g.groupby("m")["mk10v"].sum().reindex(ids, fill_value=0).to_numpy()


def gain(a, b, fm, mask=None):
    d = pm(a, fm, mask) - pm(b, fm, mask)
    bs = d[B].sum(1) / days
    return f"{d.sum()/days:+.0f} [{np.percentile(bs,2.5):+.0f}, {np.percentile(bs,97.5):+.0f}]"


for c, fr in (("ek_pred_2000", "vt_any"), ("vk_vstar_4000_d6", "veto")):
    for fm in ("base", "comp", "harsh"):
        print(c, fm, "all", gain(c, fr, fm), "| clean", gain(c, fr, fm, False), "| quirk", gain(c, fr, fm, True),
              "| quirk-neutral", gain(c + "_qn", fr, fm))
    g = f[(f["arm"] == c) & (f["fm"] == "base")]
    print("  quirk share of fills", round(g["quirk"].mean(), 3), "of mk10v", round(g.loc[g.quirk, "mk10v"].sum() / g["mk10v"].sum(), 3))
    for fm in ("base", "comp", "harsh"):
        g = f[(f["arm"] == c) & (f["fm"] == fm)]
        big = g["ordered"] > 60
        print("  ", fm, "fill frac big", round(g.loc[big, "shares"].sum() / g.loc[big, "ordered"].sum(), 3),
              "c/sh big", round(100 * g.loc[big, "mk10v"].sum() / g.loc[big, "shares"].sum(), 1),
              "c/sh <=60", round(100 * g.loc[~big, "mk10v"].sum() / max(g.loc[~big, "shares"].sum(), 1), 1))
