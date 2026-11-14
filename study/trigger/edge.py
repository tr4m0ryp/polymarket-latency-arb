"""Edge per trade, and where the PnL comes from.

  bot_table     per wallet, live taker fills: size, price paid for the chosen
                side, spot-implied fair value of that side, model edge (fair -
                paid, cents/share), realized PnL per USD, 2 s / 10 s markouts,
                aligned spot state at the fill, Brier of fair vs the stale book
  decompose     per wallet, all fills: PnL split into the locked part of
                matched Up+Down pairs (pair * (1 - avg Up cost - avg Down
                cost)) and the residual directional exposure
  edge_by_move  all bots pooled: realized PnL/USD and markouts by the size of
                the aligned 3 s BTC move at the fill"""
from __future__ import annotations

import numpy as np
import pandas as pd

R3_BINS = [-1e9, -1, 0, 0.5, 1, 2, 4, 1e9]


def _w(v, u) -> float:
    return float((v * u).sum() / u.sum()) if u.sum() > 0 else np.nan


def bot_table(tk: pd.DataFrame, who: dict[str, pd.Series]) -> pd.DataFrame:
    rows = []
    for name, sel in who.items():
        x = tk[sel]
        u, s = x["usd"], np.sign(x["q"])
        up = x["q"] > 0
        R = x["R"]
        rows.append({
            "wallet": name, "fills": len(x), "usd": u.sum(), "med_fill_usd": u.median(),
            "buy_share": _w(x["side"].eq("BUY"), u),
            "paid": _w(np.where(up, x["pi"], 1 - x["pi"]), u),
            "fair_side": _w(np.where(up, x["fair"], 1 - x["fair"]), u),
            "edge_c": 100 * _w(x["edge"], u),
            "edge_pos_share": _w(x["edge"] > 0, u),
            "pnl_per_usd_c": 100 * x["pnl"].sum() / u.sum(),
            "mo2_per_usd_c": 100 * x["mo2"].sum() / u.sum(),
            "mo10_per_usd_c": 100 * x["mo10"].sum() / u.sum(),
            "r3_al_bp": _w(1e4 * s * x["r3"], u), "move_open_al_bp": _w(s * x["move_open_bp"], u),
            "move_open_al_usd": _w(s * x["move_open_usd"], u),
            "secs_left_med": x["secs_left"].median(),
            "brier_fair": _w((x["fair"] - R) ** 2, u), "brier_book": _w((x["book"] - R) ** 2, u),
        })
    return pd.DataFrame(rows)


def decompose(f: pd.DataFrame, mk: pd.DataFrame, wallets: list[str]) -> pd.DataFrame:
    rows = []
    for w in wallets:
        x = f[f["wallet"] == w]
        sg = np.where(x["side"] == "BUY", 1, -1)
        d = pd.DataFrame({"cid": x["condition_id"], "o": x["outcome_index"],
                          "sh": sg * x["size"], "cost": sg * x["size"] * x["price"]})
        p = d.pivot_table(index="cid", columns="o", values=["sh", "cost"], aggfunc="sum").fillna(0.0)
        up, dn = p[("sh", 0)], p[("sh", 1)]
        cu, cd = p[("cost", 0)], p[("cost", 1)]
        R = mk.loc[p.index, "R"]
        tot = up * R + dn * (1 - R) - cu - cd
        pair = np.minimum(up, dn).clip(lower=0)
        au = (cu / up.where(up > 0)).fillna(0)
        ad = (cd / dn.where(dn > 0)).fillna(0)
        lock = pair * (1 - au - ad)
        rows.append({"wallet": w, "markets": len(p), "pnl": tot.sum(), "locked_pairs": lock.sum(),
                     "residual_directional": tot.sum() - lock.sum(),
                     "pair_cost": float(((au + ad) * pair).sum() / pair.sum()) if pair.sum() else np.nan,
                     "paired_share": float(2 * pair.sum() / (up.abs().sum() + dn.abs().sum())),
                     "maker_usd_share": _w(x["taker"] == 0, x["size"] * x["price"]),
                     "win_rate_mkts": float((tot > 0).mean())})
    return pd.DataFrame(rows)


def edge_by_move(tk: pd.DataFrame) -> pd.DataFrame:
    x = tk.assign(r3_al=1e4 * np.sign(tk["q"]) * tk["r3"])
    x["bin"] = pd.cut(x["r3_al"], R3_BINS)
    g = x.groupby("bin", observed=True)
    out = g.agg(fills=("usd", "size"), usd=("usd", "sum"), pnl=("pnl", "sum"),
                mo2=("mo2", "sum"), mo10=("mo10", "sum"))
    for c in ("pnl", "mo2", "mo10"):
        out[f"{c}_per_usd_c"] = 100 * out[c] / out["usd"]
    out["usd_share"] = out["usd"] / out["usd"].sum()
    out["edge_c"] = g.apply(lambda d: 100 * _w(d["edge"], d["usd"]), include_groups=False)
    return out.drop(columns=["pnl", "mo2", "mo10"]).reset_index()
