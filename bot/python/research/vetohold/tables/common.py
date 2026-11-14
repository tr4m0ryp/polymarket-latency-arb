"""Shared loading and market-bootstrap statistics.

$/day = sum of 10 s markout PnL / (markets / 288). CIs resample markets (B = 2000); c/$ is
the ratio of resampled sums. `real` rows hold the mean over 16 hold draws per order, so
fills are expected shares and fill rate is the share of draws that filled at all."""
from __future__ import annotations

import numpy as np
import pandas as pd

from .. import DAY_MARKETS, OUT, SPLIT

B = 2000


def rows(name: str = "rows") -> pd.DataFrame:
    d = pd.read_pickle(OUT / f"{name}.pkl")
    d["test"] = d["t"] >= SPLIT
    return d


def paper_pnl(d: pd.DataFrame) -> pd.Series:
    """The paper bot's own logged 10 s markout PnL of each order (fee as logged)."""
    o = pd.read_pickle(OUT / "orders.pkl")[["arm", "slug", "t", "fee"]]
    x = d[["arm", "slug", "t", "paper_fill", "paper_cost", "paper_mk10", "won"]].merge(
        o, on=["arm", "slug", "t"], how="left")
    mk = pd.to_numeric(x["paper_mk10"], errors="coerce").fillna(x["won"])
    v = np.where(x["paper_fill"] > 0, x["paper_fill"] * mk - x["paper_cost"] - x["fee"].fillna(0), 0.0)
    return pd.Series(v, index=d.index)


def market_sums(d: pd.DataFrame, pnl: str, cost: str, mk: list[str]) -> tuple[np.ndarray, np.ndarray]:
    g = d.groupby("slug").agg(p=(pnl, "sum"), c=(cost, "sum")).reindex(mk).fillna(0)
    return g["p"].to_numpy(), g["c"].to_numpy()


def stats(d: pd.DataFrame, pnl: str, cost: str, mk: list[str], seed: int = 7) -> dict:
    p, c = market_sums(d, pnl, cost, mk)
    days = len(mk) / DAY_MARKETS
    idx = np.random.default_rng(seed).integers(0, len(mk), (B, len(mk)))
    bp, bc = p[idx].sum(1), c[idx].sum(1)
    with np.errstate(invalid="ignore", divide="ignore"):
        cpd = bp / bc * 100
    return {"c_per_$": p.sum() / c.sum() * 100 if c.sum() else np.nan,
            "c_lo": np.nanpercentile(cpd, 2.5), "c_hi": np.nanpercentile(cpd, 97.5),
            "usd_day": p.sum() / days, "d_lo": np.percentile(bp, 2.5) / days,
            "d_hi": np.percentile(bp, 97.5) / days}


def paired(a: pd.DataFrame, pa: str, b: pd.DataFrame, pb: str, mk: list[str], seed: int = 7) -> dict:
    """$/day of a minus b, paired by market."""
    x = a.groupby("slug")[pa].sum().reindex(mk).fillna(0).to_numpy()
    y = b.groupby("slug")[pb].sum().reindex(mk).fillna(0).to_numpy()
    days = len(mk) / DAY_MARKETS
    idx = np.random.default_rng(seed).integers(0, len(mk), (B, len(mk)))
    bs = (x - y)[idx].sum(1) / days
    return {"gain_day": (x - y).sum() / days, "g_lo": np.percentile(bs, 2.5), "g_hi": np.percentile(bs, 97.5)}


def fmt(x: float, nd: int = 1) -> str:
    return "n/a" if x != x else f"{x:+,.{nd}f}"


def ci(s: dict, k: str, lo: str, hi: str, nd: int = 1) -> str:
    return f"{fmt(s[k], nd)} [{fmt(s[lo], nd)}, {fmt(s[hi], nd)}]"
