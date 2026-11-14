"""Anatomy of the two 5m leaders' taker buys: how many, how big, how many win, and which
conditions the losers share.

    python3 study/profit/anatomy.py

Reads data/cache/latency_profit/btc-up-or-down-5m.pkl (profit/extract.py). YES frame:
q > 0 bought Up, q < 0 bought Down; pnl = q * (R - pi) at resolution; mo2 = 2 s markout;
r3 = Binance log return over the 3 s before the fill's block. Net = pnl - full taker fee
(our 0% rebate tier). Writes data/out/latency/anatomy.md."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
WALLETS = {"0xc53375ff94e96100f2b30a4b5775db35218d69a9": "leader A (0xc533)",
           "0x3048d65321be3497164cdfc2996f94f98a2e7537": "leader B (0x3048)"}


def frame() -> pd.DataFrame:
    d = pd.read_pickle(ROOT / "data" / "cache" / "latency_profit" / "btc-up-or-down-5m.pkl")
    d = d[d["wallet"].isin(WALLETS) & (d["side"] == "BUY")].copy()
    d["d"] = np.sign(d["q"])
    d["net"] = d["pnl"] - d["fee"] * d["taker"]
    d["won"] = d["pnl"] > 0
    d["mo2_pos"] = d["mo2"] > 0
    d["move_bp"] = 1e4 * d["r3"] * d["d"]  # Binance 3 s move in the direction bought
    d["chase_c"] = 100 * (d["pi"] - d["pi_prev"]) * d["d"]  # book moved our way before the fill
    d = d.sort_values(["wallet", "condition_id", "ts"])
    prev = d.groupby(["wallet", "condition_id"])["d"].shift()
    d["flip"] = prev.notna() & (prev != d["d"])
    return d


def _tab(g: pd.DataFrame) -> dict:
    u = g["usd"].sum()
    return {"fills": len(g), "usd_share": u, "win_rate": g["won"].mean(),
            "markout_pos": g["mo2_pos"].mean(), "net_c_per_usd": 100 * g["net"].sum() / u,
            "markout_c_per_usd": 100 * g["mo2"].sum() / u}


def buckets(d: pd.DataFrame) -> dict[str, pd.DataFrame]:
    tk = d[d["taker"] == 1]
    cuts = {
        "Binance move in our direction, 3 s (bp)": pd.cut(tk["move_bp"], [-np.inf, -1, -0.2, 0.2, 1, 2, np.inf]),
        "token price paid": pd.cut(tk["price"], [0, 0.3, 0.5, 0.7, 0.9, 1.0]),
        "seconds to close": pd.cut(tk["secs_to_end"], [0, 60, 120, 180, 240, 400]),
        "book already moved our way before the fill (c)": pd.cut(tk["chase_c"], [-np.inf, -0.5, 0.5, 1.5, 3, np.inf]),
        "fill reverses the previous side": tk["flip"],
    }
    out = {}
    for name, key in cuts.items():
        rows = []
        for (w, b), g in tk.groupby([tk["wallet"].map(WALLETS), key], observed=True):
            r = {"wallet": w, "bucket": str(b), **_tab(g)}
            rows.append(r)
        t = pd.DataFrame(rows)
        t["usd_share"] = t["usd_share"] / t.groupby("wallet")["usd_share"].transform("sum")
        out[name] = t
    return out


def summary(d: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for w, g in d.groupby(d["wallet"].map(WALLETS)):
        tk = g[g["taker"] == 1]
        pm = g.groupby("condition_id")
        rows.append({"wallet": w, "markets": g["condition_id"].nunique(),
                     "buys_per_mkt_mean": pm.size().mean(), "buys_per_mkt_med": pm.size().median(),
                     "usd_per_mkt_med": pm["usd"].sum().median(),
                     "shares_mode": g["size"].round().mode().iloc[0],
                     "usd_per_fill_med": g["usd"].median(), "usd_per_fill_mean": g["usd"].mean(),
                     "taker_share": g["taker"].mean(), **{k: v for k, v in _tab(tk).items() if k != "usd_share"},
                     "mkts_net_pos": (tk.groupby("condition_id")["net"].sum() > 0).mean()})
    return pd.DataFrame(rows)


def _md(df: pd.DataFrame) -> str:
    cols = list(df.columns)
    lines = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for r in df.itertuples(index=False):
        lines.append("| " + " | ".join(f"{v:.3g}" if isinstance(v, float) else str(v) for v in r) + " |")
    return "\n".join(lines)


def main() -> None:
    d = frame()
    parts = ["# 5m leaders: trade anatomy (taker buys; net at our 0% tier)\n", _md(summary(d))]
    for name, t in buckets(d).items():
        parts += [f"\n## {name}\n", _md(t)]
    out = ROOT / "data" / "out" / "latency" / "anatomy.md"
    out.write_text("\n".join(parts) + "\n")
    print(out.read_text())


if __name__ == "__main__":
    main()
