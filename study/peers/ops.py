"""One operator behind several wallets: per-market position and PnL move together.

Bots reacting to one public BTC move tie in time by construction, so timing
alone cannot separate siblings from competitors. Wallets run by ONE
operator from one signal and one risk book also end each market with the
same net position and the same PnL sign and size. Over shared markets:
  q_corr    correlation of net outcome-0 shares per market
  pnl_corr  correlation of PnL per market
Independent latency bots in the same family sit near 0.0-0.3 on both."""
from __future__ import annotations

import numpy as np
import pandas as pd

from bursts import load_fills


def market_corr(slug: str, wallets: list[str], min_shared: int = 30) -> pd.DataFrame:
    f = load_fills(slug)
    f = f[f["wallet"].isin(wallets)]
    q = f.pivot_table(index="condition_id", columns="wallet", values="q", aggfunc="sum")
    p = f.pivot_table(index="condition_id", columns="wallet", values="pnl", aggfunc="sum")
    cols, rows = list(q.columns), []
    for i, a in enumerate(cols):
        for b in cols[i + 1:]:
            m = q[a].notna() & q[b].notna()
            n = int(m.sum())
            if n < min_shared:
                continue
            rows.append({"a": a, "b": b, "shared_mkts": n,
                         "q_corr": float(np.corrcoef(q.loc[m, a], q.loc[m, b])[0, 1]),
                         "pnl_corr": float(np.corrcoef(p.loc[m, a], p.loc[m, b])[0, 1]),
                         "series": slug})
    return pd.DataFrame(rows)


def groups(edges: pd.DataFrame) -> dict[str, str]:
    """Union-find over operator edges -> wallet: group id (smallest member)."""
    parent: dict[str, str] = {}

    def find(x: str) -> str:
        while parent.setdefault(x, x) != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for a, b in edges[["a", "b"]].itertuples(index=False):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[max(ra, rb)] = min(ra, rb)
    return {w: find(w) for w in parent}
