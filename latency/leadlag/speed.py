"""Does arriving faster pay more? Every Polymarket taker trade on the burst side within
[T0 - 0.5, T0 + 2] s of a Binance burst onset, bucketed by its delay on the venues' own clocks
(trade stamp minus Binance trade time). Edge per share = d * (fair - p_up) - taker fee at our 0%
tier, fair = Up-book mid 3 s after the trade. Also the fastest first reprices of the book.

    python3 latency/leadlag/speed.py [hour ...]     (default: every recorded hour)"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import book  # noqa: E402
import load  # noqa: E402
import spot  # noqa: E402

BINS = [-0.5, 0] + [round(0.01 * i, 2) for i in range(1, 16)] + [0.2, 0.3, 0.5, 1.0, 2.0]


def trades_after(m: dict, rows: pd.DataFrame, bursts: pd.DataFrame) -> pd.DataFrame:
    top, _ = book.replay(rows, m["up"], np.array([]))
    tk = rows[(rows["kind"] == 2) & ((rows["t"] - rows["ts"]) <= 0.1)]
    if not len(tk) or not len(top):
        return pd.DataFrame()
    up = (tk["asset"] == m["up"]).to_numpy()
    pu = np.where(up, tk["price"], 1 - tk["price"])
    dirn = np.where(up, 1, -1) * tk["side"].to_numpy()
    ts, t, sz = tk["ts"].to_numpy(), tk["t"].to_numpy(), tk["size"].to_numpy()
    bb, ba = book.top_at(top, t + 3.0)
    fair = (bb + ba) / 2
    out = []
    b = bursts[(bursts["T0"] > m["start"] + 5) & (bursts["T0"] < m["end"] - 30)
               & ((bursts["R0"] - bursts["T0"]) <= 0.3)]
    for e in b.itertuples():
        w = (ts >= e.T0 - 0.5) & (ts <= e.T0 + 2.0) & (dirn == e.d) & ~np.isnan(fair)
        paid = np.where(e.d > 0, pu[w], 1 - pu[w])
        edge = e.d * (fair[w] - pu[w]) - spot.fee(paid)
        out.append(pd.DataFrame({"delay": ts[w] - e.T0, "shares": sz[w], "usd": sz[w] * paid,
                                 "edge": sz[w] * edge, "move_bp": abs(e.move_bp), "fam": m["fam"]}))
    return pd.concat(out) if out else pd.DataFrame()


def _files(stream: str, hours) -> list:
    return [p for h in hours for p in load.LIVE.glob(f"*/{stream}-{h}.tsv.gz")]


def collect(hours: list[int]) -> pd.DataFrame:
    """Hour by hour (memory): markets starting in hour h use files h-1..h+1."""
    mk = load.markets()
    mk = mk.assign(hour=(mk["start"] // 3600).astype(int))
    res = []
    for h in hours:
        sub = mk[mk["hour"] == h]
        if not len(sub):
            continue
        near = [h - 1, h, h + 1]
        bn = pd.concat([load._binance(p) for p in _files("binance", near)])
        bursts = spot.bursts(spot.trades(bn), 1.0)
        for fam in ("5m", "15m"):
            parts = [load._clob(p) for p in _files(f"clob_{fam}", [h, h + 1])]
            if not parts:
                continue
            clob = pd.concat(parts).sort_values("t", kind="stable")
            for m in sub[sub["fam"] == fam].to_dict("records"):
                rows = clob[clob["market"] == m["condition_id"]]
                if len(rows) > 100:
                    res.append(trades_after(m, rows, bursts))
        print("hour", h, "done", flush=True)
    return pd.concat([r for r in res if len(r)])


def main(hours: list[int]) -> None:
    if not hours:
        hs = sorted({int(p.name.split("-")[-1].split(".")[0]) for p in load.LIVE.glob("*/clob_5m-*.tsv.gz")})
        hours = hs[:-1]  # skip the hour still being written
    df = collect(hours)
    out = load.ROOT / "data" / "out" / "live"
    df.to_csv(out / "speed_trades.csv.gz", index=False)
    df["bucket"] = pd.cut(df["delay"], BINS)
    tab = df.groupby(["fam", "bucket"], observed=True).agg(
        trades=("usd", "size"), usd=("usd", "sum"), edge=("edge", "sum"),
        win=("edge", lambda x: (x > 0).mean())).reset_index()
    tab["edge_c_per_usd"] = 100 * tab["edge"] / tab["usd"]
    print(tab.to_string(index=False))
    tab.to_csv(out / "speed.csv", index=False)


if __name__ == "__main__":
    main([int(h) for h in sys.argv[1:]])
