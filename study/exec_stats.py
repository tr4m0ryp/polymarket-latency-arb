"""Execution-microstructure statistics for one wallet in one family.

Input is the wallet's slice of features.family_frame (YES frame + spot cols).
PnL split (exact, average-cost, per market, YES frame): with B YES-shares
bought at average pb and S sold at average ps (buying Down = selling YES at
1 - price), pnl = min(B,S)*(ps - pb) + held-net * (R - entry). The first term
is round-trip / arbitrage PnL (it includes Up+Down pairs bought under $1),
the second is what the open position earned at resolution."""
from __future__ import annotations

import numpy as np
import pandas as pd

T_BINS = [-np.inf, 0, 0.1, 0.25, 0.5, 0.75, 0.9, 1.0, np.inf]
T_LAB = ["pre", "0-.1", ".1-.25", ".25-.5", ".5-.75", ".75-.9", ".9-1", "post"]
P_BINS = [0, 0.1, 0.3, 0.5, 0.7, 0.9, 1.01]
P_LAB = ["<.1", ".1-.3", ".3-.5", ".5-.7", ".7-.9", ">.9"]
GAP = 5  # s of silence that separates two bursts inside one market


def _q(a, p):
    return float(np.nanpercentile(a, p)) if len(a) else np.nan


def market_split(x: pd.DataFrame) -> pd.DataFrame:
    """Per market: round-trip vs hold PnL, exposure, Up/Down buy costs."""
    q, pi = x["q"].to_numpy(), x["pi"].to_numpy()
    x = x.assign(qb=np.clip(q, 0, None), qs=np.clip(-q, 0, None),
                 cb=np.clip(q, 0, None) * pi, cs=np.clip(-q, 0, None) * pi,
                 bu=((x["side"] == "BUY") & (x["outcome_index"] == 0)) * x["size"],
                 bd=((x["side"] == "BUY") & (x["outcome_index"] == 1)) * x["size"],
                 cu=((x["side"] == "BUY") & (x["outcome_index"] == 0)) * x["usd"],
                 cd=((x["side"] == "BUY") & (x["outcome_index"] == 1)) * x["usd"],
                 sell=(x["side"] == "SELL") * x["usd"])
    m = x.groupby("condition_id").agg(
        B=("qb", "sum"), S=("qs", "sum"), CB=("cb", "sum"), CS=("cs", "sum"), R=("R", "first"),
        pnl=("pnl", "sum"), usd=("usd", "sum"), sell=("sell", "sum"), n=("q", "size"),
        bu=("bu", "sum"), bd=("bd", "sum"), cu=("cu", "sum"), cd=("cd", "sum"),
        t0=("ts", "min"), t1=("ts", "max"))
    pb = m["CB"] / m["B"].where(m["B"] > 0)
    ps = m["CS"] / m["S"].where(m["S"] > 0)
    mt = np.minimum(m["B"], m["S"])
    m["rt_pnl"] = (mt * (ps - pb)).fillna(0.0)
    m["hold_pnl"] = m["pnl"] - m["rt_pnl"]
    m["net"] = m["B"] - m["S"]
    m["exposure"] = m["net"].abs() / (m["B"] + m["S"]).clip(lower=1e-9)
    m["two_buy"] = (m["bu"] > 0) & (m["bd"] > 0)
    m["pair_cost"] = (m["cu"] / m["bu"].where(m["bu"] > 0)) + (m["cd"] / m["bd"].where(m["bd"] > 0))
    return m


def bursts(x: pd.DataFrame) -> pd.DataFrame:
    """Per market: bursts (fills split by > GAP s silence) and side flips."""
    rows = []
    for _, g in x.groupby("condition_id", sort=False):
        ts = g["ts"].to_numpy()
        d = np.sign(g.groupby("tx", sort=False)["q"].sum().to_numpy())
        rows.append((1 + int((np.diff(ts) > GAP).sum()), int((np.diff(d[d != 0]) != 0).sum()),
                     len(d), ts[-1] - ts[0]))
    return pd.DataFrame(rows, columns=["bursts", "flips", "n_tx", "span"])


