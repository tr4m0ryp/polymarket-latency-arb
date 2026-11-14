"""Exposure to rivals per arm and regime, and markout split by that exposure (base fills)."""
from __future__ import annotations

import numpy as np
import pandas as pd

from .boot import DAY, markets, per_market, ratio_ci
from ..data.prints import _leaders


def _leader_markets() -> set:
    return set(_leaders()["m"].unique())


def _c(g: pd.DataFrame) -> float:
    return 100 * g["base_mk10v"].sum() / max(g["base_cost"].sum(), 1e-9)


def exposure(o: pd.DataFrame, ids: dict, arms, L: int, groups=("quiet", "busy")) -> pd.DataFrame:
    rows = []
    for arm in arms:
        for gname in groups:
            mk = markets(ids, gname)
            a = o[(o["arm"] == arm) & (o["L"] == L) & o["m"].isin(mk) & ~o["skip"]]
            f = a[a["base_got"] > 0]
            if not len(f):
                continue
            fl = f[f["m"].isin(_leader_markets())]   # markets with the leaders' Data API fills
            lead = fl["hold_lead"].sum() / max(fl["hold_n"].sum(), 1) if len(fl) else np.nan
            rows.append({
                "arm": arm, "L": L, "regime": gname, "orders/day": len(a) / (len(mk) / DAY),
                "fill rate": len(f) / len(a), "shares/fill": f["base_got"].mean(),
                "rival in hold, our levels": (f["hold_n_lim"] > 0).mean(),
                "rival in hold, any level": (f["hold_n"] > 0).mean(),
                "rival in hold, unfilled": (a.loc[a["base_got"] <= 0, "hold_n"] > 0).mean(),
                "leader share of hold prints": lead,
                "rival <= 25 ms after": (f["aft25"] > 0).mean(),
                "our shares gone 50 ms later": f["van50"].sum() / f["base_got"].sum(),
                "... taken by a print": f["tr50"].sum() / f["base_got"].sum(),
                "our shares gone 100 ms later": f["van100"].sum() / f["base_got"].sum(),
                "depth kept through hold": np.median(np.minimum(f["dep_match"] / f["dep_dec"].clip(lower=1), 3)),
                "traded share of hold drop": f["hold_traded"].sum()
                / max((f["dep_dec"] - f["dep_match"]).clip(lower=0).sum(), 1e-9),
                "slip c": 100 * (f["base_cost"] / f["base_got"] - f["seen"]).mean(),
                "mk10 c/$": _c(f)})
    return pd.DataFrame(rows)


SPLITS = {
    "rival print in hold at our levels": lambda f: np.where(f["hold_n_lim"] > 0, "yes", "no"),
    "rival print in hold, any level": lambda f: np.where(f["hold_n"] > 0, "yes", "no"),
    "share of our fill a rival took <= 50 ms later": lambda f: pd.cut(
        f["tr50"] / f["base_got"], [-1, 0, 0.5, 2], labels=["0", "0-50%", ">50%"]).astype(str),
    "share of our fill gone <= 50 ms later": lambda f: pd.cut(
        f["van50"] / f["base_got"], [-1, 0, 0.5, 2], labels=["0", "0-50%", ">50%"]).astype(str),
    "same-side prints in last 1 s (decision time)": lambda f: pd.cut(
        f["pre1"], [-1, 0, 2, 1e9], labels=["0", "1-2", "3+"]).astype(str),
    "our-view depth at seen price (decision time)": lambda f: pd.cut(
        f["dep_seen_r"], [-1, 30, 120, 1e9], labels=["<30", "30-120", "120+"]).astype(str),
    "book messages in last 1 s (decision time)": lambda f: pd.cut(
        f["ev1"], [-1, 500, 1500, 1e9], labels=["<500", "500-1500", "1500+"]).astype(str),
    "fill fraction": lambda f: pd.cut(f["base_got"] / 60, [0, 0.5, 0.999, 2], labels=["<50%", "50-99%", "full"]).astype(str),
}


def by_split(o: pd.DataFrame, ids: dict, arm: str, L: int, groups=("quiet", "busy")) -> pd.DataFrame:
    rows = []
    for gname in groups:
        mk = markets(ids, gname)
        f = o[(o["arm"] == arm) & (o["L"] == L) & o["m"].isin(mk) & (o["base_got"] > 0)]
        days = len(mk) / DAY
        for name, fn in SPLITS.items():
            lab = fn(f)
            for v in sorted(set(lab)):
                g = f[lab == v]
                c = ratio_ci(per_market(g, "base_mk10v", mk), per_market(g, "base_cost", mk))
                rows.append({"arm": arm, "regime": gname, "split": name, "group": v, "fills": len(g),
                             "share": len(g) / len(f), "mk10 c/$": c[0], "lo": c[1], "hi": c[2],
                             "mk10 $/day": g["base_mk10v"].sum() / days})
    return pd.DataFrame(rows)


def bad_markets(o: pd.DataFrame, ids: dict, arm: str, L: int, group: str = "unseen", k: int = 5) -> pd.DataFrame:
    """Bottom-k markets by base 10 s markout vs the rest: exposure and fill-model sensitivity."""
    mk = markets(ids, group)
    al = o[(o["arm"] == arm) & (o["L"] == L) & o["m"].isin(mk)]
    a = al[al["base_got"] > 0]
    per = a.groupby("m")["base_mk10v"].sum().sort_values()
    rows = []
    for name, sel in (("bottom 5", per.index[:k]), ("top 5", per.index[-k:]),
                      ("rest", per.index[k:-k])):
        g, ga = a[a["m"].isin(sel)], al[al["m"].isin(sel)]
        rows.append({"arm": arm, "markets": name, "fills": len(g), "mk10 $": g["base_mk10v"].sum(),
                     "mk10 c/$": _c(g), "windows": ",".join(sorted(g["win"].unique())),
                     "rival in hold (our levels)": (g["hold_n_lim"] > 0).mean(),
                     "taken <= 50 ms later": g["tr50"].sum() / g["base_got"].sum(),
                     "pre1 mean": g["pre1"].mean(), "ev1 mean": g["ev1"].mean(),
                     "mk10 $ at e+25": ga["e+25_mk10v"].sum(), "mk10 $ comp": ga["comp_mk10v"].sum(),
                     "mk10 $ at e-25": ga["e-25_mk10v"].sum()})
    return pd.DataFrame(rows)
