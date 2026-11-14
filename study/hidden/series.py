"""Step-function price series on one clock, built from the prep tables of an hour and the
hour before it (so 10 s lookbacks at the top of an hour work).

Clock: the venue clock. Binance trades and perp bookTicker carry venue stamps; spot bookTicker
does not, so its venue time is estimated as receipt minus the hour's median spot trade lag.
The Polymarket Up-book top uses its message stamp (ms; median receipt lag ~10 ms), else
receipt minus the median CLOB lag. All series return values at query times strictly before the query (state an actor at
that instant could have seen, ignoring its own latency)."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
PREP = ROOT / "data" / "cache" / "hidden" / "prep"


class Step:
    """Right-continuous step series; at(q) = last value with time < q."""

    def __init__(self, t: np.ndarray, v: np.ndarray) -> None:
        o = np.argsort(t, kind="stable")
        self.t, self.v = np.asarray(t, float)[o], np.asarray(v, float)[o]

    def at(self, q) -> np.ndarray:
        i = np.searchsorted(self.t, np.asarray(q, float), side="left") - 1
        return np.where(i >= 0, self.v[np.clip(i, 0, None)], np.nan)

    def last_time(self, q) -> np.ndarray:
        i = np.searchsorted(self.t, np.asarray(q, float), side="left") - 1
        return np.where(i >= 0, self.t[np.clip(i, 0, None)], np.nan)


def load(h: int) -> dict[str, pd.DataFrame]:
    out: dict[str, list] = {}
    for hh in (h - 1, h):
        p = PREP / f"{hh}.pkl"
        if not p.exists():
            continue
        for k, v in pd.read_pickle(p).items():
            if k != "levels" or hh == h:
                out.setdefault(k, []).append(v)
    return {k: pd.concat(v, ignore_index=True) for k, v in out.items()}


def build(d: dict[str, pd.DataFrame]) -> dict:
    s: dict = {}
    tr = d["spot_tr"]
    lag_spot = float(np.median(tr["t"] - tr["ts"]))
    s["lag_spot"] = lag_spot
    s["spot_tr"] = Step(tr["ts"].to_numpy(), tr["px"].to_numpy())
    bk = d["spot_bk"]
    s["spot_mid"] = Step(bk["t"].to_numpy() - lag_spot, ((bk["bid"] + bk["ask"]) / 2).to_numpy())
    smic = (bk["bid"] * bk["aq"] + bk["ask"] * bk["bq"]) / (bk["aq"] + bk["bq"])
    s["spot_micro"] = Step(bk["t"].to_numpy() - lag_spot, smic.to_numpy())
    sgn = np.where(tr["bm"].to_numpy() == 1, -1.0, 1.0)  # buyer is maker = taker sold
    s["spot_flow"] = Step(tr["ts"].to_numpy(), np.cumsum(sgn * tr["qty"].to_numpy()))
    if "perp_bk" in d and len(d["perp_bk"]):
        pb = d["perp_bk"]
        s["lag_perp"] = float(np.median(pb["t"] - pb["ts"]))
        s["perp_mid"] = Step(pb["ts"].to_numpy(), ((pb["bid"] + pb["ask"]) / 2).to_numpy())
        micro = (pb["bid"] * pb["aq"] + pb["ask"] * pb["bq"]) / (pb["aq"] + pb["bq"])
        s["perp_micro"] = Step(pb["ts"].to_numpy(), micro.to_numpy())
        s["perp_imb"] = Step(pb["ts"].to_numpy(), ((pb["bq"] - pb["aq"]) / (pb["bq"] + pb["aq"])).to_numpy())
    if "perp_tr" in d and len(d["perp_tr"]):
        pt = d["perp_tr"].sort_values("ts")
        sgn = pt["sgn"].to_numpy() if "sgn" in pt else np.where(pt["bm"].to_numpy() == 1, -1.0, 1.0)
        s["perp_flow"] = Step(pt["ts"].to_numpy(), np.cumsum(sgn * pt["qty"].to_numpy()))
    for v in ("coinbase", "okx", "bybit"):  # side-recorder hours only
        if f"{v}_bk" in d and len(d[f"{v}_bk"]):
            b = d[f"{v}_bk"]
            s[f"{v}_mid"] = Step(b["ts"].to_numpy(), ((b["bid"] + b["ask"]) / 2).to_numpy())
            s[f"{v}_micro"] = Step(b["ts"].to_numpy(),
                                   ((b["bid"] * b["aq"] + b["ask"] * b["bq"]) / (b["aq"] + b["bq"])).to_numpy())
        if f"{v}_tr" in d and len(d[f"{v}_tr"]):
            x = d[f"{v}_tr"].sort_values("ts")
            s[f"{v}_flow"] = Step(x["ts"].to_numpy(), np.cumsum((x["sgn"] * x["qty"]).to_numpy()))
    if "chain" in d and len(d["chain"]):
        c = d["chain"]
        s["chain"] = Step(c["obs"].to_numpy(), c["px"].to_numpy())
    pr = d["prints"]
    s["lag_clob"] = float(np.nanmedian(pr["t"] - pr["ts"]))
    return s


def book_tops(d: dict[str, pd.DataFrame], market: str, lag_clob: float) -> dict[str, Step]:
    """Up-book top for one market on the CLOB message stamp (receipt - lag if missing)."""
    tp = d["tops"]
    tp = tp[tp["market"] == market]
    t = np.where(np.isnan(tp["ts"]), tp["t"] - lag_clob, tp["ts"]).astype(float)
    return {"bb": Step(t, tp["bb"].to_numpy()), "ba": Step(t, tp["ba"].to_numpy()),
            "bbs": Step(t, tp["bbs"].to_numpy()), "bas": Step(t, tp["bas"].to_numpy())}