def wallet_exec(x: pd.DataFrame) -> dict:
    usd = x["usd"].sum()
    tk = x[x["taker"] == 1]
    tx = x.groupby("tx").agg(usd=("usd", "sum"), n=("q", "size"), ts=("ts", "first"),
                             edge=("fair", "first"), pi=("pi", "mean"), q=("q", "sum"),
                             r3=("r3", "first"), taker=("taker", "max"))
    ttx = tx[tx["taker"] == 1]
    m = market_split(x)
    b = bursts(x)
    sz = x["size"].round(0)
    out = {
        "n_markets": len(m), "n_fills": len(x), "usd": usd, "pnl": x["pnl"].sum(),
        "fills_per_mkt_med": float(m["n"].median()), "tx_per_mkt_med": float(b["n_tx"].median()),
        "fills_per_tx": len(x) / max(len(tx), 1),
        "fill_usd_p10": _q(x["usd"], 10), "fill_usd_p50": _q(x["usd"], 50), "fill_usd_p90": _q(x["usd"], 90),
        "tx_usd_p50": _q(tx["usd"], 50), "tx_usd_p90": _q(tx["usd"], 90),
        "tx_usd_cv": float(tx["usd"].std() / tx["usd"].mean()) if len(tx) > 1 else np.nan,
        "mode_size": float(sz.mode().iloc[0]) if len(sz) else np.nan,
        "mode_size_share": float((sz == sz.mode().iloc[0]).mean()) if len(sz) else np.nan,
        "mkt_usd_p50": float(m["usd"].median()),
        "taker_usd_share": tk["usd"].sum() / usd if usd else np.nan,
        "sell_usd_share": float(m["sell"].sum() / usd) if usd else np.nan,
        "two_buy_share": float(m["two_buy"].mean()),
        "pair_cost_med": float(m.loc[m["two_buy"], "pair_cost"].median()),
        "pair_lt1_share": float((m.loc[m["two_buy"], "pair_cost"] < 1).mean()) if m["two_buy"].any() else np.nan,
        "exposure_med": float(m["exposure"].median()),
        "flat_share": float((m["exposure"] < 0.05).mean()),
        "rt_pnl": float(m["rt_pnl"].sum()), "hold_pnl": float(m["hold_pnl"].sum()),
        "win_mkts": float((m["pnl"] > 0).mean()),
        "bursts_med": float(b["bursts"].median()), "flips_med": float(b["flips"].median()),
        "span_med_s": float(b["span"].median()),
        "secs_to_end_p10": _q(x["secs_to_end"], 10), "secs_to_end_p50": _q(x["secs_to_end"], 50),
        "secs_to_end_p90": _q(x["secs_to_end"], 90),
        "first_t_rel_med": float(((m["t0"] - x.groupby("condition_id")["start_ts"].first())
                                  / (x.groupby("condition_id")["end_ts"].first()
                                     - x.groupby("condition_id")["start_ts"].first())).median()),
    }
    tb = pd.cut(x["t_rel"], T_BINS, labels=T_LAB, right=False)
    out.update({f"t_{k}": v for k, v in (x.groupby(tb, observed=False)["usd"].sum() / usd).items()})
    buys = x[x["side"] == "BUY"]
    pb = pd.cut(buys["price"], P_BINS, labels=P_LAB, right=False)
    out.update({f"p_{k}": v for k, v in
                (buys.groupby(pb, observed=False)["usd"].sum() / max(buys["usd"].sum(), 1e-9)).items()})
    out["pnl_taker"] = float(tk["pnl"].sum())
    out["pnl_maker"] = float(x.loc[x["taker"] == 0, "pnl"].sum())
    out["mo2_taker"] = float(tk["mo2"].sum() / max(tk["usd"].sum(), 1e-9))
    e = np.sign(tk["q"]) * (tk["fair"] - tk["pi"])
    tu = max(tk["usd"].sum(), 1e-9)
    out["edge_pos_share"] = float(tk.loc[e > 0, "usd"].sum() / tu)
    out["edge_med_c"] = float(np.median(e) * 100) if len(tk) else np.nan
    out["moved3_share"] = float(tk.loc[tk["r3"].abs() >= 5e-5, "usd"].sum() / tu)
    out["last60_share"] = float(x.loc[x["secs_to_end"] <= 60, "usd"].sum() / usd)
    out["secs_to_end_p1"] = _q(x["secs_to_end"], 1)
    vc = x["size"].round(2).value_counts(normalize=True).head(3)
    out["top_sizes"] = ";".join(f"{k:g}:{v:.2f}" for k, v in vc.items())
    held = m[m["net"].abs() > 1e-6]
    hit = np.sign(held["net"]) == np.where(held["R"] == 1, 1, -1)
    out["net_hit_usd"] = float((held["net"].abs() * hit).sum() / held["net"].abs().sum()) if len(held) else np.nan
    out["net_hit_mkts"] = float(hit.mean()) if len(held) else np.nan
    out["buy_price_med"] = _q(np.repeat(buys["price"].to_numpy(), 1), 50)
    # size vs edge: does the bot scale its taker order with spot-model edge or move size?
    if len(ttx) > 30:
        e = (np.sign(ttx["q"]) * (ttx["edge"] - ttx["pi"])).rank()
        out["size_vs_edge_rho"] = float(ttx["usd"].rank().corr(e))
        out["size_vs_move_rho"] = float(ttx["usd"].rank().corr(ttx["r3"].abs().rank()))
    hr = pd.to_datetime(x["ts"], unit="s", utc=True).dt.hour
    h = x.groupby(hr)["usd"].sum() / usd
    out["hours_active"] = int((h > 0.01).sum())
    out["top3_hours_share"] = float(h.nlargest(3).sum())
    out["peak_hours_utc"] = ",".join(str(i) for i in h.nlargest(3).index)
    gaps = np.diff(np.sort(m["t0"].to_numpy()))
    out["mkt_gap_med_s"] = float(np.median(gaps)) if len(gaps) else np.nan
    return out
